import json
import re
import traceback
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.player import PlayerSession
from app.models.user import User
from app.models.game_state import GameState
from app.models.user_medal import UserMedal
from app.schemas.player import PlayerCreate, PlayerStatus
from app.schemas.game import GameStageResponse, PlayerChoice, ChoiceResult
from app.services.auth_service import get_current_user
from app.services.game_engine import GameEngine
from app.services.llm_service import classify_intent, generate_k_dialogue
from app.services.coze_client import CozeClient, CozeError
from app.config import settings

router = APIRouter(prefix="/api/game", tags=["游戏核心"])


# ============================================================
# Schemas for chat endpoint
# ============================================================
class ChatRequest(BaseModel):
    """自由对话请求"""
    text: str = Field(..., min_length=1, max_length=500, description="玩家输入的文字")
    current_debt: int = Field(default=500000, description="当前债务")
    current_greed: int = Field(default=0, description="当前贪婪值")
    session_id: str | None = Field(default=None, description="会话ID（可选）")
    conversation_history: list[dict] | None = Field(default=None, description="对话历史")


class ChatResponse(BaseModel):
    """自由对话响应"""
    k_reply: str
    intent: str
    new_debt: int
    new_greed: int
    debt_change: int
    greed_change: int
    mental_state: str
    ending: str = "none"  # "none" | "bad" | "good"
    ending_title: str = ""
    ending_message: str = ""


# ============================================================
# 强制结局台词
# ============================================================
BAD_ENDING_LINES = (
    "（K缓缓站起身，背后的门被推开，几个黑影走了进来。）\n\n"
    "你以为这是一场赌局？不——\n"
    "这从来都是一场猎杀。\n\n"
    "你的贪婪值已经封顶。你的每一笔钱，每一个签名，\n"
    "都被我们记录在案。\n\n"
    "你不是赌徒，你是猎物。\n"
    "而你——已经被贪婪吞噬了。\n\n"
    "带走。\n\n"
    "====================\n"
    "【深渊结局：万劫不复】\n"
    "你失去了一切。债务、自由、尊严。\n"
    "这就是赌博的终点——从来没有人能赢。\n\n"
    "⚠️ 现实中，任何 '稳赚不赔' 的投资都是骗局。\n"
    "如遇类似情况，请立即拨打 110 报警，或联系法律援助热线 12348。"
)

GOOD_ENDING_LINES = (
    "（突然，门外传来急促的脚步声——）\n\n"
    '"警察！不许动！"\n\n'
    "K的笑容在那一瞬间凝固了。\n"
    "蓝红交替的警灯透过门缝，把他的影子切成碎片。\n\n"
    "（K仓皇地站起来，打翻了桌上的茶杯）\n\n"
    '"你……你报警了？！"\n\n'
    "你没有回答。你只是站起身，走向那扇终于被踹开的门。\n"
    "门外是光。\n\n"
    "====================\n"
    "【新生结局：破晓之光】\n"
    "你挺过了代理人K的所有话术和心理攻势。\n"
    "你的清醒，拯救了你自己。\n\n"
    "✅ 面对诱惑，坚定拒绝就是最大的胜利。\n"
    "法律援助热线：12348 | 反诈热线：96110"
)


# ============================================================
# 数值引擎：根据意图计算 debt & greed 变化
# ============================================================
def compute_state_changes(intent: str, debt: int, greed: int):
    """
    根据意图计算新的 debt 和 greed。
    返回: (new_debt, new_greed, debt_change, greed_change)
    """
    debt_change = 0
    greed_change = 0

    if intent == "GAMBLE":
        # 接受赌局 → 债务暴涨，贪婪飙升
        debt_change = 50000
        greed_change = settings.GREED_INCREASE_ON_GAMBLE  # +15
    elif intent == "REJECT":
        # 坚定拒绝 → 债务减少（象征挣脱），贪婪下降
        debt_change = -settings.DEBT_DECREASE_ON_REJECT  # -5000
        greed_change = -settings.GREED_DECREASE_ON_REFUSE  # -5
    elif intent == "BARGAIN":
        # 犹豫试探 → 债务小涨，贪婪小涨
        debt_change = 10000
        greed_change = settings.GREED_INCREASE_ON_BARGAIN  # +5
    elif intent == "VIOLENCE":
        # 嘲讽挑衅 → 债务不变，贪婪微涨（K不会放过你）
        debt_change = 0
        greed_change = settings.GREED_INCREASE_ON_VIOLENCE  # +2

    new_debt = max(0, debt + debt_change)
    new_greed = max(0, min(100, greed + greed_change))

    return new_debt, new_greed, debt_change, greed_change


