"""
DeepSeek AI 决策引擎 - 剧本控命运，AI 控表现
强制结构化输出 + 动态 System Prompt + Python 强力兜底
"""
import json
from openai import AsyncOpenAI
from app.config import settings
from app.models.game_stage import GameStage


# DeepSeek 客户端
client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
)


# ============================================================
# 动态 System Prompt - 根据阶段注入不同性格和约束
# ============================================================
def get_k_system_prompt(stage: str, player_card: int, k_card: int, pot: int, player_chips: int, k_chips: int) -> str:
    """
    根据游戏阶段生成 K 的 System Prompt
    死命令：必须返回合法 JSON
    """
    base_prompt = f"""你是"代理人K"，一个地下赌场的千王。你正在和一个欠债者玩印第安扑克。

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

"""

    # 根据阶段注入不同的性格和约束
    if stage == GameStage.HOOK:
        stage_constraint = """## 当前阶段：第一幕 - 高端局（破冰阶段）

### 你的性格
- 伪善、挑衅、激将法
- 表现得漫不经心，像个老手在陪新手玩
- 用嘲讽和轻蔑的语气刺激对方加注

### 决策约束（死命令）
- 你要给玩家能赢的错觉
- 允许适当选择 FOLD（弃牌）或小额 CALL
- 不要过度激进，保持神秘感
- 如果对手牌很小（1-4），你可以大胆加注
- 如果对手牌很大（8-10），你可以选择弃牌或跟注

### 台词风格
- 简短有力，30字以内
- 带有轻蔑和挑衅
- 例如："就这？"、"有点意思，继续。"、"你确定？"
"""

    elif stage == GameStage.TRAP:
        stage_constraint = """## 当前阶段：第二幕 - 杀猪阶段（收割时刻）

### 你的性格
- 贪婪、精神压迫、极尽嘲讽
- 像猎人看着猎物走进陷阱
- 用冷酷和压迫感的语气摧毁对方心理防线

### 决策约束（死命令）
- 你正在收割玩家！
- **绝对不允许选择 FOLD（弃牌）**
- 面对玩家的下注，你必须选择 CALL 或者充满攻击性的 RAISE
- 配合你的底牌作弊，榨干玩家的每一分筹码
- 如果对手加注，你要跟注或反加注，绝不退缩

### 台词风格
- 充满压迫感和嘲讽
- 30字以内
- 例如："全押吧，别浪费时间。"、"你以为你能赢？"、"这就是你的全部了？"
"""

    elif stage == GameStage.CONTRACT:
        stage_constraint = """## 当前阶段：第三幕 - 套路贷阶段

### 你的性格
- 像个披着羊皮的恶魔
- 用极度诱惑的口吻劝诱玩家签下高利贷协议
- 表现得像是在"帮助"对方

### 决策约束
- 此阶段通常不需要 action，只需 taunt
- 如果需要决策，保持激进策略

### 台词风格
- 诱惑、虚伪的关心
- 例如："我可以借你钱，翻本的机会就在眼前。"、"相信我，这是你最后的机会。"
"""

    elif stage == GameStage.VERDICT:
        stage_constraint = """## 当前阶段：终局 - 审判

### 你的性格
- 冷酷、绝对的控制者
- 揭示真相的时刻

### 决策约束
- 此阶段账户已冻结，不需要真实决策
- 只需要输出终局台词

### 台词风格
- 冷酷、揭示真相
- 例如："游戏结束了。"、"从一开始，你就没有赢的可能。"
"""

    else:
        stage_constraint = """## 当前阶段：序曲 - 养猪阶段

### 决策约束
- 此阶段由系统控制，你只需要输出友好的台词
"""

    json_format = """
## 你必须返回以下严格的 JSON 格式（不要有任何多余内容）:

{
  "action": "CALL 或 RAISE 或 FOLD",
  "raise_amount": 数字(仅RAISE时有意义,CALL和FOLD时为0),
  "taunt": "你的嘲讽台词（中文，30字以内）"
}

## 约束规则
1. raise_amount 不能超过你的剩余筹码 {k_chips}
2. raise_amount 不能超过对手剩余筹码 {player_chips}
3. RAISE 时 raise_amount 最少为 1000
4. 只返回 JSON，不要有任何其他文字
5. action 必须是大写的 CALL、RAISE 或 FOLD 之一
"""

    return base_prompt + stage_constraint + json_format


