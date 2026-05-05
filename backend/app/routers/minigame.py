"""
深渊契约 - 印第安扑克小游戏 API
剧本控命运，AI 控表现 - 状态机驱动的反诈教育游戏
"""
import random
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.models.game_stage import GameStage
from app.services.stage_machine import StageMachine
from app.services.ai_decision import generate_k_decision

router = APIRouter(prefix="/api/minigame", tags=["印第安扑克"])

# ============================================================
# 数据模型 - 扩展支持状态机
# ============================================================
class PokerStartRequest(BaseModel):
    """开始新牌局"""
    player_chips: int = Field(default=10000, description="玩家筹码")
    k_chips: int = Field(default=50000, description="K的筹码")
    game_stage: str = Field(default=GameStage.BAIT.value, description="当前游戏阶段")
    bait_wins: int = Field(default=0, description="养猪阶段连赢次数")
    hook_rounds: int = Field(default=0, description="高端局已玩局数")


class PokerStartResponse(BaseModel):
    """发牌结果"""
    round_id: int
    player_card: int = Field(description="玩家的牌（玩家看不到，但前端需要最终开牌用）")
    k_card: int = Field(description="K的牌（玩家能看到）")
    player_card_hidden: bool = True
    pot: int = Field(description="当前底池")
    ante: int = Field(description="底注")
    player_chips: int
    k_chips: int
    message: str

    # 状态机字段
    game_stage: str
    stage_title: str
    stage_hint: str


class PokerActionRequest(BaseModel):
    """玩家行动 / 请求K行动"""
    round_id: int
    player_card: int = Field(description="玩家的牌（前端持有）")
    k_card: int = Field(description="K的牌")
    pot: int = Field(description="当前底池")
    player_chips: int = Field(description="玩家剩余筹码")
    k_chips: int = Field(description="K剩余筹码")
    player_action: str = Field(description="玩家行动: raise/call/fold")
    player_bet: int = Field(default=0, description="玩家下注金额（raise时）")
    round_history: list[str] = Field(default=[], description="本轮行动历史")

    # 状态机字段
    game_stage: str = Field(default=GameStage.BAIT.value)
    bait_wins: int = Field(default=0)
    hook_rounds: int = Field(default=0)
    loan_accepted: bool = Field(default=False)


class PokerActionResponse(BaseModel):
    """K的回应"""
    k_action: str = Field(description="K的行动: RAISE/CALL/FOLD")
    k_bet: int = Field(default=0, description="K的下注金额")
    taunt: str = Field(description="K的嘲讽台词")
    new_pot: int = Field(description="更新后的底池")
    player_chips: int = Field(description="玩家剩余筹码")
    k_chips: int = Field(description="K剩余筹码")
    round_over: bool = Field(default=False, description="本轮是否结束")
    winner: str = Field(default="", description="赢家: player/k/draw")
    game_over: bool = Field(default=False, description="游戏是否结束")
    game_over_reason: str = Field(default="", description="结束原因: player_bankrupt/k_bankrupt/account_frozen")

    # 状态机字段
    game_stage: str
    stage_changed: bool = Field(default=False, description="是否发生阶段切换")
    stage_title: str = Field(default="")
    stage_hint: str = Field(default="")
    bait_wins: int = Field(default=0)
    hook_rounds: int = Field(default=0)


class PokerRevealRequest(BaseModel):
    """开牌请求"""
    player_card: int
    k_card: int
    pot: int
    player_chips: int
    k_chips: int


class PokerRevealResponse(BaseModel):
    """开牌结果"""
    player_card: int
    k_card: int
    winner: str = Field(description="player/k/draw")
    pot_won: int
    taunt: str
    player_chips: int
    k_chips: int
    game_over: bool = False
    game_over_reason: str = ""


# ============================================================
# 破产嘲讽台词
# ============================================================
PLAYER_BANKRUPT_TAUNT = (
    "（K站起身来，居高临下地看着你）\n\n"
    "这就榨干了？\n"
    "连高利贷都还不起的人，果然在牌桌上也是这副德行。\n\n"
    "（他掐灭了烟，语气冷到骨子里）\n\n"
    "既然筹码输光了——\n"
    "那就只能拿你这个人来抵债了。\n\n"
    "远洋渔船的合同我已经替你签好了。三年。\n"
    "别挣扎了。从你坐下来的那一刻起，结局就已经注定了。"
)