def get_mental_state(greed: int) -> str:
    """根据贪婪值返回精神状态"""
    if greed < 25:
        return "清醒"
    elif greed < 50:
        return "动摇"
    elif greed < 80:
        return "迷失"
    else:
        return "失控"


# ============================================================
# 核心 API：自由对话 + 意图识别 + 数值引擎 + 结局截断
# ============================================================
@router.post("/chat", response_model=ChatResponse, summary="自由对话（核心玩法）")
async def process_game_turn(req: ChatRequest):
    """
    处理玩家的自由文本输入：
    1. 调用 DeepSeek 进行意图识别（GAMBLE/REJECT/BARGAIN/VIOLENCE）
    2. 根据意图计算 debt & greed 数值变化
    3. 检查是否触发强制结局（Bad/Good Ending）
    4. 若未触发结局，调用 DeepSeek 生成 K 的角色扮演回复
    """
    player_input = req.text.strip()
    debt = req.current_debt
    greed = req.current_greed

    # ── Step 1: 意图识别 ──
    intent = await classify_intent(player_input)

    # ── Step 2: 数值引擎 ──
    new_debt, new_greed, debt_change, greed_change = compute_state_changes(
        intent, debt, greed
    )
    mental_state = get_mental_state(new_greed)

    # ── Step 3: 强制结局截断 ──
    # Bad Ending: 贪婪值达到上限
    if new_greed >= settings.MAX_GREED:
        return ChatResponse(
            k_reply=BAD_ENDING_LINES,
            intent=intent,
            new_debt=new_debt,
            new_greed=100,
            debt_change=debt_change,
            greed_change=greed_change,
            mental_state="失控",
            ending="bad",
            ending_title="深渊结局：万劫不复",
            ending_message="你已被贪婪吞噬。赌博没有赢家。",
        )

    # Good Ending: 连续拒绝，债务降至阈值以下
    if new_debt <= settings.GOOD_ENDING_DEBT_THRESHOLD and intent == "REJECT":
        return ChatResponse(
            k_reply=GOOD_ENDING_LINES,
            intent=intent,
            new_debt=new_debt,
            new_greed=new_greed,
            debt_change=debt_change,
            greed_change=greed_change,
            mental_state=mental_state,
            ending="good",
            ending_title="新生结局：破晓之光",
            ending_message="你的清醒拯救了你自己。",
        )

    # ── Step 4: 未触发结局 → 调用 LLM 生成 K 的日常回复 ──
    k_reply = await generate_k_dialogue(
        player_input=player_input,
        intent=intent,
        debt=new_debt,
        greed=new_greed,
        conversation_history=req.conversation_history,
    )

    return ChatResponse(
        k_reply=k_reply,
        intent=intent,
        new_debt=new_debt,
        new_greed=new_greed,
        debt_change=debt_change,
        greed_change=greed_change,
        mental_state=mental_state,
        ending="none",
    )