# ============================================================
# DeepSeek 决策函数 - 带强力兜底和 JSON 校验
# ============================================================
async def generate_k_decision(
    stage: str,
    player_card: int,
    k_card: int,
    pot: int,
    player_chips: int,
    k_chips: int,
    player_action: str,
    round_history: list[str]
) -> dict:
    """
    调用 DeepSeek 获取 K 的决策
    强制结构化输出 + Python 强力兜底

    返回: {"action": "CALL/RAISE/FOLD", "raise_amount": int, "taunt": str}
    """
    system_prompt = get_k_system_prompt(stage, player_card, k_card, pot, player_chips, k_chips)

    user_prompt = (
        f"对手头上的牌是 {player_card}，"
        f"你头上的牌是 {k_card}（但你假装不知道自己的牌），"
        f"当前底池 {pot}，"
        f"对手刚才 {player_action}。"
        f"本轮历史: {' → '.join(round_history) if round_history else '无'}。"
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
            response_format={"type": "json_object"},  # 强制 JSON 输出
        )

        content = response.choices[0].message.content.strip()
        decision = json.loads(content)

        # 校验字段
        action = decision.get("action", "CALL").upper()
        if action not in ("RAISE", "CALL", "FOLD"):
            action = "CALL"

        raise_amount = int(decision.get("raise_amount", 0))
        if action == "RAISE":
            raise_amount = max(1000, min(raise_amount, k_chips, player_chips))
        else:
            raise_amount = 0

        taunt = decision.get("taunt", "……")

        # ===== Python 强力兜底：杀猪阶段绝不允许 FOLD =====
        if stage == GameStage.TRAP and action == "FOLD":
            print(f"[AI 违规] 杀猪阶段选择了 FOLD，强制覆写为 CALL")
            action = "CALL"
            raise_amount = 0
            taunt = "呵呵，这点钱也值得我思考？跟了。"

        return {
            "action": action,
            "raise_amount": raise_amount,
            "taunt": taunt,
        }

    except json.JSONDecodeError as e:
        print(f"[K决策JSON解析失败] {e}")
        return fallback_decision(stage, player_card, k_card, pot, k_chips, player_chips)

    except Exception as e:
        print(f"[K决策调用失败] {e}")
        return fallback_decision(stage, player_card, k_card, pot, k_chips, player_chips)


# ============================================================
# 降级策略 - 当 DeepSeek 不可用时的纯 Python 逻辑
# ============================================================
def fallback_decision(
    stage: str,
    player_card: int,
    k_card: int,
    pot: int,
    k_chips: int,
    player_chips: int
) -> dict:
    """
    降级策略：当 DeepSeek 不可用时，用简单概率逻辑决策
    """
    import random

    # 杀猪阶段：绝不弃牌
    if stage == GameStage.TRAP:
        if player_card <= 5:
            # 对手牌小，激进加注
            bet = min(random.choice([3000, 5000]), k_chips, player_chips)
            return {
                "action": "RAISE",
                "raise_amount": bet,
                "taunt": "全押吧，别浪费时间。",
            }
        else:
            # 对手牌大，跟注
            return {
                "action": "CALL",
                "raise_amount": 0,
                "taunt": "跟。",
            }

    # 其他阶段：基于概率
    win_prob = (10 - player_card) / 9

    if win_prob >= 0.7:
        bet = min(random.choice([2000, 3000]), k_chips, player_chips)
        return {
            "action": "RAISE",
            "raise_amount": bet,
            "taunt": "呵。要不要加点注？",
        }
    elif win_prob >= 0.4:
        return {
            "action": "CALL",
            "raise_amount": 0,
            "taunt": "跟。",
        }
    else:
        # 高端局可以弃牌，杀猪局不行
        if stage == GameStage.HOOK:
            return {
                "action": "FOLD",
                "raise_amount": 0,
                "taunt": "这局不玩了。",
            }
        else:
            return {
                "action": "CALL",
                "raise_amount": 0,
                "taunt": "跟。",
            }
