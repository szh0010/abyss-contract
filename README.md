# 深渊契约 (Abyss Contract)

> 一款反金融诈骗与反赌博主题的网页端文字互动游戏

## 核心玩法
玩家扮演负债者，面对 AI 地下金融代理人 K 的诱惑。
- 选择赌博/投机 -> 必定触发深渊结局
- 选择正规途径/报警 -> 触发新生结局

## 技术栈
- 后端: Python + FastAPI + SQLAlchemy + SQLite
- 前端: Vue 3 (Composition API) + Pinia + Vite
- 通信: RESTful API

## 快速启动
### 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

### 前端
cd frontend
npm install
npm run dev