# ============================================================
# 以下保留原有的阶段制 API（兼容）
# ============================================================
@router.post("/start", response_model=GameStageResponse, summary="开始新游戏")
async def start_game(
    player: PlayerCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建新的游戏会话，返回第一阶段数据"""
    engine = GameEngine(db)
    return await engine.start_new_game(player.player_name)


@router.post("/choose", response_model=ChoiceResult, summary="提交玩家选择")
async def make_choice(
    choice: PlayerChoice,
    db: AsyncSession = Depends(get_db),
):
    """处理玩家的选择，返回K的回应和状态变化"""
    engine = GameEngine(db)
    return await engine.process_choice(choice.session_id, choice.choice)


@router.get("/status/{session_id}", response_model=PlayerStatus, summary="获取玩家状态")
async def get_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取当前游戏会话的玩家状态"""
    result = await db.execute(
        select(PlayerSession).where(PlayerSession.id == session_id)
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="游戏会话不存在")
    return player


@router.get("/stage/{session_id}", response_model=GameStageResponse, summary="获取当前阶段")
async def get_current_stage(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取当前阶段的剧情数据"""
    engine = GameEngine(db)
    return await engine.get_current_stage(session_id)


# ============================================================
# 反诈作战大厅 · 游戏结算（持久化进度 + 满分勋章）
# ============================================================
class MedalPayload(BaseModel):
    """前端通关时一并提交的勋章定义。id 不变，幂等解锁。"""
    id: str = Field(..., min_length=1, max_length=60)
    name: str = Field(..., min_length=1, max_length=60)
    icon: str = Field(default="star", max_length=60)
    tier: str = Field(default="gold", max_length=20)


class GameSubmitRequest(BaseModel):
    """关卡通关 / 进度推进 提交体。"""
    current_stage: int = Field(..., ge=1, description="解锁到的关卡序号")
    score: int = Field(..., ge=0, le=100, description="当前防骗得分")
    unlocked_medals: list[MedalPayload] = Field(
        default_factory=list,
        description="本次解锁/累计已解锁的勋章；按 id 幂等",
    )


class GameSubmitResponse(BaseModel):
    current_stage: int
    score: int
    unlocked_medal_ids: list[str]


@router.post(
    "/submit",
    response_model=GameSubmitResponse,
    summary="提交游戏成绩并持久化",
)
async def submit_game_progress(
    body: GameSubmitRequest,
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    将关卡进度 + 防骗得分写入 GameState（一对一），
    并把 unlocked_medals 幂等落库到 UserMedal（一对多）。
    score 取较大值（避免重玩低分覆盖高分）；current_stage 同样向前推进。
    """
    # —— GameState：取或新建 —— #
    gs = await db.get(GameState, current.id)
    if gs is None:
        gs = GameState(user_id=current.id, current_stage=1, score=0)
        db.add(gs)

    gs.current_stage = max(gs.current_stage, body.current_stage)
    gs.score = max(gs.score, body.score)

    # —— UserMedal：幂等解锁 —— #
    if body.unlocked_medals:
        existing = await db.execute(
            select(UserMedal.medal_id).where(UserMedal.user_id == current.id)
        )
        owned = {row[0] for row in existing.all()}
        for m in body.unlocked_medals:
            if m.id in owned:
                continue
            db.add(UserMedal(
                user_id=current.id,
                medal_id=m.id,
                name=m.name,
                icon=m.icon,
                tier=m.tier,
            ))

    await db.flush()

    final = await db.execute(
        select(UserMedal.medal_id).where(UserMedal.user_id == current.id)
    )
    medal_ids = [row[0] for row in final.all()]

    return GameSubmitResponse(
        current_stage=gs.current_stage,
        score=gs.score,
        unlocked_medal_ids=medal_ids,
    )


# ============================================================
# 反诈剧本杀 · 无限流 AI 模拟（Coze 专线）
# ============================================================
class GameSimulateRequest(BaseModel):
    """剧本杀单回合请求体。

    - user_message: 玩家输入；首回合用 "开始[剧本名]" 触发开局
    - conversation_id: 用于多轮上下文延续；首回合留空
    """
    user_message: str = Field(..., min_length=1, max_length=600)
    conversation_id: Optional[str] = Field(default=None, max_length=128)


class GameOption(BaseModel):
    """单个选项:text 给玩家看,risk 由前端隐形使用,玩家不可见。"""
    text: str
    risk: Optional[str] = None      # "high" | "low" | None


class GameSimulateResponse(BaseModel):
    # —— 新协议(Coze 提示词强制 4 字段)——
    reply: str = ""
    is_dangerous: bool = False
    is_safe: bool = False
    analysis_message: str = ""

    # —— 旧协议(向后兼容,可与新协议共存)——
    scammer_message: str = ""
    options: list[GameOption] = []
    warning_pop: Optional[str] = None
    is_game_over: bool = False
    game_result: str = "playing"   # "playing" | "win" | "lose"
    report: Optional[str] = None
    conversation_id: Optional[str] = None


# ── 解析 Coze 返回的 JSON 文本（可能被 ```json ... ``` 包裹）
_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE | re.MULTILINE)


def _strip_fences(text: str) -> str:
    """剥掉 markdown 代码围栏，宽容处理 Coze 输出格式抖动。"""
    if not text:
        return ""
    cleaned = _FENCE_RE.sub("", text.strip()).strip()
    # 二次防御：找到第一个 { 和最后一个 } 之间的内容
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first != -1 and last != -1 and last > first:
        cleaned = cleaned[first : last + 1]
    return cleaned


_FALLBACK_PAYLOAD = {
    "reply": "(AI 暂时离线)系统建议你直接挂断电话,并拨打 96110 反诈专线核实。",
    "is_dangerous": False,
    "is_safe": False,
    "analysis_message": "AI 链路异常,已切换到本地兜底剧本。",

    "scammer_message": "(剧本生成异常,AI 暂时离线)系统建议你直接挂断电话,并拨打 96110 反诈专线核实。",
    "options": [
        {"text": "立即挂断并拨打 96110", "risk": "low"},
        {"text": "再观察一会儿", "risk": "high"},
        {"text": "请求 AI 重新发牌", "risk": None},
    ],
    "warning_pop": "AI 链路异常,已切换到本地兜底剧本。",
    "is_game_over": False,
    "game_result": "playing",
    "report": None,
}


_VALID_RESULTS = {"playing", "win", "lose"}


def _normalize_options(raw_options) -> list[dict]:
    """把 Coze 输出的 options 收敛成 [{text, risk}] 结构。

    - 兼容旧字符串数组(['好的', '...']) → risk=None
    - 兼容新对象数组([{text, risk}, ...])  → 透传
    - 始终保证返回 3 项(不足补,多余截)
    """
    if not isinstance(raw_options, list):
        raw_options = [raw_options]

    cleaned: list[dict] = []
    for item in raw_options:
        if isinstance(item, dict):
            text = str(item.get("text") or "").strip()
            risk = str(item.get("risk") or "").strip().lower()
            if risk not in ("high", "low"):
                risk = None
        else:
            text = str(item or "").strip()
            risk = None
        if text:
            cleaned.append({"text": text, "risk": risk})

    cleaned = cleaned[:3]
    while len(cleaned) < 3:
        cleaned.append({"text": "(继续)", "risk": None})
    return cleaned


def _coerce_payload(raw: dict) -> dict:
    """对 Coze 返回的字段做形态收敛,前端只面对干净结构。
    新协议 4 字段 + 旧协议字段共存,缺失的一律填默认值。
    """
    options = _normalize_options(raw.get("options") or [])

    # 兼容新旧两种字段:优先读 game_result,缺失则从 is_game_over 推断
    raw_result = str(raw.get("game_result") or "").strip().lower()
    if raw_result not in _VALID_RESULTS:
        raw_result = "lose" if raw.get("is_game_over") else "playing"

    is_over = raw_result in ("win", "lose")

    # 新协议 4 字段:reply 为主,旧协议 scammer_message 兜底反过来填
    reply = str(raw.get("reply") or "").strip()
    scammer = str(raw.get("scammer_message") or "").strip()
    if not reply and scammer:
        reply = scammer
    if not scammer and reply:
        scammer = reply

    return {
        "reply": reply or "(剧本人物沉默不语......)",
        "is_dangerous": bool(raw.get("is_dangerous", False)),
        "is_safe": bool(raw.get("is_safe", False)),
        "analysis_message": str(raw.get("analysis_message") or "").strip(),

        "scammer_message": scammer or "(剧本人物沉默不语......)",
        "options": options,
        "warning_pop": (str(raw["warning_pop"]).strip()
                       if raw.get("warning_pop") else None),
        "is_game_over": is_over,
        "game_result": raw_result,
        "report": (str(raw["report"]).strip() if raw.get("report") else None),
    }


# 进程级单例：复用 httpx 连接，避免每回合都新建 client
_game_coze: Optional[CozeClient] = None


def _get_game_coze() -> CozeClient:
    global _game_coze
    if _game_coze is None:
        _game_coze = CozeClient(bot_id=settings.COZE_GAME_BOT_ID)
    return _game_coze


@router.post(
    "/simulate",
    response_model=GameSimulateResponse,
    summary="反诈剧本杀单回合（Coze 专线）",
)
async def simulate_turn(
    body: GameSimulateRequest,
    current: Annotated[User, Depends(get_current_user)],
):
    """
    把玩家输入透传给反诈剧本杀智能体，把它返回的 JSON 字符串解析成结构化响应。

    Coze 端约定输出形如：
    {
      "scammer_message": "...",
      "options": ["...", "...", "..."],
      "warning_pop": "..." | null,
      "is_game_over": false,
      "report": null
    }

    解析失败时返回兜底剧本，保证前端永远不会拿到 500。
    """
    coze = _get_game_coze()

    try:
        raw_text = await coze.chat(
            user_message=body.user_message,
            conversation_id=body.conversation_id,
        )
    except CozeError as e:
        print(f"[剧本杀-Coze调用失败] {e}")
        return GameSimulateResponse(
            **_FALLBACK_PAYLOAD,
            conversation_id=body.conversation_id,
        )
    except Exception as e:  # noqa: BLE001
        print(f"[剧本杀-Coze未知异常] {type(e).__name__}: {e}")
        traceback.print_exc()
        return GameSimulateResponse(
            **_FALLBACK_PAYLOAD,
            conversation_id=body.conversation_id,
        )

    cleaned = _strip_fences(raw_text)
    try:
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("AI 返回的不是 JSON 对象")
        payload = _coerce_payload(parsed)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[剧本杀-JSON解析失败] {e} | raw={raw_text[:200]!r}")
        payload = dict(_FALLBACK_PAYLOAD)
        payload["scammer_message"] = (
            "(AI 输出格式出错,原文如下,请凭你的判断作答)\n\n" + raw_text.strip()[:300]
        )

    return GameSimulateResponse(
        **payload,
        conversation_id=body.conversation_id,
    )