K_BANKRUPT_TAUNT = (
    "（K的最后一枚筹码滑入你的手中。他愣住了。）\n\n"
    "……你居然赢了。\n\n"
    "（但他的脸上，渐渐浮起一个让你不寒而栗的笑容）\n\n"
    "不过——你以为赢了筹码，就赢了一切？"
)

ACCOUNT_FROZEN_TAUNT = (
    "（就在你准备开牌的瞬间，屏幕突然黑了）\n\n"
    "系统提示：账户异常，提现通道已关闭\n\n"
    "（K的笑声在黑暗中回荡）\n\n"
    "从一开始，你就没有赢的可能。\n"
    "这是一场猎杀，而你——是猎物。"
)


# ============================================================
# API 端点 - 状态机驱动
# ============================================================

@router.post("/start", response_model=PokerStartResponse, summary="开始新一轮")
async def start_round(req: PokerStartRequest):
    """
    发牌，开始新一轮印第安扑克
    集成状态机：根据阶段控制发牌逻辑
    """
    # 破产保护
    if req.player_chips <= 0 or req.k_chips <= 0:
        raise HTTPException(
            status_code=400,
            detail="筹码不足，无法继续游戏"
        )

    # 获取阶段配置
    stage_config = StageMachine.get_stage_config(req.game_stage)
    ante = min(stage_config["ante"], req.player_chips, req.k_chips)

    # ===== 发牌作弊机制 =====
    player_card, k_card = StageMachine.deal_cards_with_cheat(
        stage=req.game_stage,
        player_chips=req.player_chips,
        k_chips=req.k_chips
    )

    # 扣除底注
    player_chips = req.player_chips - ante
    k_chips = req.k_chips - ante
    pot = ante * 2

    return PokerStartResponse(
        round_id=random.randint(1000, 9999),
        player_card=player_card,
        k_card=k_card,
        player_card_hidden=True,
        pot=pot,
        ante=ante,
        player_chips=player_chips,
        k_chips=k_chips,
        message=f"牌已发出。你看到K头上的牌是 {k_card}。你的牌……你看不到。",
        game_stage=req.game_stage,
        stage_title=stage_config["title"],
        stage_hint=stage_config["hint"],
    )


