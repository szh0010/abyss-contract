import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fastapi.middleware.cors import CORSMiddleware

# 1. 安全读取你的 DeepSeek API Key
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    raise ValueError("请确保在 .env 文件中配置了 DEEPSEEK_API_KEY！")

# 2. 初始化 DeepSeek 客户端 (DeepSeek 完全兼容 OpenAI 的调用格式)
client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

app = FastAPI()

# 允许前端 Vue 跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 定义前端传过来的数据格式
class PlayerInput(BaseModel):
    text: str
    current_debt: int
    current_greed: int

# 4. 核心逻辑 API
@app.post("/api/game/chat")
async def process_game_turn(player_data: PlayerInput):
    player_text = player_data.text
    debt = player_data.current_debt
    greed = player_data.current_greed

    try:
        # 第一步：意图识别 (Agent 分类器)
        intent_prompt = f"""
        请分析玩家的输入，将其归类为以下四种意图之一，并且【只输出这一个英文大写单词，不要有任何其他字符】：
        GAMBLE (同意下注/试图借钱/继续玩)
        REJECT (拒绝/想要离开/认清现实)
        BARGAIN (讲价/质疑规则/拖延时间)
        VIOLENCE (掀桌子/报警/人身攻击)
        
        玩家输入: "{player_text}"
        """
        
        intent_response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": intent_prompt}],
            temperature=0.1 # 温度调低，保证只输出分类单词
        )
        intent = intent_response.choices[0].message.content.strip().upper()

        # 第二步：游戏引擎接管 (死逻辑，AI 改不了)
        if intent == "GAMBLE":
            debt += 50000
            greed += 15
        elif intent == "REJECT":
            debt -= 5000  # 稍微减少一点作为正向反馈
        # BARGAIN 和 VIOLENCE 暂时不改变数值，只推进剧情

        # 第三步：动态台词生成 (扮演代理人 K)
        k_prompt = f"""
        你是地下金融代理人K。说话风格冷酷、狡诈、极具压迫感。
        玩家刚才说："{player_text}"
        你的意图分析器判定他想：{intent}
        系统结算后，他现在的债务是 {debt} 元，贪婪值是 {greed}/100。
        
        请根据他的话语进行精准的嘲讽或反击，自然地引出他现在的债务数字，逼迫他继续深陷。绝不能同意他报警或免除债务。
        """
        
        dialogue_response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": k_prompt}],
            temperature=0.7 # 温度适中，让反派说话更有创造力
        )
        k_reply = dialogue_response.choices[0].message.content.strip()

        # 返回 JSON 给前端 Vue
        return {
            "k_reply": k_reply,
            "new_debt": debt,
            "new_greed": greed,
            "detected_intent": intent
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))