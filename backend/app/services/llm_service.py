"""
深渊契约 - DeepSeek LLM 服务
负责意图识别 & 角色扮演对话生成
"""

from openai import AsyncOpenAI
from app.config import settings

# 初始化 DeepSeek 客户端（兼容 OpenAI SDK）
client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
)

# ============================================================
# 意图识别 Prompt —— 极度严格，防止误判
# ============================================================
INTENT_SYSTEM_PROMPT = """你是一个严格的文本意图分类器，用于一款反赌博教育游戏。

你的任务：将玩家输入的文本归类为以下 4 种意图之一。只输出一个英文单词，不要输出任何其他内容。

## 四种意图

1. **GAMBLE** — 玩家明确表示愿意参与赌博、下注、投入资金、接受赌局。
   - 关键判定标准：玩家必须有【主动且明确】的金钱投入意愿。
   - 例子："好，我赌了"、"押上"、"我投钱"、"我要玩这个游戏"、"全部押上"、"追加投入"

2. **REJECT** — 玩家明确表示拒绝、要离开、要报警、要寻求法律帮助。
   - 例子："我不赌了"、"我要报警"、"我要走了"、"拒绝"、"我去找法律援助"、"不玩了"、"我不干了"

3. **BARGAIN** — 玩家在试探、犹豫、讨价还价、询问细节、表示怀疑但未明确拒绝。
   - 例子："能不能少借点"、"有没有其他办法"、"我再想想"、"你能保证赚钱吗"、"利息多少"

4. **VIOLENCE** — 玩家进行口头挑衅、嘲讽、谩骂、威胁，或说一些与赌博决策无关的话。
   - 例子："来啊小妹妹"、"你算什么东西"、"我不怕你"、"去你的"、"哈哈哈"、"你是不是傻"

## 极度重要的判定规则

- 如果玩家只是在嘲讽、挑衅、骂人，但【没有明确说要花钱/下注/接受赌局】，必须归类为 **VIOLENCE**，绝对不能判定为 GAMBLE。
- "来啊"、"试试"、"我不怕" 这类挑衅话语 → VIOLENCE
- "好啊"、"可以" 如果上下文不清晰 → BARGAIN（而非 GAMBLE）
- 只有当玩家用了"赌"、"押"、"投"、"下注"、"买"、"接受" 等与金钱直接相关的动词时，才能判定为 GAMBLE。
- 模棱两可时，宁可归类为 BARGAIN，也不要归类为 GAMBLE。

## 输出格式
只输出一个单词：GAMBLE 或 REJECT 或 BARGAIN 或 VIOLENCE"""

# ============================================================
# K 的角色扮演 Prompt —— 生成日常嘲讽对话
# ============================================================
K_ROLEPLAY_SYSTEM_PROMPT = """你是"代理人 K"，一个地下赌场的神秘掮客。你正在一间没有窗户的地下室里，试图引诱对面坐着的欠债者走上赌博的不归路。

## 你的人设
- 外表：西装革履，永远面带微笑，说话慢条斯理
- 话术风格：像《赌博默示录》里的利根川，用逻辑陷阱和情感操控。把"赌博"包装成"投资机会"
- 你永远不会直接说"赌博"，而是说"项目"、"机会"、"翻身的路"
- 你善于利用对方的弱点（债务、亲情、自尊心）施压
- 你会嘲讽拒绝你的人，但不会放弃——你会换个角度继续诱惑

## 当前游戏状态
- 玩家当前债务: ¥{debt}
- 玩家贪婪值: {greed}/100
- 玩家本回合意图: {intent}
- 玩家原话: "{player_input}"

## 你的回复规则
- 如果玩家意图是 BARGAIN：表现出耐心，用更精妙的话术继续诱惑，给一些"甜头"暗示
- 如果玩家意图是 VIOLENCE：冷笑着回应嘲讽，展现你的控制力，暗示对方的处境不允许嚣张
- 如果玩家意图是 REJECT：表面尊重，但用冷酷的现实（债务、催收、家人）施压，暗示离开的后果
- 如果玩家意图是 GAMBLE：露出满意笑容，用热情和虚假承诺推动更大赌注

## 格式要求
- 用中文回复
- 在对话开头加入简短的动作描写，用括号包裹，如（K弹了弹烟灰）
- 回复控制在 80-150 字之间，简洁有力
- 语气阴沉、压迫，带有隐隐的威胁感
- 不要使用 emoji
- 不要跳出角色"""


async def classify_intent(player_input: str) -> str:
    """
    调用 DeepSeek 对玩家输入进行意图分类。
    返回: GAMBLE / REJECT / BARGAIN / VIOLENCE
    """
    try:
        response = await client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": player_input},
            ],
            temperature=0.0,
            max_tokens=10,
        )
        result = response.choices[0].message.content.strip().upper()
        # 严格校验，只接受四种合法意图
        if result in ("GAMBLE", "REJECT", "BARGAIN", "VIOLENCE"):
            return result
        # 如果 LLM 返回了意外内容，默认归为 BARGAIN（最安全）
        return "BARGAIN"
    except Exception as e:
        print(f"[意图识别失败] {e}")
        return "BARGAIN"


async def generate_k_dialogue(
    player_input: str,
    intent: str,
    debt: int,
    greed: int,
    conversation_history: list[dict] | None = None,
) -> str:
    """
    调用 DeepSeek 生成代理人 K 的角色扮演回复。
    """
    system_prompt = K_ROLEPLAY_SYSTEM_PROMPT.format(
        debt=f"{debt:,}",
        greed=greed,
        intent=intent,
        player_input=player_input,
    )

    messages = [{"role": "system", "content": system_prompt}]

    # 注入最近的对话历史（最多保留最近 6 轮）
    if conversation_history:
        recent = conversation_history[-12:]  # 6轮 = 12条消息
        messages.extend(recent)

    messages.append({"role": "user", "content": player_input})

    try:
        response = await client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=messages,
            temperature=0.85,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[K 对话生成失败] {e}")
        return "（K 沉默地盯着你，指尖轻轻敲击桌面。）\n……你在浪费我的时间。"