# 反诈王牌 (Abyss Contract)

> > 一款结合 AI 智能研判与反诈教育的互动式全栈 Web 应用。
> **在线体验：** [https://abysscontract.online](https://abysscontract.online)

## ✨ 核心功能与亮点
- 🎭 沉浸式情景模拟 (核心玩法)
    * 玩家扮演负债者，面对 AI 地下金融代理人 K 的多重话术诱惑。
    * 基于用户选择走向不同分支：选择投机/赌博将无情坠入“深渊结局”，选择正规途径报警则触发“新生结局”。
- 🚨 智能一键研判 (AI 辅助分析)
    * 深度接入 DeepSeek 大模型，化身国家级网络安全反诈专家。
    * 支持对可疑话术、钓鱼链接进行毫秒级研判，动态返回高危预警或低风险提示，并联动国家反诈举报中心。
    * 内置系统级“官方白名单特征认知机制”，精准降低模型误报率（False Positive）。
- 🌲 深渊树洞 (经验交流论坛)
    * 支持图文混排的匿名交流社区，采用灵活的表单校验（纯图、纯文均可发布）。
    * 基于 Vue 3 Teleport 实现的全局高清图片预览（Lightbox），完美适配屏幕缩放，解决长列表滚动定位冲突。
- 🏅 用户与成就系统
    * 完整的 JWT 身份认证体系，记录用户的防诈成长值。
    * 通过探索特定剧情分支，可解锁独特的荣誉勋章（如“钢铁防诈战士”等）。

## 技术栈
- 前端 (Frontend): Vue 3 (Composition API) + Vite + Tailwind CSS + Pinia
- 后端 (Backend): Python 3.x + FastAPI + SQLAlchemy + SQLite
- AI 接入: OpenAI SDK (对接 DeepSeek V1 接口，强制 JSON 模式响应)
- 生产部署: Ubuntu Server + Nginx 反向代理 + Uvicorn 后台守护进程 + HTTPS 证书加密

## 快速启动
### 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

### 前端
cd frontend
npm install
npm run dev

## 许可证
MIT License
