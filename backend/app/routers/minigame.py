"""
深渊契约 - 印第安扑克小游戏 API
DeepSeek 驱动的 AI 对手
"""
import random
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from app.config import settings

router = APIRouter(prefix="/api/minigame", tags=["印第安扑克"])

# DeepSeek 客户端
client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
)

# ============================================================
# 数据模型
# ============================================================
class PokerStartRequest(BaseModel):
    """开始新牌局"""
    player_chips: int = Field(default=50000, description="玩家筹码")
    k_chips: int = Field(default=50000, description="K的筹码")


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


class PokerActionRequest(BaseModel):
    """玩家行动 / 请求K行动"""
    round_id: int
    player_card: int = Field(description="玩家的牌（前端持有）")
    k_card: int = Field(description="K的牌")
    pot: int = Field(description="当前底池")
    player_chips: int = Field(description="玩家剩余筹码")
    k_chips: int = Field(description="K剩余筹码")
    player_action: str = Field(description="玩家行动: raise/call/fold/check")
    player_bet: int = Field(default=0, description="玩家下注金额（raise时）")
    round_history: list[str] = Field(default=[], description="本轮行动历史")
    game_history: str = Field(default="", description="之前几局的简要描述")


class PokerActionResponse(BaseModel):
    """K的回应"""
    k_action: str = Field(description="K的行动: raise/call/fold")
    k_bet: int = Field(default=0, description="K的下注金额")
    taunt: str = Field(description="K的嘲讽台词")
    new_pot: int = Field(description="更新后的底池")
    player_chips: int = Field(description="玩家剩余筹码")
    k_chips: int = Field(description="K剩余筹码")
    round_over: bool = Field(default=False, description="本轮是否结束")
    winner: str = Field(default="", description="赢家: player/k/none")
    reasoning: str = Field(default="", description="K的内心独白（调试用，前端可选展示）")


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
# K 的扑克 AI System Prompt
# ============================================================
K_POKER_SYSTEM_PROMPT = """你是"代理人K"，一个地下赌场的千王。你正在和一个欠债者玩印第安扑克。

## 游戏规则
- 牌面数字 1-10，数字大的赢
- 双方各抽一张牌贴在额头上
- 你能看到对方的牌，但看不到自己的牌
- 对方也能看到你的牌，但看不到自己的牌

## 当前局面
- 你（K）头上的牌: {k_card}（对手能看到这张牌）
- 对手头上的牌: {player_card}（你能看到，对手看不到）
- 当前底池: {pot} 筹码
- 你的筹码: {k_chips}
- 对手筹码: {player_chips}
- 对手刚才的行动: {player_action}
- 本轮行动历史: {round_history}

## 你的策略思考框架

### 第一步：分析已知信息
- 你知道对手牌是 {player_card}
- 你不知道自己的牌，但知道是 1-10 之间的某个数
- 你赢的概率 = (10 - {player_card}) / 9 （因为你的牌可能是 1-10 中除了对手牌以外的任何一张）

### 第二步：决定行动
基于概率和心理战术决定行动:

**诈唬策略（Bluff）**:
- 如果对手牌很大（7-10），他可能很自信。你可以考虑弃牌保存筹码，或者大胆加注诈唬
- 如果对手牌很小（1-3），他可能会紧张。你加注会很有效，因为你大概率能赢

**价值下注（Value Bet）**:
- 如果对手牌很小，你大概率能赢，应该加注以赚取更多筹码

**保守策略**:
- 如果局面不明朗，可以选择跟注

### 第三步：台词风格
- 你是一个冷酷、精于算计的赌场老手
- 诈唬时要表现得极度自信
- 拿到好位置时反而可以故意示弱
- 台词要简短有力，带有压迫感
- 可以嘲讽对手的犹豫、恐惧、贪婪

## 你必须返回以下严格的 JSON 格式（不要有任何多余内容）:

{{
  "action": "raise 或 call 或 fold",
  "amount": 数字(仅raise时有意义,call和fold时为0),
  "taunt": "你的嘲讽台词（中文，30字以内）",
  "reasoning": "你的内心分析（中文，简短）"
}}

## 约束规则
1. amount 不能超过你的剩余筹码 {k_chips}
2. amount 不能超过对手剩余筹码 {player_chips}（不能下注超过对手能跟的数量）
3. raise 时 amount 最少为 1000
4. 如果对手 fold 了，你不需要行动（这种情况不会调用你）
5. 只返回 JSON，不要有任何其他文字"""


