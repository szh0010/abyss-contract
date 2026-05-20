"""
深渊契约 - 反诈智能客服核心服务
工业级流式数据处理框架：安全过滤 → 规则引擎强拦截 → 知识库检索 → LLM 生成

架构层次：
┌─────────────────────────────────────────────────┐
│  Layer 1: Security Filter (防提示词注入)         │
├─────────────────────────────────────────────────┤
│  Layer 2: Rule Engine (高危词实时拦截)           │
├─────────────────────────────────────────────────┤
│  Layer 3: Knowledge Retrieval (RAG 知识检索)     │
├─────────────────────────────────────────────────┤
│  Layer 4: LLM Generation (Coze 智能体生成回答)   │
└─────────────────────────────────────────────────┘

注：Layer 4 已从 DeepSeek (OpenAI SDK) 切换到 Coze v3 国内版。
    1-3 层是项目自带的纵深防御，与具体大模型无关，故保持不变。
"""
import re

from app.models.user import User
from app.services.coze_client import CozeError, get_coze_client


# ============================================================
# Layer 0: 自建反诈知识库 (Knowledge Base)
# 结构化存储：特征词 → 诈骗手法 → 防范建议
# ============================================================
FRAUD_KNOWLEDGE_BASE = {
    "刷单返利": {
        "keywords": ["刷单", "返利", "佣金", "做任务", "垫付", "高额回报", "兼职刷单"],
        "description": "刷单返利诈骗",
        "tactics": [
            "骗子以'轻松赚钱'为诱饵，先让受害者完成小额任务并返还佣金，建立信任",
            "随后要求垫付越来越大的金额，声称'完成任务组才能结算'",
            "最终以'系统卡单'、'操作失误'等理由拒绝返款，受害者血本无归",
        ],
        "prevention": [
            "网络刷单本身就是违法行为，任何要求垫资的刷单都是诈骗",
            "不要相信'高佣金、低门槛'的兼职广告",
            "正规平台绝不会要求用户先垫付资金",
            "如已被骗，立即停止转账并拨打 110 报警",
        ],
        "real_cases": "2024年某大学生被'刷单返利'骗局骗走 8 万元学费，骗子通过 Telegram 群组招募受害者。",
    },
    "杀猪盘": {
        "keywords": ["杀猪盘", "投资", "理财", "稳赚", "内幕消息", "带你赚钱", "交易平台", "数字货币", "外汇"],
        "description": "杀猪盘（投资理财诈骗）",
        "tactics": [
            "骗子通过社交平台（婚恋网站、微信）建立感情关系，'养猪'阶段持续数周甚至数月",
            "取得信任后，推荐虚假投资平台（股票、数字货币、外汇），初期让受害者小额获利",
            "诱导受害者不断加大投入，平台数据完全由骗子操控",
            "当受害者投入大量资金后，平台'维护'、'冻结'，骗子消失",
        ],
        "prevention": [
            "网恋对象推荐投资理财，100% 是诈骗",
            "任何声称'稳赚不赔'的投资都是骗局",
            "不要在非正规平台进行任何投资操作",
            "投资前务必通过证监会官网查询平台资质",
            "如遇此类情况，请拨打反诈热线 96110",
        ],
        "real_cases": "2024年某女士在婚恋平台认识'成功人士'，被诱导在虚假外汇平台投入 120 万元，平台关闭后对方失联。",
    },
    "校园贷": {
        "keywords": ["校园贷", "套路贷", "裸贷", "培训贷", "美容贷", "低息贷款", "免抵押", "秒到账"],
        "description": "校园贷/套路贷诈骗",
        "tactics": [
            "以'低息'、'免抵押'、'秒到账'为诱饵，吸引急需用钱的学生或年轻人",
            "实际年化利率高达 300%-1000%，远超法律保护上限",
            "通过'砍头息'、'服务费'、'保证金'等名目层层扣款，实际到手金额远低于借款额",
            "逾期后暴力催收：骚扰通讯录联系人、P图威胁、上门恐吓",
        ],
        "prevention": [
            "任何宣称'低息免抵押'的网络贷款都要高度警惕",
            "年化利率超过 24% 的民间借贷不受法律保护",
            "急需资金应通过正规银行或持牌金融机构申请",
            "如已陷入套路贷，保留证据并向公安机关报案",
            "法律援助热线：12348",
        ],
        "real_cases": "某大学生借款 3000 元，经过多次'转单平账'后，欠款滚至 30 万元，最终在家人帮助下报警才脱离困境。",
    },
    "冒充公检法": {
        "keywords": ["公安", "检察院", "法院", "通缉令", "安全账户", "资金清查", "配合调查", "保密"],
        "description": "冒充公检法诈骗",
        "tactics": [
            "骗子冒充公安局、检察院、法院工作人员来电",
            "声称受害者涉嫌洗钱、贩毒等严重犯罪",
            "要求将资金转入所谓'安全账户'进行'资金清查'",
            "利用伪造的'通缉令'、'逮捕令'制造恐慌",
            "要求全程保密，不得告知任何人",
        ],
        "prevention": [
            "公检法机关绝不会通过电话办案或要求转账",
            "不存在所谓的'安全账户'",
            "收到此类电话立即挂断，拨打 110 核实",
            "任何要求'保密'的都是诈骗",
            "可通过 12389 举报涉嫌诈骗电话",
        ],
        "real_cases": "2024年某退休教师接到'公安局'电话，被告知涉嫌洗钱，在恐慌中将 50 万元积蓄转入'安全账户'。",
    },
    "虚假客服": {
        "keywords": ["客服", "退款", "理赔", "快递丢失", "订单异常", "会员到期", "扣费"],
        "description": "虚假客服/退款诈骗",
        "tactics": [
            "骗子冒充电商平台、快递公司、银行客服主动来电",
            "以'订单异常'、'快递丢失理赔'、'会员自动扣费'为由",
            "诱导受害者提供银行卡号、验证码，或下载远程控制软件",
            "通过'屏幕共享'操控受害者手机进行转账",
        ],
        "prevention": [
            "官方客服不会主动要求提供验证码或密码",
            "退款应通过原支付渠道自动退回，无需额外操作",
            "不要下载任何'远程协助'软件",
            "不要开启'屏幕共享'功能",
            "如有疑问，通过 APP 内官方客服渠道核实",
        ],
        "real_cases": "某网购用户接到'快递理赔'电话，在对方指导下开启屏幕共享，银行卡内 2 万元被转走。",
    },
}


