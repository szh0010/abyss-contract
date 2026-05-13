"""
反诈人格评估服务
- 预置题库（10 道心理测试题）
- DeepSeek 判定人格 → 返回结构化 JSON
- 勋章授予逻辑
"""
import json
from datetime import datetime, timezone
from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
)


# ============================================================
# 题库：10 道心理测试题，每题 4 个选项
# 选项设计覆盖：贪婪度 / 恐惧感 / 从众心理 / 信任阈值 / 情感依赖
# ============================================================
QUESTION_BANK = [
    {
        "id": "q1",
        "dimension": "贪婪",
        "text": "刷到'日赚 500 元，一部手机即可操作'的兼职广告，你的第一反应是？",
        "options": [
            {"key": "A", "text": "直接拉黑，天上不会掉馅饼", "score": {"greed": 0}},
            {"key": "B", "text": "点进去看看，了解下是什么项目", "score": {"greed": 2}},
            {"key": "C", "text": "先加客服问问，感觉还能试试", "score": {"greed": 4}},
            {"key": "D", "text": "好机会！反正只要一部手机", "score": {"greed": 6}},
        ],
    },
    {
        "id": "q2",
        "dimension": "恐惧",
        "text": "接到陌生来电，对方自称'公安局'说你涉嫌洗钱，你会？",
        "options": [
            {"key": "A", "text": "立即挂断并拨打 110 核实", "score": {"fear": 0}},
            {"key": "B", "text": "先听完，看他说什么", "score": {"fear": 2}},
            {"key": "C", "text": "紧张，按对方指引操作手机", "score": {"fear": 5}},
            {"key": "D", "text": "完蛋了，赶紧配合调查自证清白", "score": {"fear": 7}},
        ],
    },
    {
        "id": "q3",
        "dimension": "情感",
        "text": "网上认识的对象突然说自己家人重病急需用钱，你会？",
        "options": [
            {"key": "A", "text": "真爱和钱无关，先视频确认身份", "score": {"love": 0}},
            {"key": "B", "text": "借个小数目表达心意", "score": {"love": 3}},
            {"key": "C", "text": "为了 TA 愿意承担一些", "score": {"love": 5}},
            {"key": "D", "text": "爱就是要付出，砸锅卖铁也要救", "score": {"love": 8}},
        ],
    },
    {
        "id": "q4",
        "dimension": "贪婪",
        "text": "同学推荐你一个'稳赚不赔'的投资群，初期真的赚到了 500 元，接下来？",
        "options": [
            {"key": "A", "text": "立即提现退群，这是杀猪盘前兆", "score": {"greed": 0}},
            {"key": "B", "text": "再观察一段时间看看", "score": {"greed": 3}},
            {"key": "C", "text": "加大投入，毕竟真赚钱了", "score": {"greed": 6}},
            {"key": "D", "text": "全仓 all in，错过就亏了", "score": {"greed": 10}},
        ],
    },
    {
        "id": "q5",
        "dimension": "从众",
        "text": "班级群里有人说某 App 内部渠道能买到半价苹果手机，已经 5 个人下单了，你？",
        "options": [
            {"key": "A", "text": "明显是诈骗，提醒其他同学别上当", "score": {"crowd": 0}},
            {"key": "B", "text": "问问先下单的同学靠不靠谱", "score": {"crowd": 3}},
            {"key": "C", "text": "既然有人下单了，我也来一台", "score": {"crowd": 6}},
            {"key": "D", "text": "抢！去晚了就没了", "score": {"crowd": 8}},
        ],
    },
    {
        "id": "q6",
        "dimension": "信任",
        "text": "陌生人发链接说'帮我点一下注销校园贷账户，不然影响征信'，你？",
        "options": [
            {"key": "A", "text": "根本不存在这种注销服务，直接拉黑", "score": {"trust": 0}},
            {"key": "B", "text": "问他要官方客服电话", "score": {"trust": 2}},
            {"key": "C", "text": "点进去看看是什么页面", "score": {"trust": 5}},
            {"key": "D", "text": "征信很重要，按他说的做", "score": {"trust": 8}},
        ],
    },
    {
        "id": "q7",
        "dimension": "恐惧",
        "text": "收到短信'您的账户将于 24 小时内冻结'，附带一个验证链接，你？",
        "options": [
            {"key": "A", "text": "标准钓鱼短信，直接删除", "score": {"fear": 0}},
            {"key": "B", "text": "打银行官方电话核实", "score": {"fear": 1}},
            {"key": "C", "text": "点进链接看看是什么情况", "score": {"fear": 5}},
            {"key": "D", "text": "赶紧按链接里的指引处理", "score": {"fear": 8}},
        ],
    },
    {
        "id": "q8",
        "dimension": "贪婪",
        "text": "看到短视频'AI 量化交易，月收益 30%，学费 999 元'，你？",
        "options": [
            {"key": "A", "text": "真能月赚 30% 还用收学费？智商税", "score": {"greed": 0}},
            {"key": "B", "text": "查查这个人的资质再说", "score": {"greed": 2}},
            {"key": "C", "text": "999 试试也亏不了多少", "score": {"greed": 5}},
            {"key": "D", "text": "报名！改变命运的机会", "score": {"greed": 8}},
        ],
    },
    {
        "id": "q9",
        "dimension": "信任",
        "text": "'客服'要你开启屏幕共享协助退款，你会？",
        "options": [
            {"key": "A", "text": "立即挂断，这是屏幕共享诈骗", "score": {"trust": 0}},
            {"key": "B", "text": "问清楚为什么需要共享", "score": {"trust": 3}},
            {"key": "C", "text": "开了，反正我没输密码", "score": {"trust": 7}},
            {"key": "D", "text": "按指引操作，退款要紧", "score": {"trust": 10}},
        ],
    },
    {
        "id": "q10",
        "dimension": "情感",
        "text": "你觉得自己被骗的可能性有多大？",
        "options": [
            {"key": "A", "text": "我会保持警惕，但不会百分百不可能", "score": {"love": 0}},
            {"key": "B", "text": "正常情况下应该不会吧", "score": {"love": 2}},
            {"key": "C", "text": "除非对方很高明", "score": {"love": 4}},
            {"key": "D", "text": "我这么聪明，绝对不会被骗", "score": {"love": 7}},
        ],
    },
]


