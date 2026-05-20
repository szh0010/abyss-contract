"""
Coze v3 客户端（国内版 https://api.coze.cn）

为什么自己撸：
  Coze 的会话流程与 OpenAI 完全不同——
    1. POST /v3/chat   发起会话，返回 { data: { id, conversation_id, status: "in_progress" } }
    2. GET  /v3/chat/retrieve  轮询直到 status == "completed"（或 failed/canceled）
    3. GET  /v3/chat/message/list  拉取该次回合产生的所有消息，type == "answer" 是助手主回复
  我们把这三步封装成 `CozeClient.chat()`，对调用方暴露为 `await client.chat(message)` 一行调用。

依赖：
  - httpx >= 0.25     # async HTTP
  - Python >= 3.10    # asyncio.timeout

环境变量（参见 app.config.Settings）：
  - COZE_API_TOKEN              ：必填，PAT 或 OAuth Token
  - COZE_BOT_ID                 ：默认 7641078571066687542
  - COZE_BASE_URL               ：默认 https://api.coze.cn
  - COZE_USER_ID                ：会话归集用，可任意稳定字符串
  - COZE_TIMEOUT_SECONDS        ：单次回合总超时（默认 45 秒）
  - COZE_POLL_INTERVAL_SECONDS  ：轮询间隔（默认 1 秒）
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Iterable, Optional

import httpx

from app.config import settings


class CozeError(RuntimeError):
    """Coze API 调用失败的统一异常类型。调用方可据此回退到本地兜底文案。"""


@dataclass(frozen=True)
class CozeMessage:
    """Coze 输入消息（仅暴露最常用的子集）。"""
    role: str             # "user" | "assistant"
    content: str
    content_type: str = "text"


def _auth_headers() -> dict[str, str]:
    token = settings.COZE_API_TOKEN
    if not token:
        raise CozeError("COZE_API_TOKEN 未配置。请在 backend/.env 写入 COZE_API_TOKEN=...")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _check_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Coze 顶层错误用 { code, msg, data } 表达；非 0 即业务错误。"""
    code = payload.get("code")
    if code not in (0, None):  # 0 = 成功；某些端点不返回 code
        raise CozeError(f"Coze API 错误 code={code} msg={payload.get('msg')!r}")
    return payload


class CozeClient:
    """异步 Coze 客户端。线程安全，单实例可在整个 FastAPI 进程复用。"""

    def __init__(
        self,
        bot_id: Optional[str] = None,
        user_id: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        poll_interval: Optional[float] = None,
    ) -> None:
        self.bot_id = bot_id or settings.COZE_BOT_ID
        self.user_id = user_id or settings.COZE_USER_ID
        self.base_url = (base_url or settings.COZE_BASE_URL).rstrip("/")
        self.timeout = timeout if timeout is not None else settings.COZE_TIMEOUT_SECONDS
        
        # 💡 [修复点] 就是这里！加上这一行就彻底通了！
        self.poll_interval = poll_interval if poll_interval is not None else settings.COZE_POLL_INTERVAL_SECONDS

    async def chat(
        self,
        user_message: str,
        *,
        system_prompt: Optional[str] = None,
        history: Optional[Iterable[CozeMessage]] = None,
        custom_variables: Optional[dict[str, str]] = None,
        conversation_id: Optional[str] = None,
    ) -> str:
        """
        发起一次完整的"非流式"对话回合并返回纯文本回复。

        实现要点：
        - `auto_save_history=True` 让 Coze 自动管理历史；调用方仍可显式塞 history
        - `stream=False` 走「create → retrieve poll → message list」三步式
        - 单次总耗时受 self.timeout 上限；超时即 raise CozeError，由 chat_service 兜底
        """
        payload: dict[str, Any] = {
            "bot_id": self.bot_id,
            "user_id": self.user_id,
            "stream": False,
            "auto_save_history": True,
            "additional_messages": _build_messages(
                system_prompt=system_prompt,
                history=history,
                user_message=user_message,
            ),
        }
        if custom_variables:
            payload["custom_variables"] = custom_variables
        if conversation_id:
            payload["conversation_id"] = conversation_id

        deadline = time.monotonic() + self.timeout

        async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as http:
            # ── 1. 发起会话 ──
            create = await http.post(
                f"{self.base_url}/v3/chat",
                headers=_auth_headers(),
                json=payload,
            )
            create.raise_for_status()
            data = _check_payload(create.json()).get("data") or {}
            chat_id = data.get("id")
            conv_id = data.get("conversation_id")
            if not chat_id or not conv_id:
                raise CozeError(f"Coze 未返回有效会话 ID：{data!r}")

            status = data.get("status") or "in_progress"

            # ── 2. 轮询直到完成 ──
            while status in ("in_progress", "created"):
                if time.monotonic() >= deadline:
                    raise CozeError("Coze 响应超时")
                await asyncio.sleep(self.poll_interval)

                resp = await http.get(
                    f"{self.base_url}/v3/chat/retrieve",
                    headers=_auth_headers(),
                    params={"chat_id": chat_id, "conversation_id": conv_id},
                )
                resp.raise_for_status()
                d = _check_payload(resp.json()).get("data") or {}
                status = d.get("status") or "in_progress"

            if status != "completed":
                # failed / canceled / requires_action 都视为失败
                raise CozeError(f"Coze 会话状态={status}（未完成）")

            # ── 3. 拉取消息列表，提取助手 answer ──
            msgs = await http.get(
                f"{self.base_url}/v3/chat/message/list",
                headers=_auth_headers(),
                params={"chat_id": chat_id, "conversation_id": conv_id},
            )
            msgs.raise_for_status()
            items = _check_payload(msgs.json()).get("data") or []
            return _extract_answer_text(items)


def _build_messages(
    *,
    system_prompt: Optional[str],
    history: Optional[Iterable[CozeMessage]],
    user_message: str,
) -> list[dict[str, str]]:
    """组装 additional_messages：system → 历史 → 当前提问。"""
    out: list[dict[str, str]] = []
    if system_prompt:
        # Coze 不支持 role=system，统一作为 user 前置说明，并打 meta_data 标记便于后续追溯
        out.append({
            "role": "user",
            "content": system_prompt,
            "content_type": "text",
        })
    if history:
        for h in history:
            out.append({
                "role": h.role,
                "content": h.content,
                "content_type": h.content_type,
            })
    out.append({
        "role": "user",
        "content": user_message,
        "content_type": "text",
    })
    return out


def _extract_answer_text(items: list[dict[str, Any]]) -> str:
    """
    从 message list 里挑出助手的最终 answer 文本。
    - 优先 type == 'answer' 且 role == 'assistant' 且 content_type == 'text'
    - 多条 answer 用换行拼接（极少数场景模型会拆段）
    """
    answers = [
        (m.get("content") or "").strip()
        for m in items
        if m.get("type") == "answer"
        and m.get("role") == "assistant"
        and m.get("content_type") in (None, "text")
        and m.get("content")
    ]
    if answers:
        return "\n".join(answers).strip()
    raise CozeError("Coze 未返回任何 answer 文本")


# 进程级单例：FastAPI 多个请求共用同一个 client（无状态）
_default_client: Optional[CozeClient] = None


def get_coze_client() -> CozeClient:
    global _default_client
    if _default_client is None:
        _default_client = CozeClient()
    return _default_client