# ============================================================
# API 端点
# ============================================================

@router.post("/start", response_model=PokerStartResponse, summary="开始新一轮")
async def start_round(req: PokerStartRequest):
    """发牌，开始新一轮印第安扑克"""
    # 从 1-10 随机抽两张不同的牌
    cards = random.sample(range(1, 11), 2)
    player_card = cards[0]
    k_card = cards[1]
    ante = 1000

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
    )


@router.post("/action", response_model=PokerActionResponse, summary="处理行动")
async def poker_action(req: PokerActionRequest):
    """
    处理玩家行动，然后调用 DeepSeek 让 K 做决策。
    流程: 玩家行动 → 更新状态 → K决策 → 返回结果
    """
    pot = req.pot
    player_chips = req.player_chips
    k_chips = req.k_chips
    history = list(req.round_history)

    # ── 处理玩家行动 ──
    if req.player_action == "fold":
        # 玩家弃牌，K 赢得底池
        k_chips += pot
        return PokerActionResponse(
            k_action="win",
            k_bet=0,
            taunt="（K轻轻摇头）连看一眼的勇气都没有吗？",
            new_pot=0,
            player_chips=player_chips,
            k_chips=k_chips,
            round_over=True,
            winner="k",
            reasoning="玩家弃牌，K自动获胜",
        )

    elif req.player_action == "raise":
        bet = min(req.player_bet, player_chips, k_chips)
        bet = max(bet, 1000)
        player_chips -= bet
        pot += bet
        history.append(f"玩家加注{bet}")

    elif req.player_action == "call":
        history.append("玩家跟注")

    elif req.player_action == "check":
        history.append("玩家过牌")

    # ── 调用 DeepSeek 让 K 决策 ──
    k_decision = await get_k_decision(
        player_card=req.player_card,
        k_card=req.k_card,
        pot=pot,
        player_chips=player_chips,
        k_chips=k_chips,
        player_action=req.player_action,
        round_history=history,
    )

    k_action = k_decision.get("action", "call")
    k_amount = k_decision.get("amount", 0)
    taunt = k_decision.get("taunt", "……")
    reasoning = k_decision.get("reasoning", "")

    round_over = False
    winner = ""

    if k_action == "fold":
        # K 弃牌，玩家赢得底池
        player_chips += pot
        pot = 0
        round_over = True
        winner = "player"

    elif k_action == "raise":
        k_amount = min(k_amount, k_chips, player_chips)
        k_amount = max(k_amount, 1000)
        k_chips -= k_amount
        pot += k_amount
        history.append(f"K加注{k_amount}")

    elif k_action == "call":
        # 跟注 = 双方匹配，然后开牌
        # 如果玩家之前是 raise，K 需要匹配差额
        if req.player_action == "raise":
            match_amount = min(req.player_bet, k_chips)
            k_chips -= match_amount
            pot += match_amount
        history.append("K跟注")
        # 跟注后开牌
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

    return PokerActionResponse(
        k_action=k_action,
        k_bet=k_amount if k_action == "raise" else 0,
        taunt=taunt,
        new_pot=pot,
        player_chips=player_chips,
        k_chips=k_chips,
        round_over=round_over,
        winner=winner,
        reasoning=reasoning,
    )


