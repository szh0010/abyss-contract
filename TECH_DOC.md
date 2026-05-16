# 深渊契约 · 技术文档

> 截止 2026-05-16 · 全栈快照

一个反金融诈骗 + 反赌博主题的 Web 应用。前期是带有金融诈骗代理人 K 的文字互动（保留为兼容代码），现阶段主玩法已重构为「反诈作战大厅 · 关卡制 + 勋章墙 + 深渊树洞论坛」。

---

## 目录

1. [总体架构](#1-总体架构)
2. [技术栈与运行环境](#2-技术栈与运行环境)
3. [本地启动 / 部署](#3-本地启动--部署)
4. [数据持久化层](#4-数据持久化层)
5. [鉴权与会话](#5-鉴权与会话)
6. [REST API 全集](#6-rest-api-全集)
7. [前端架构](#7-前端架构)
8. [核心交互流程](#8-核心交互流程)
9. [合规与安全](#9-合规与安全)
10. [运维要点](#10-运维要点)

---

## 1. 总体架构

```
┌──────────────────────────────────────────────────────────────┐
│                         浏览器（Vue 3 SPA）                    │
│  LoginView · App.vue（主大厅 · liquid-glass）                  │
│  ├ ChatView      —— DeepSeek 反诈客服                          │
│  ├ AbyssGame     —— 反诈作战大厅（关卡制）                      │
│  ├ ForumView     —— 深渊树洞（图文 + 点赞 + 评论）              │
│  └ LinkCheckView —— 可疑链接研判                                │
└────────────┬───────────────────────────┬─────────────────────┘
             │ axios `/api/*`            │ `<img :src="/uploads/...">`
             ▼                           ▼
┌──────────────────────────────────────────────────────────────┐
│                       FastAPI（uvicorn）                       │
│  Routers：auth / user / forum / game / minigame / chat /      │
│           assessment                                          │
│  Services：auth_service · llm_service · personality_service · │
│            game_engine · stage_machine · ai_decision          │
│  Static  ：/uploads → backend/uploads                          │
└────────────┬───────────────────────────┬─────────────────────┘
             │ SQLAlchemy 2.x async      │ DeepSeek API
             ▼                           ▼
┌──────────────────────┐         ┌──────────────────────┐
│   SQLite (aiosqlite) │         │  DeepSeek（可选）      │
│  abyss_contract.db   │         │  对话生成 + 意图识别    │
└──────────────────────┘         └──────────────────────┘
```

主大厅 `App.vue` 用一个根 flex column 包住三段布局（登录无壳、游戏全屏、主大厅 + 路由），底部固定一条液态玻璃合规 Footer（ICP / 公安备案）。

---

## 2. 技术栈与运行环境

### 后端
- Python ≥ 3.11（项目实际使用 3.14；`from __future__` 语法不依赖）
- FastAPI ≥ 0.115、uvicorn[standard] ≥ 0.30
- SQLAlchemy 2.x async + aiosqlite ≥ 0.19
- pydantic 2.x、pydantic-settings 2.x
- 鉴权：`bcrypt ≥ 4.0`（**已淘汰 passlib**，原因见 [auth_service.py](backend/app/services/auth_service.py) 头部说明）+ `python-jose[cryptography]`
- LLM：openai ≥ 1.30（DeepSeek 兼容协议）
- 上传：`python-multipart`

### 前端
- Vue 3.4（Composition API + `<script setup>`）
- vue-router 4
- pinia 2（持久化通过组件内 `watch` + `localStorage`，未引第三方插件）
- axios 1.x
- Vite 5（开发代理 `/api` + `/uploads` → `127.0.0.1:8000`）
- 不使用 Tailwind/UnoCSS，所有样式手写 scoped CSS（液态玻璃 + 弹簧曲线 `cubic-bezier(0.25, 1.5, 0.5, 1)`）

### 运行平台
- 当前部署：Windows 11 + 本地 SQLite（开发态）
- 生产可平迁至 Linux + PostgreSQL，仅需改 `DATABASE_URL`

---

## 3. 本地启动 / 部署

### 后端
```bash
cd backend
pip install -r requirements.txt
# 灌入冷启动论坛种子（4 条反诈机器人帖子，幂等）
python -m app.seed_forum
# 启动
uvicorn app.main:app --reload
```
启动后：
- API 入口：`http://127.0.0.1:8000`
- Swagger 文档：`http://127.0.0.1:8000/docs`
- 上传根：`http://127.0.0.1:8000/uploads/forum/...`

### 前端
```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```
Vite 已代理 `/api` 与 `/uploads` 到后端，无需 CORS 折腾。

### 配置（可选）`backend/.env`
| Key | 默认 | 说明 |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./abyss_contract.db` | DB DSN |
| `JWT_SECRET_KEY` | `abyss-jwt-change-me-in-production` | **生产必改** |
| `JWT_EXPIRE_MINUTES` | 10080 | JWT 有效期（7 天） |
| `DEEPSEEK_API_KEY` |  | 留空时 LLM 回退到本地占位文案 |
| `DEEPSEEK_MODEL` | `deepseek-chat` |  |
| `APP_DEBUG` | true | 控制 SQL echo |

---

## 4. 数据持久化层

### 4.1 ER 总览

```
       ┌──────────┐
       │  users   │
       └────┬─────┘
            │ 1                        1
            ├────────────────────► game_states (1:1)
            │
            │ 1                        N
            ├────────────────────► user_medals
            │
            │ 1                        N
            ├────────────────────► posts ─────► post_likes (N:N)
            │                          └─────► post_comments (1:N)
            │
            │ 兼容旧表：player_sessions / story_stages / choice_records / user_profiles
```

### 4.2 表清单

| 表 | 文件 | 关键字段 | 说明 |
|---|---|---|---|
| `users` | [models/user.py](backend/app/models/user.py) | `id (UUID)` · `username unique` · `hashed_password` | bcrypt 哈希前先 SHA-256 预压（防 72 字节截断） |
| `game_states` | [models/game_state.py](backend/app/models/game_state.py) | `user_id PK/FK` · `current_stage` · `score` | 1:1，跨登录持久化进度 |
| `user_medals` | [models/user_medal.py](backend/app/models/user_medal.py) | `(user_id, medal_id)` 唯一 · `name/icon/tier` | 1:N，幂等解锁 |
| `posts` | [models/post.py](backend/app/models/post.py) | `user_id` 可空 · `author_name` · `content/image_path/likes` | 机器人种子帖 `user_id IS NULL` |
| `post_likes` | [models/post_interaction.py](backend/app/models/post_interaction.py) | `(user_id, post_id)` 唯一 | 切换式幂等点赞 |
| `post_comments` | 同上 | `post_id/user_id/content` | 1:N，按时间升序 |
| `user_profiles` | [models/user_profile.py](backend/app/models/user_profile.py) | `personality_type` · `medals(JSON)` · `last_answers(JSON)` | 反诈人格档案（独立于游戏勋章） |
| `player_sessions` 等 | 老业务表 | — | 旧版赌牌玩法残留，暂不使用 |

集中入口：[models/all_models.py](backend/app/models/all_models.py) + [models/__init__.py](backend/app/models/__init__.py)。`init_db()`(`Base.metadata.create_all`) 启动时自动建表。

### 4.3 冷启动种子

[seed_forum.py](backend/app/seed_forum.py)：4 条反诈机器人帖（校园贷、冒充公检法、亲属求助、新生季），按 `(author_name, content[:60])` 幂等。
```bash
python -m app.seed_forum            # 幂等
python -m app.seed_forum --reset    # 清掉 user_id IS NULL 的帖子再灌
```

---

## 5. 鉴权与会话

### 流程
1. 注册 / 登录 → `POST /api/auth/{register,login}` → 返回 `{access_token, user}`
2. 前端 [services/http.js](frontend/src/services/http.js) 把 `access_token` 写入 `localStorage.abyss_token`，`abyss_user`、`abyss_username` 同步落地
3. 全站 axios 请求自动注入 `Authorization: Bearer <token>`
4. 401 → 自动 `clearAuth()` + 跳 `/login`，并抛全局 toast「密码错误或账号不存在」

### 关键决策
- **bcrypt 直调**：`auth_service` 跳过 passlib（passlib 1.7.x 启动自检会用 72 字节样本，撞上 bcrypt 5.x 的硬上限直接 500）；改成「SHA-256 预哈希 → bcrypt」对称对应。
- **JWT 透传**：sub = username。FastAPI 依赖 `get_current_user` 解析 token + 查库返回 `User`，所有写接口都依赖它。
- **三种鉴权策略**：
  - 强制：`Depends(get_current_user)` —— 写接口
  - 软：`Header()` 自行 `decode_token` —— `GET /forum/posts` 这种「公开但希望识别 is_mine」
  - 无：登录页 / 静态资源

---

## 6. REST API 全集

> 所有路径前缀 `/api`；标 🔒 必须带 Bearer。

### 6.1 鉴权 `/api/auth`
| Method | Path | 说明 |
|---|---|---|
| POST | `/register` | 注册（409 用户名已占用） |
| POST | `/login` | 登录（401 密码错误或账号不存在） |
| GET | `/me` 🔒 | 当前用户 |

### 6.2 用户档案 `/api/user`
| Method | Path | 说明 |
|---|---|---|
| GET | `/profile` 🔒 | 关卡进度 + 防骗得分 + 勋章列表（前端冷启动数据源） |

### 6.3 游戏 `/api/game`
| Method | Path | 说明 |
|---|---|---|
| POST | `/submit` 🔒 | 提交关卡进度 + 解锁勋章（幂等；`score` / `current_stage` 取较大值） |
| POST | `/chat` | 旧版自由对话（DeepSeek 数值引擎，保留兼容） |
| POST | `/start` `/choose` `/status/{id}` `/stage/{id}` | 旧阶段制 API（保留兼容） |

`POST /game/submit` body：
```json
{
  "current_stage": 2,
  "score": 60,
  "unlocked_medals": [
    { "id": "expert", "name": "首席反诈专家", "icon": "🏆", "tier": "gold" }
  ]
}
```

### 6.4 论坛 `/api/forum`
| Method | Path | 说明 |
|---|---|---|
| GET | `/posts` | 列表，可选 token；返回 `liked_by_me / comment_count / is_mine / is_bot` |
| POST | `/posts` 🔒 | 发帖（`content` + 可选 `image_path`） |
| DELETE | `/posts/{id}` 🔒 | 仅作者可删；403 否则 |
| POST | `/upload` 🔒 | `multipart/form-data` 上传图片，5MB 内，返回 `/uploads/forum/<uuid>.ext` |
| POST | `/posts/{id}/like` 🔒 | 切换式幂等，返回 `{ liked, likes }` |
| GET | `/posts/{id}/comments` | 评论列表 |
| POST | `/posts/{id}/comments` 🔒 | 发表评论 |

实现亮点：列表接口用 `func.count + group_by` 一次性聚合 `likes` / `comment_count` / `liked_by_me`，杜绝 N+1。

### 6.5 反诈人格评估 `/api/assess`
- `GET /questions` 🔒：题库（隐藏打分字段）
- `POST /` 🔒：提交答案 → DeepSeek 生成人格报告 + 落 `user_profiles`

### 6.6 反诈客服 / 链接研判 `/api/chat`
- `POST /ask`：自由问答 + 风险等级（`high/mid/low`）

### 6.7 旧版小游戏 `/api/minigame`
保留，但前端入口已下线。

### 6.8 静态
- `GET /uploads/...`：用户上传图片直出（FastAPI `StaticFiles`）

---

## 7. 前端架构

### 7.1 路由表 [router/index.js](frontend/src/router/index.js)

| Path | View | 鉴权 | 备注 |
|---|---|---|---|
| `/login` | `LoginView` | 公开 | `meta.layout: 'blank'` |
| `/` | — | — | 已登录 → `/chat`，否则 `/login` |
| `/chat` | `ChatView` | 必须 | 反诈客服 + AI 研判 |
| `/link-check` | `LinkCheckView` | 必须 | |
| `/forum` | `ForumView` | 必须 | 深渊树洞 |
| `/game` | `AbyssGame` | 必须 | 反诈作战大厅 |
| `/game/intro` | `IntroView` | 必须 | 电影化序章（暗色） |
| `/simulation` `/game/home` `/game/play` | redirect | — | 旧入口兼容，统一汇入 `/game` |
| `/:pathMatch(.*)*` | redirect `/` | — | 兜底 |

两道全局守卫：必须同时持 `token + user` 才放行非公开路由；已登录访问 `/login` 自动回 `/chat`。

### 7.2 视图 / 组件

```
views/
├ LoginView.vue       注册/登录卡片，模式切换有动画
├ ChatView.vue        反诈客服 IM
├ LinkCheckView.vue   单链接研判
├ AbyssGame.vue       关卡列表 / 对话 / 通关结算 三态
├ IntroView.vue       序章（仅在 /game/intro 时启用 game-mode 暗色）
└ ForumView.vue       深渊树洞（图文 + 点赞 + 评论）
components/
├ AssessmentModal.vue 反诈 MBTI 测试弹层
├ GlobalToast.vue     全局 toast（teleport to body）
└ TypeWriter.vue      打字机效果
```

### 7.3 状态管理

- [stores/medalStore.js](frontend/src/stores/medalStore.js)：
  - 本地缓存 `localStorage.abyss_medals::<username>`（按用户名分表）
  - `unlock(medal)` 幂等
  - `hydrateFromServer()` 从 `/api/user/profile` 拉取并按 id 合并
  - `syncWithCurrentUser()` 切账号时重新加载
- 视图本地态（每帖的 `show_comments / draft / liked_by_me` 等）就地放在 `posts` 数组里，不上 store。

### 7.4 服务层

- [services/http.js](frontend/src/services/http.js)：axios 实例 + token 注入 + 401/409/500 全局 toast + JWT `sub` 解析回退
- [services/toast.js](frontend/src/services/toast.js)：`reactive` 队列 + 自动消失，配套 `<GlobalToast />`

### 7.5 设计系统（液态玻璃 + 弹簧）

```css
.liquid-glass            /* 半透白 + blur(24) + 内高光 + 外阴影 */
.liquid-glass-success    /* 蓝调（信任 / 通过） */
.liquid-glass-danger     /* 红调（警告 / 失败 / 骗子气泡） */
.liquid-glass-gold       /* 金调（通关 / 成就） */
.locked-level            /* 灰阶 + 45° 斜纹封印 */
.spring-bounce           /* transition cubic-bezier(0.25, 1.5, 0.5, 1) */
```
配色基底：奶油沙渐变 `#FFFCF5 → #FDF5E6` + 三色极光（`#FFD6A8 / #FFF0C2 / #FFD6DC`）`mix-blend-multiply` 浮动光晕。
头像：DiceBear `notionists` 用 username 作为 seed，千人千面。

---

## 8. 核心交互流程

### 8.1 跨登录持久化
```
登录 → setToken/setUsername
   ↓ App.vue onMounted
medalStore.hydrateFromServer()       ← /api/user/profile
loadProfile()                        ← /api/assess/profile
   ↓ 进入 AbyssGame onMounted
hydrateFromServer()                  ← 还原关卡解锁状态 + 防骗得分
```
通关后：
```
selectOption(success) → totalScore += points
   → 立即 POST /api/game/submit
通关满 100 → triggerClear()
   → medalStore.unlock(🏆首席反诈专家) → 本地 localStorage 立即写
   → POST /api/game/submit (含 unlocked_medals)
```
两条路径都把数据落到 `game_states` 与 `user_medals`，重登 / 换设备直接还原。

### 8.2 论坛发帖 + 互动
```
打开 /forum → GET /api/forum/posts
点 📷 → 隐藏 input 触发 → POST /api/forum/upload (multipart)
        ← image_path: /uploads/forum/<uuid>.png
点「发布分享」 → POST /api/forum/posts { content, image_path }
点 ❤️ → POST /api/forum/posts/{id}/like → 后端切换记录 → 返回 { liked, likes }
点 💬 → 首次懒加载 GET /comments；输入回车 → POST /comments
作者「删除」→ DELETE /api/forum/posts/{id}（403 兜底）
```
机器人种子帖 `user_id IS NULL`，所有用户既不能 `is_mine`、也不能删除。

### 8.3 全局错误提示
axios 响应拦截器统一在 [http.js](frontend/src/services/http.js)：
- 401 → 清 token + 跳登录 + toast「密码错误或账号不存在」
- 409 → toast「用户名已被占用」（或后端 detail）
- 5xx → toast「服务器异常」
- `/auth/login` `/auth/register` 列入静默路径，由 LoginView 自行展示

---

## 9. 合规与安全

- **底部备案**：[App.vue](frontend/src/App.vue) 全站 footer 含「闽 ICP 备 2026016245 号-1」与「闽公网安备 35078402010138 号」，点击外链 `target="_blank" rel="noreferrer"`
- **赌博内容下线**：旧版赌牌玩法 (`GameView/HomeView/LoanDialog/...`) 已物理删除；现役玩法是关卡制反诈推演
- **密码哈希**：SHA-256 → bcrypt（72 字节安全）
- **JWT**：HS256，默认 7 天，密钥从 `JWT_SECRET_KEY` 读取，**生产必改**
- **CORS**：开发态白名单 `localhost:5173 / 3000`；生产应改为同源或显式列前端域名
- **上传安全**：扩展名白名单（`png/jpg/jpeg/gif/webp`）+ 体积上限 5MB + 流式落盘 + 失败清理
- **删除权限**：`DELETE /forum/posts/{id}` 校验 `post.user_id == current.id`，否则 403
- **多账号隔离**：`medalStore` 按 `abyss_username` 分 key，切账号自动重载，避免脏读

---

## 10. 运维要点

### 数据迁移
当前 `init_db` = `Base.metadata.create_all`，仅做「不存在则建表」。增列 / 改列需要：
1. 切到 PostgreSQL（生产）
2. 引入 Alembic（建议路径：`backend/alembic/`）

### 日志
- SQLAlchemy `echo` 受 `APP_DEBUG` 控制；生产环境记得置 false，否则会刷屏
- 登录 / 写接口失败均通过 `HTTPException` 抛 4xx；500 仅在意外异常时返回，前端会兜底 toast

### 性能
- 论坛列表 limit ≤ 200，单次请求 SQL 数稳定为 4（`SELECT posts` + 三个聚合）
- DiceBear 头像走 CDN（外网），如内网部署可换本地静态头像
- 图片上传走静态目录直出，不经过 ASGI worker；并发上传由 OS 文件系统兜底

### 已知技术债
- `models/all_models.py` 与 `models/__init__.py` 都在做集中导出，留一份即可（现状是双份保险）
- 老业务表 `player_sessions / story_stages / choice_records` 仍随 `init_db` 建表，未来可单独迁出
- 上传当前没做用户级配额；机器人种子帖也无法附图（`image_path` 仅在用户端生效）
- 没有点赞 / 评论的反垃圾限频，公网部署前应加 rate limit（uvicorn-rate-limit / nginx）

---

## 附录 A · 目录结构（截选）

```
abyss-contract/
├ backend/
│  ├ uploads/                      # 用户上传（运行时创建）
│  ├ abyss_contract.db             # SQLite
│  ├ requirements.txt
│  └ app/
│     ├ main.py                    # FastAPI 入口 + 静态挂载 + 路由聚合
│     ├ config.py                  # pydantic-settings
│     ├ database.py                # 引擎、会话、init_db
│     ├ seed_forum.py              # 论坛冷启动种子
│     ├ models/                    # User · GameState · UserMedal · Post · PostLike/Comment · UserProfile · 老表
│     ├ routers/                   # auth · user · forum · game · minigame · chat · assessment
│     ├ services/                  # auth_service · llm_service · personality_service · game_engine · stage_machine · ai_decision
│     └ schemas/                   # 旧版 pydantic schemas（assessment / game / player）
└ frontend/
   ├ public/police-icon.png        # 公安联网备案警徽
   ├ vite.config.js                # `/api` `/uploads` 代理
   └ src/
      ├ App.vue                    # 主大厅 + 极光 + 液态玻璃 + 合规 footer
      ├ main.js                    # Pinia + Router 装配
      ├ router/index.js
      ├ views/                     # LoginView / ChatView / LinkCheckView / AbyssGame / ForumView / IntroView
      ├ components/                # AssessmentModal / GlobalToast / TypeWriter
      ├ stores/medalStore.js
      ├ services/http.js · toast.js
      └ assets/styles/dark-theme.css
```

## 附录 B · 关键接口速查

```
登录态
POST   /api/auth/register         注册
POST   /api/auth/login            登录
GET    /api/auth/me               当前用户

用户档案 / 游戏
GET    /api/user/profile          关卡 + 得分 + 勋章
POST   /api/game/submit           写进度 + 幂等解锁勋章

深渊树洞
GET    /api/forum/posts
POST   /api/forum/posts
DELETE /api/forum/posts/{id}
POST   /api/forum/upload          (multipart/form-data)
POST   /api/forum/posts/{id}/like
GET    /api/forum/posts/{id}/comments
POST   /api/forum/posts/{id}/comments

反诈人格
GET    /api/assess/questions
POST   /api/assess

反诈客服
POST   /api/chat/ask
```
