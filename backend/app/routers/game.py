from typing import Annotated
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