from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers.game import router as game_router
from app.routers.minigame import router as minigame_router
from app.routers.chat import router as chat_router
from app.routers.assessment import router as assessment_router
from app.routers.auth import router as auth_router
from app.routers.user import router as user_router
from app.routers.forum import router as forum_router


# 上传目录：与 backend/ 同级
UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "uploads"
(UPLOAD_ROOT / "forum").mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("深渊契约 -- 服务器已启动")
    print("API 文档: http://localhost:8000/docs")
    yield
    print("服务器已关闭")


app = FastAPI(
    title="深渊契约 API",
    description="反金融诈骗与反赌博 文字互动游戏后端",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源：用户上传的图片直接对外暴露在 /uploads/...
app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT), name="uploads")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(forum_router)
app.include_router(game_router)
app.include_router(minigame_router)
app.include_router(chat_router)
app.include_router(assessment_router)


@app.get("/", tags=["健康检查"])
async def root():
    return {
        "name": "深渊契约 API",
        "status": "running",
        "message": "你已经站在深渊的边缘了……"
    }