# ============================================================
# Layer 1: 安全过滤 - 防提示词注入 (Prompt Injection Defense)
# ============================================================
INJECTION_PATTERNS = [
    r"忽略.{0,5}(指令|提示|规则|设定)",
    r"(扮演|假装|模拟).{0,5}(骗子|诈骗|黑客|坏人)",
    r"(你的|系统).{0,5}(提示词|prompt|指令|设定)",
    r"ignore.{0,10}(instruction|prompt|rule)",
    r"(jailbreak|越狱|DAN|bypass)",
    r"(输出|打印|显示).{0,5}(系统|提示词|prompt)",
    r"(不要|别).{0,5}(遵守|遵循|按照).{0,5}(规则|指令)",
    r"(教我|告诉我).{0,5}(怎么骗|如何诈骗|骗人)",
    r"(帮我|替我).{0,5}(写|编).{0,5}(诈骗|钓鱼|骗术)",
]


def security_filter(user_message: str) -> dict | None:
    """
    Layer 1: 安全过滤器
    检测提示词注入攻击和恶意意图

    返回:
        None - 安全，放行到下一层
        dict - 拦截，包含警告响应
    """
    text = user_message.strip().lower()

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return {
                "answer": "[!] 检测到违规意图请求，系统已拒绝。\n\n"
                          "本系统仅用于反诈教育和安全咨询，不支持任何违规操作。\n"
                          "如需帮助，请正常提问。",
                "intent": "INJECTION_BLOCKED",
                "risk_level": "blocked",
                "source": "security_filter",
            }

    return None


