"""反诈智能客服 API 路由"""
import json
import re
from typing import Annotated, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.config import settings
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.chat_service import process_chat_message
from app.services.ai_decision import client as deepseek_client

router = APIRouter(
    prefix="/api/chat",
    tags=["反诈客服"],
    dependencies=[Depends(get_current_user)],
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="用户提问")


class ChatResponse(BaseModel):
    answer: str = Field(description="回复内容")
    intent: str = Field(default="NORMAL_CHAT", description="意图分类")
    risk_level: str = Field(default="normal", description="风险等级")
    source: str = Field(default="rag_llm", description="响应来源")
    is_alert: bool = Field(default=False, description="是否为紧急警报")
    knowledge_used: list[str] = Field(default=[], description="使用的知识库条目")


@router.post("/ask", response_model=ChatResponse, summary="智能客服对话")
async def ask_question(
    req: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    反诈智能客服主接口（需登录）。
    四层流水线：安全过滤 → 规则引擎 → 知识检索 → LLM 生成。
    """
    result = await process_chat_message(req.question, user=current_user)

    return ChatResponse(
        answer=result.get("answer", ""),
        intent=result.get("intent", "NORMAL_CHAT"),
        risk_level=result.get("risk_level", "normal"),
        source=result.get("source", "rag_llm"),
        is_alert=result.get("is_alert", False),
        knowledge_used=result.get("knowledge_used", []),
    )


# ============================================================
# 一键研判 · DeepSeek 严格模式
# - 系统提示禁止 Markdown / HTML / 代码围栏
# - 强制 JSON: {risk_level, core_risk, analysis}
# ============================================================
SPOTLIGHT_SYSTEM_PROMPT = """你是一名国家级网络安全反诈专家。请对用户提交的话术或链接进行分析。注意:你不需要访问链接,只需根据 URL 特征和文本上下文判断。

请严格遵循以下规则:
1. 绝对不要使用 <b>、* 或任何 HTML/Markdown 标记,只输出纯文本。
2. 分析内容必须结合用户输入的上下文(不要生搬硬套网恋等无关场景)。
3. 必须且只能输出合法的 JSON 格式,不要包含任何 ```json 的代码块符号!

返回格式必须严格如下:
{
  "risk_level": "high" 或 "low",
  "core_risk": "一句话指出核心破绽(如:仿冒官方域名、制造恐慌心理)",
  "analysis": "50字以内的深度剖析"
}"""


_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE | re.MULTILINE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MARKDOWN_BOLD_RE = re.compile(r"\*+")


def _strip_fences(text: str) -> str:
    if not text:
        return ""
    cleaned = _FENCE_RE.sub("", text.strip()).strip()
    first, last = cleaned.find("{"), cleaned.rfind("}")
    if first != -1 and last != -1 and last > first:
        cleaned = cleaned[first : last + 1]
    return cleaned


def _strip_format(text: str) -> str:
    """二次防御:即便 AI 偷偷塞了 <b>/* 标记,这里再剥一遍。"""
    if not text:
        return ""
    text = _HTML_TAG_RE.sub("", text)
    text = _MARKDOWN_BOLD_RE.sub("", text)
    return text.strip()


class SpotlightRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=600, description="可疑话术或链接")


class SpotlightResponse(BaseModel):
    risk_level: str = Field(default="low", description="high | low")
    core_risk: str = Field(default="", description="核心破绽")
    analysis: str = Field(default="", description="深度剖析(<=50字)")


_SPOTLIGHT_FALLBACK = SpotlightResponse(
    risk_level="low",
    core_risk="AI 链路异常,无法完成研判",
    analysis="请稍后重试,或拨打 96110 反诈专线人工核实。",
)


@router.post("/spotlight", response_model=SpotlightResponse, summary="一键研判 · 严格 JSON")
async def spotlight_judge(
    req: SpotlightRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """对可疑链接 / 话术做严格研判。

    - DeepSeek 系统提示禁止 Markdown/HTML/围栏
    - 后端再做一次 strip_fences + strip_format 双防御
    - JSON 解析失败 → 兜底 + low 风险,前端依然能渲染
    """
    if not settings.DEEPSEEK_API_KEY:
        return _SPOTLIGHT_FALLBACK

    try:
        resp = await deepseek_client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": SPOTLIGHT_SYSTEM_PROMPT},
                {"role": "user", "content": req.text.strip()},
            ],
            temperature=0.2,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or ""
    except Exception as e:  # noqa: BLE001
        print(f"[spotlight] DeepSeek 调用失败: {type(e).__name__}: {e}")
        return _SPOTLIGHT_FALLBACK

    cleaned = _strip_fences(raw)
    try:
        data = json.loads(cleaned) if cleaned else {}
    except json.JSONDecodeError:
        print(f"[spotlight] JSON 解析失败 raw={raw[:200]!r}")
        return _SPOTLIGHT_FALLBACK

    risk = str(data.get("risk_level") or "").strip().lower()
    if risk not in ("high", "low"):
        risk = "low"

    return SpotlightResponse(
        risk_level=risk,
        core_risk=_strip_format(str(data.get("core_risk") or "")),
        analysis=_strip_format(str(data.get("analysis") or "")),
    )