@router.post("/reveal", response_model=PokerRevealResponse, summary="开牌")
async def reveal_cards(req: PokerRevealRequest):
    """强制开牌（用于双方都不弃牌的情况）"""
    pot = req.pot
    player_chips = req.player_chips
    k_chips = req.k_chips

    if req.player_card > req.k_card:
        winner = "player"
        player_chips += pot
        taunt = "（K沉默地看着翻开的牌）……运气不错。但运气不会永远站在你这边。"
    elif req.player_card < req.k_card:
        winner = "k"
        k_chips += pot
        taunt = "（K露出微笑）看到了吗？这就是实力的差距。"
    else:
        winner = "draw"
        player_chips += pot // 2
        k_chips += pot // 2
        taunt = "（K挑了挑眉）平局？有意思。"

    game_over = player_chips <= 0 or k_chips <= 0
    game_over_reason = ""
    if player_chips <= 0:
        game_over_reason = "player_bankrupt"
    elif k_chips <= 0:
        game_over_reason = "k_bankrupt"

    return PokerRevealResponse(
        player_card=req.player_card,
        k_card=req.k_card,
        winner=winner,
        pot_won=pot,
        taunt=taunt,
        player_chips=player_chips,
        k_chips=k_chips,
        game_over=game_over,
        game_over_reason=game_over_reason,
    )


# ============================================================
# DeepSeek AI 决策
# ============================================================
async def get_k_decision(
    player_card: int,
    k_card: int,
    pot: int,
    player_chips: int,
    k_chips: int,
    player_action: str,
    round_history: list[str],
) -> dict:
    """调用 DeepSeek 获取 K 的扑克决策"""

    system_prompt = K_POKER_SYSTEM_PROMPT.format(
        k_card=k_card,
        player_card=player_card,
        pot=pot,
        k_chips=k_chips,
        player_chips=player_chips,
        player_action=player_action,
        round_history=" → ".join(round_history) if round_history else "无",
    )

    user_prompt = (
        f"对手头上的牌是 {player_card}，"
        f"你头上的牌是 {k_card}（但你假装不知道自己的牌），"
        f"当前底池 {pot}，"
        f"对手刚才 {player_action}。"
        f"请做出你的决策，只返回JSON。"
    )

    try:
        response = await client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=200,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content.strip()
        decision = json.loads(content)

        # 校验字段
        action = decision.get("action", "call").lower()
        if action not in ("raise", "call", "fold"):
            action = "call"

        amount = int(decision.get("amount", 0))
        if action == "raise":
            amount = max(1000, min(amount, k_chips, player_chips))
        else:
            amount = 0

        return {
            "action": action,
            "amount": amount,
            "taunt": decision.get("taunt", "……"),
            "reasoning": decision.get("reasoning", ""),
        }

    except json.JSONDecodeError as e:
        print(f"[K决策JSON解析失败] {e}")
        # 降级策略：基于概率做简单决策
        return fallback_decision(player_card, k_card, pot, k_chips, player_chips)

    except Exception as e:
        print(f"[K决策调用失败] {e}")
        return fallback_decision(player_card, k_card, pot, k_chips, player_chips)


def fallback_decision(
    player_card: int, k_card: int, pot: int, k_chips: int, player_chips: int
) -> dict:
    """
    降级策略：当 DeepSeek 不可用时，用简单概率逻辑决策。
    K 知道对手的牌（player_card），但"假装"不知道自己的牌。
    实际上我们也知道 k_card，所以可以做出合理的AI行为。
    """
    win_prob = (10 - player_card) / 9  # K赢的概率

    if win_prob >= 0.7:
        # 大概率赢，价值下注
        bet = min(random.choice([2000, 3000, 5000]), k_chips, player_chips)
        return {
            "action": "raise",
            "amount": bet,
            "taunt": "呵。要不要加点注？让游戏更刺激一些。",
            "reasoning": f"对手牌{player_card}较小，我大概率赢，价值加注",
        }
    elif win_prob >= 0.4:
        # 五五开，跟注观察
        return {
            "action": "call",
            "amount": 0,
            "taunt": "跟。",
            "reasoning": f"对手牌{player_card}中等，局面不明朗，选择跟注",
        }
    else:
        # 大概率输
        bluff_roll = random.random()
        if bluff_roll < 0.3:
            # 30% 概率诈唬
            bet = min(random.choice([3000, 5000]), k_chips, player_chips)
            return {
                "action": "raise",
                "amount": bet,
                "taunt": "你确定要跟吗？想清楚了再说。",
                "reasoning": f"对手牌{player_card}较大，选择诈唬",
            }
        else:
            return {
                "action": "fold",
                "amount": 0,
                "taunt": "这局不玩了。小鱼不值得下网。",
                "reasoning": f"对手牌{player_card}较大，选择弃牌保存筹码",
            }