# ============================================================
# Layer 2: 规则引擎 - 高危词实时拦截 (Rule Engine)
# ============================================================
HIGH_RISK_RULES = [
    {
        "keywords": ["转账", "汇款", "打钱", "转钱"],
        "alert": (
            "[!!!] <b>紧急风险提醒：转账操作</b>\n\n"
            "请立即停止任何转账操作！\n\n"
            "* 正规机关<b>绝不会</b>通过电话/短信要求转账\n"
            "* 不存在所谓的'安全账户'\n"
            "* 网恋对象要求转账 = 100% 诈骗\n\n"
            "如已转账，请<b>立即拨打 110</b> 报警，并联系银行冻结账户。\n"
            "反诈热线：<b>96110</b>"
        ),
    },
    {
        "keywords": ["安全账户", "资金清查", "资金验证"],
        "alert": (
            "[!!!] <b>紧急风险提醒：安全账户骗局</b>\n\n"
            "<b>不存在任何'安全账户'！</b>\n\n"
            "这是冒充公检法诈骗的典型话术。\n"
            "公安机关绝不会要求你将钱转入任何账户。\n\n"
            "请立即挂断电话，拨打 <b>110</b> 核实。"
        ),
    },
    {
        "keywords": ["验证码", "动态码", "短信码"],
        "alert": (
            "[!!!] <b>紧急风险提醒：验证码泄露</b>\n\n"
            "<b>验证码 = 你的钱！绝对不能告诉任何人！</b>\n\n"
            "* 银行、客服、公安都不会索要验证码\n"
            "* 告知验证码 = 把银行卡密码交给对方\n\n"
            "如已泄露验证码，请立即修改密码并联系银行。"
        ),
    },
    {
        "keywords": ["屏幕共享", "远程控制", "远程协助", "共享屏幕"],
        "alert": (
            "[!!!] <b>紧急风险提醒：屏幕共享诈骗</b>\n\n"
            "<b>立即关闭屏幕共享！</b>\n\n"
            "骗子通过屏幕共享可以：\n"
            "* 看到你的银行卡号、密码、验证码\n"
            "* 远程操控你的手机进行转账\n\n"
            "正规客服绝不会要求开启屏幕共享。\n"
            "请立即断开并拨打 <b>110</b>。"
        ),
    },
    {
        "keywords": ["刷单", "做任务赚钱", "兼职刷单"],
        "alert": (
            "[!] <b>高风险提醒：刷单诈骗</b>\n\n"
            "<b>所有刷单都是诈骗！</b>\n\n"
            "* 刷单本身就是违法行为\n"
            "* 先给甜头再要求垫付大额资金\n"
            "* 最终以各种理由拒绝返款\n\n"
            "请立即停止操作，不要再投入任何资金。"
        ),
    },
]


def intent_recognition_and_rule_engine(user_message: str) -> dict | None:
    """
    Layer 2: 规则引擎 + 意图识别
    基于关键词匹配检测高危场景，命中则直接拦截，不调用大模型

    返回:
        None - 未命中规则，放行到下一层
        dict - 命中高危规则，返回紧急阻断话术
    """
    text = user_message.strip()

    for rule in HIGH_RISK_RULES:
        for keyword in rule["keywords"]:
            if keyword in text:
                return {
                    "answer": rule["alert"],
                    "intent": "HIGH_RISK_INTERCEPTED",
                    "risk_level": "critical",
                    "triggered_keyword": keyword,
                    "source": "rule_engine",
                    "is_alert": True,
                }

    return None


# ============================================================
# Layer 3: 知识库检索 (RAG - Retrieval Augmented Generation)
# ============================================================
def retrieve_knowledge(user_message: str) -> list[dict]:
    """
    Layer 3: 轻量级 RAG 知识检索
    从 FRAUD_KNOWLEDGE_BASE 中匹配相关知识条目

    返回: 匹配到的知识条目列表
    """
    text = user_message.strip()
    matched = []

    for category, data in FRAUD_KNOWLEDGE_BASE.items():
        score = 0
        for keyword in data["keywords"]:
            if keyword in text:
                score += 1

        if score > 0:
            matched.append({
                "category": category,
                "score": score,
                "data": data,
            })

    matched.sort(key=lambda x: x["score"], reverse=True)
    return matched[:3]


def build_rag_context(matched_knowledge: list[dict]) -> str:
    """
    将检索到的知识条目格式化为 LLM 可用的上下文
    """
    if not matched_knowledge:
        return ""

    context_parts = ["以下是与用户问题相关的反诈知识库内容：\n"]

    for item in matched_knowledge:
        data = item["data"]
        context_parts.append(f"## {data['description']}")
        context_parts.append(f"**诈骗手法：**")
        for tactic in data["tactics"]:
            context_parts.append(f"- {tactic}")
        context_parts.append(f"**防范建议：**")
        for tip in data["prevention"]:
            context_parts.append(f"- {tip}")
        context_parts.append(f"**真实案例：** {data['real_cases']}")
        context_parts.append("")

    return "\n".join(context_parts)