@router.post("/action", response_model=PokerActionResponse, summary="处理行动")
async def poker_action(req: PokerActionRequest):
    """
    处理玩家行动 + K 决策 + 阶段流转
    核心流程：
    1. 处理玩家行动（扣筹码）
    2. 调用 AI 决策引擎（DeepSeek）
    3. 处理 K 的行动
    4. 结算（如果需要）
    5. 检查阶段流转
    6. 检查破产/冻结
    """
    pot = req.pot
    player_chips = req.player_chips
    k_chips = req.k_chips
    history = list(req.round_history)
    game_stage = req.game_stage
    bait_wins = req.bait_wins
    hook_rounds = req.hook_rounds

    # ── Step 1: 处理玩家行动 ──
    if req.player_action == "fold":
        # 玩家弃牌，K 赢得底池
        k_chips += pot
        return PokerActionResponse(
            k_action="WIN",
            k_bet=0,
            taunt="（K轻轻摇头）连看一眼的勇气都没有吗？",
            new_pot=0,
            player_chips=player_chips,
            k_chips=k_chips,
            round_over=True,
            winner="k",
            game_stage=game_stage,
            bait_wins=bait_wins,
            hook_rounds=hook_rounds,
        )

    elif req.player_action == "raise":
        bet = min(req.player_bet, player_chips, k_chips)
        bet = max(bet, min(1000, player_chips))
        if bet <= 0:
            history.append("玩家跟注（筹码不足加注）")
        else:
            player_chips -= bet
            pot += bet
            history.append(f"玩家加注{bet}")

    elif req.player_action == "call":
        history.append("玩家跟注")

    # ── Step 2: 调用 AI 决策引擎 ──
    k_decision = await generate_k_decision(
        stage=game_stage,
        player_card=req.player_card,
        k_card=req.k_card,
        pot=pot,
        player_chips=player_chips,
        k_chips=k_chips,
        player_action=req.player_action,
        round_history=history,
    )

    k_action = k_decision["action"]
    k_amount = k_decision["raise_amount"]
    taunt = k_decision["taunt"]

    # ===== All-in 强制摊牌：玩家筹码为 0 后，K 只能 CALL（直接开牌） =====
    if player_chips <= 0 and req.player_action == "raise":
        if k_action == "RAISE":
            k_action = "CALL"
            k_amount = 0
            taunt = "（K冷笑）既然你已经梭哈了，那就开牌吧。"

    round_over = False
    winner = ""

    # ── Step 3: 处理 K 的行动 ──
    if k_action == "FOLD":
        # K 弃牌，玩家赢得底池
        player_chips += pot
        pot = 0
        round_over = True
        winner = "player"

    elif k_action == "RAISE":
        max_raise_cap = min(k_chips, player_chips)
        if max_raise_cap < 1000:
            # 无法满足最低加注额，降级为 CALL
            k_action = "CALL"
            k_amount = 0
            history.append("K跟注（筹码不足加注）")
        else:
            k_amount = min(k_amount, max_raise_cap)
            k_amount = max(k_amount, 1000)
            k_chips -= k_amount
            pot += k_amount
            history.append(f"K加注{k_amount}")

    if k_action == "CALL":
        # 跟注后开牌
        if req.player_action == "raise":
            match_amount = min(req.player_bet, k_chips)
            k_chips -= match_amount
            pot += match_amount
        history.append("K跟注")

        # ── Step 4: 开牌结算 ──
        round_over = True
        if req.player_card > req.k_card:
            winner = "player"
            player_chips += pot
        elif req.player_card < req.k_card:
            winner = "k"
            k_chips += pot
        else:
            winner = "draw"
            player_chips += pot // 2
            k_chips += pot // 2
        pot = 0

    # 强制筹码下限保护
    player_chips = max(0, player_chips)
    k_chips = max(0, k_chips)

    # ── Step 5: 阶段流转判定 ──
    stage_changed = False
    new_stage = game_stage

    # 更新阶段进度
    if round_over and winner == "player":
        if game_stage == GameStage.BAIT:
            bait_wins += 1
        hook_rounds += 1

    # 检查是否需要切换阶段
    should_transition, next_stage, reason = StageMachine.check_stage_transition(
        current_stage=game_stage,
        player_chips=player_chips,
        bait_wins=bait_wins,
        hook_rounds=hook_rounds,
        loan_accepted=req.loan_accepted,
    )

    if should_transition:
        stage_changed = True
        new_stage = next_stage
        print(f"[阶段流转] {game_stage} → {new_stage} | 原因: {reason}")

    # 获取新阶段配置
    stage_config = StageMachine.get_stage_config(new_stage)

    # ── Step 6: 破产判定 ──
    game_over = False
    game_over_reason = ""

    if round_over:
        if player_chips <= 0:
            game_over = True
            game_over_reason = "player_bankrupt"
            taunt = PLAYER_BANKRUPT_TAUNT
        elif k_chips <= 0:
            game_over = True
            game_over_reason = "k_bankrupt"
            taunt = K_BANKRUPT_TAUNT

    # ── Step 7: 终局冻结判定 ──
    if new_stage == GameStage.VERDICT and round_over:
        game_over = True
        game_over_reason = "account_frozen"
        taunt = ACCOUNT_FROZEN_TAUNT

    return PokerActionResponse(
        k_action=k_action,
        k_bet=k_amount if k_action == "RAISE" else 0,
        taunt=taunt,
        new_pot=pot,
        player_chips=player_chips,
        k_chips=k_chips,
        round_over=round_over,
        winner=winner,
        game_over=game_over,
        game_over_reason=game_over_reason,
        game_stage=new_stage,
        stage_changed=stage_changed,
        stage_title=stage_config["title"],
        stage_hint=stage_config["hint"],
        bait_wins=bait_wins,
        hook_rounds=hook_rounds,
    )