# ============================================================
# DeepSeek 人格判定 Prompt
# ============================================================
PERSONALITY_SYSTEM_PROMPT = """你是一个"反诈人格鉴定官"，专门根据心理测试结果给玩家贴一个略带毒舌但富有警示意义的人格标签。

## 人格库参考（你可以从中选择，也可以创造新的，但风格必须一致）
- "赛博送钱观音"——对一切求助都怀有慈悲心，容易被杀猪盘/情感诈骗击穿
- "懵懂韭菜候补"——对高收益投资毫无抵抗力，典型的投资诈骗受害者候选
- "恐惧傀儡"——一听到公检法/冻结账户就六神无主，冒充公检法诈骗的完美目标
- "从众小绵羊"——看见别人下单就冲动消费，容易被刷单/杀猪盘带偏
- "屏幕共享之友"——把陌生客服当亲妈，共享屏幕一气呵成
- "无敌自信者"——自以为不会被骗，其实最容易被高定制化骗局拿下
- "钢铁防诈战士"——警觉性高、心态稳，反诈满级大佬
- "清醒观察员"——不算顶级但基本功扎实，能识破大多数套路

## 你的任务
根据用户的答题分数维度（贪婪/恐惧/情感/从众/信任），判定一个最贴合的人格类型，并输出结构化 JSON。

## 输出格式（严格 JSON，禁止额外说明、禁止 markdown 代码块）
{
  "personality_name": "赛博送钱观音",
  "humorous_analysis": "用毒舌但不恶意的风格点评这个人的典型反应，大约 80-120 字。要有网感、带梗，但核心是让用户意识到自己的反诈盲区。",
  "educational_warning": "针对这种人格最容易中招的诈骗类型，给出 3 条具体、可操作的防骗建议，用『；』分隔。",
  "suggested_medal": {
    "id": "英文标识，小写下划线",
    "name": "中文勋章名（4-6 字）",
    "icon": "从 shield/star/eye/bolt 四个中选一个",
    "tier": "bronze/silver/gold 之一，根据人格强度选择（钢铁防诈战士=gold，清醒观察员=silver，其余=bronze）"
  }
}

## 重要
- 语气毒舌但不侮辱，像互联网老哥调侃朋友
- 不要使用 emoji
- personality_name 必须是 4-7 个字
- 严禁输出 JSON 之外的任何内容
"""


def compute_score_profile(answers: list[dict]) -> dict:
    """
    根据用户选择聚合各维度得分。
    answers: [{"id": "q1", "selected": "A"}, ...]
    """
    profile = {"greed": 0, "fear": 0, "love": 0, "crowd": 0, "trust": 0}
    q_map = {q["id"]: q for q in QUESTION_BANK}

    for ans in answers:
        q = q_map.get(ans.get("id"))
        if not q:
            continue
        opt = next((o for o in q["options"] if o["key"] == ans.get("selected")), None)
        if not opt:
            continue
        for dim, val in opt["score"].items():
            profile[dim] = profile.get(dim, 0) + val

    return profile