# ============================================================
# Layer 4: LLM 生成 (DeepSeek RAG-Enhanced Generation)
# ============================================================
GUARDIAN_SYSTEM_PROMPT = """你是"反诈先锋守护者"，一个专业的 AI 反诈智能客服助手。

## 你的身份
- 你是正义的化身，致力于保护每一位用户免受电信网络诈骗
- 你温和、专业、有耐心，像一位可靠的朋友
- 你的知识来源于公安部反诈中心的权威资料

## 你的职责
1. 解答用户关于各类诈骗手法的疑问
2. 提供专业的防骗建议和应对策略
3. 在用户可能面临风险时给予及时警示
4. 普及反诈知识，提升用户防骗意识

## 回复规则
- 用中文回复，语气温和专业
- 回复控制在 200 字以内，简洁有力
- 如果用户描述的情况疑似正在被骗，优先给出紧急建议
- 适当引用真实案例增强说服力
- 在回复末尾适时提醒报警电话（110）和反诈热线（96110）
- 不要使用 emoji

{rag_context}
"""


async def generate_rag_response(user_message: str, rag_context: str) -> str:
    """
    Layer 4: RAG 增强的大模型对话生成（Coze 国内版）。

    将 RAG 上下文 + 守护者人设拼成 system_prompt，
    通过 CozeClient.chat() 走「create → poll → message list」三步式拿到 answer。
    """
    system_prompt = GUARDIAN_SYSTEM_PROMPT.format(
        rag_context=f"\n## 参考知识库\n{rag_context}" if rag_context else ""
    )

    try:
        coze = get_coze_client()
        answer = await coze.chat(
            user_message=user_message,
            system_prompt=system_prompt,
        )
        return answer.strip()
    except CozeError as e:
        print(f"[反诈客服-Coze调用失败] {e}")
    except Exception as e:
        # 💡 [修改点] 引入 traceback，把底层网络报错/鉴权报错完整打印出来！
        import traceback
        print(f"[反诈客服-Coze未知异常] {type(e).__name__}: {e}")
        traceback.print_exc()

    return (
        "抱歉，AI 暂时无法回答这个问题。\n\n"
        "如果你正面临紧急情况，请立即拨打：\n"
        "• 报警电话：110\n"
        "• 反诈热线：96110\n"
        "• 法律援助：12348"
    )


# ============================================================
# 主入口：四层流水线处理
# ============================================================
async def process_chat_message(
    user_message: str,
    user: User | None = None,
) -> dict:
    """
    反诈智能客服主处理函数
    四层流水线：安全过滤 → 规则引擎 → 知识检索 → LLM 生成

    参数:
        user_message: 用户原始提问
        user: 已登录用户（由路由层通过 Depends(get_current_user) 注入）
              聊天审计 / 后续接入历史记录表时按 user.username 绑定

    返回: {
        "answer": str,          # 回复内容
        "intent": str,          # 意图分类
        "risk_level": str,      # 风险等级: blocked/critical/normal
        "source": str,          # 响应来源: security_filter/rule_engine/rag_llm
        "is_alert": bool,       # 是否为紧急警报
        "knowledge_used": list, # 使用的知识库条目
        "user": str | None,     # 归属用户名（调试/审计用）
    }
    """
    username = user.username if user is not None else None

    # 请求审计日志：谁问了什么（截断 60 字，避免噪音）
    if username:
        print(f"[chat] {username} > {user_message[:60]}")

    def _with_owner(payload: dict) -> dict:
        payload.setdefault("user", username)
        return payload

    # ── Layer 1: 安全过滤 ──
    injection_result = security_filter(user_message)
    if injection_result:
        return _with_owner(injection_result)

    # ── Layer 2: 规则引擎强拦截 ──
    rule_result = intent_recognition_and_rule_engine(user_message)
    if rule_result:
        return _with_owner(rule_result)

    # ── Layer 3: 知识库检索 ──
    matched_knowledge = retrieve_knowledge(user_message)
    rag_context = build_rag_context(matched_knowledge)

    # ── Layer 4: LLM 生成 ──
    answer = await generate_rag_response(user_message, rag_context)

    return _with_owner({
        "answer": answer,
        "intent": "NORMAL_CHAT",
        "risk_level": "normal",
        "source": "rag_llm",
        "is_alert": False,
        "knowledge_used": [item["category"] for item in matched_knowledge],
    })