async def get_personality_evaluation(answers: list[dict]) -> dict:
    """
    核心函数：调用 DeepSeek 对用户答案进行人格判定。

    返回结构：
    {
        "personality_name": str,
        "humorous_analysis": str,
        "educational_warning": str,
        "suggested_medal": { id, name, icon, tier }
    }
    """
    score_profile = compute_score_profile(answers)

    # 构造给 LLM 的答题摘要（节省 token）
    q_map = {q["id"]: q for q in QUESTION_BANK}
    summary_lines = []
    for ans in answers:
        q = q_map.get(ans.get("id"))
        if not q:
            continue
        opt = next((o for o in q["options"] if o["key"] == ans.get("selected")), None)
        if not opt:
            continue
        summary_lines.append(
            f"[{q['dimension']}] {q['text']} → 选【{opt['key']}】{opt['text']}"
        )

    user_payload = (
        f"## 答题记录\n" + "\n".join(summary_lines) +
        f"\n\n## 维度聚合分数\n{json.dumps(score_profile, ensure_ascii=False)}"
        f"\n\n请据此判定人格并按格式输出 JSON。"
    )

    try:
        response = await client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": PERSONALITY_SYSTEM_PROMPT},
                {"role": "user", "content": user_payload},
            ],
            temperature=0.85,
            max_tokens=600,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)

        # 字段防御：保底值
        data.setdefault("personality_name", "清醒观察员")
        data.setdefault("humorous_analysis", "你属于基本盘扎实的一类人，日常防诈合格。")
        data.setdefault("educational_warning",
                        "保持警惕；不轻信陌生链接；遇到异常直接拨打 96110。")
        medal = data.get("suggested_medal") or {}
        medal.setdefault("id", "observer")
        medal.setdefault("name", "清醒哨兵")
        medal.setdefault("icon", "eye")
        medal.setdefault("tier", "silver")
        data["suggested_medal"] = medal
        data["_score_profile"] = score_profile
        return data

    except Exception as e:
        print(f"[人格评估LLM调用失败] {e}")
        # 降级方案：用分数规则本地判定，保证接口始终可用
        return _fallback_evaluation(score_profile)


def _fallback_evaluation(profile: dict) -> dict:
    """LLM 失败时的规则兜底"""
    total = sum(profile.values())
    top_dim = max(profile, key=profile.get) if profile else "greed"

    if total < 15:
        return {
            "personality_name": "钢铁防诈战士",
            "humorous_analysis": "警觉性拉满、逻辑在线，骗子看到你都想绕道走。继续保持这份清醒。",
            "educational_warning": "帮助身边亲友识别骗局；关注反诈中心发布的新手法；遇到新型诈骗及时举报。",
            "suggested_medal": {"id": "iron_guardian", "name": "钢铁哨兵", "icon": "shield", "tier": "gold"},
            "_score_profile": profile,
        }

    dim_map = {
        "greed": ("懵懂韭菜候补", "high_yield_trap",
                  "对'高收益稳赚不赔'几乎零抵抗，典型的投资诈骗受害者候选。",
                  "任何承诺稳赚的都是骗局；投资前查证监会官网；高回报=高风险，常识守门。"),
        "fear": ("恐惧傀儡", "composure_shield",
                 "一听到公检法/账户冻结就大脑宕机，冒充公检法骗局的完美目标。",
                 "公检法不会电话办案；不存在安全账户；先挂断再拨 110 核实。"),
        "love": ("赛博送钱观音", "heart_guard",
                 "慈悲心爆棚，网恋对象说缺钱能信个七八分，杀猪盘直呼内行。",
                 "网恋对象提钱必防；视频核实真实身份；跟身边人确认再做决定。"),
        "crowd": ("从众小绵羊", "independent_mind",
                  "别人下单你下单，别人投资你跟上，缺少独立判断。",
                  "不盲信群聊'已下单'；自己查证官方渠道；冷静 24 小时再决定。"),
        "trust": ("屏幕共享之友", "privacy_ward",
                  "对陌生'客服'过于信任，屏幕共享一气呵成。",
                  "绝不开启屏幕共享；不告诉任何人验证码；退款走官方原路径。"),
    }
    name, mid, analysis, warning = dim_map.get(top_dim, dim_map["greed"])
    return {
        "personality_name": name,
        "humorous_analysis": analysis,
        "educational_warning": warning,
        "suggested_medal": {"id": mid, "name": name[:4], "icon": "bolt", "tier": "bronze"},
        "_score_profile": profile,
    }


def merge_medal(existing: list, new_medal: dict) -> list:
    """把新勋章合并进已有列表（去重 by id，保留 unlocked=True）"""
    medals = list(existing or [])
    acquired_at = datetime.now(timezone.utc).isoformat()

    found = False
    for m in medals:
        if m.get("id") == new_medal.get("id"):
            m["unlocked"] = True
            m["acquired_at"] = acquired_at
            found = True
            break

    if not found:
        medals.append({
            **new_medal,
            "unlocked": True,
            "acquired_at": acquired_at,
        })
    return medals
