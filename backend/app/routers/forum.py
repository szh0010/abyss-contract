"""
深渊树洞 · 论坛 API
- GET    /api/forum/posts                 ：分页拉取最新帖子
- POST   /api/forum/posts                 ：发帖（强制鉴权）
- DELETE /api/forum/posts/{id}            ：仅作者可删
- POST   /api/forum/upload                ：上传配图（multipart/form-data）
- POST   /api/forum/posts/{id}/like       ：切换点赞 / 取消点赞（幂等）
- GET    /api/forum/posts/{id}/comments   ：评论列表
- POST   /api/forum/posts/{id}/comments   ：发表评论

帖子按 created_at 倒序；机器人种子帖 user_id 为 NULL，author_name 直存。
"""
import os
import uuid
from pathlib import Path
from typing import Annotated, List, Optional

from fastapi import (
    APIRouter, Depends, File, Header, HTTPException, Query, UploadFile,
)
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from app.database import get_db
from app.models.user import User
from app.models.post import Post
from app.models.post_interaction import PostLike, PostComment
from app.services.auth_service import decode_token, get_current_user


router = APIRouter(prefix="/api/forum", tags=["深渊树洞"])

# 上传根目录：与 backend/uploads/forum 对齐（main.py 已 mkdir）
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "forum"
ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


# ===== Schemas =====
class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    image_path: Optional[str] = Field(default=None, max_length=255)


class PostOut(BaseModel):
    id: str
    author: str
    avatar: str
    content: str
    image_path: Optional[str] = None
    likes: int
    liked_by_me: bool
    comment_count: int
    time: str
    is_mine: bool
    is_bot: bool


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)


class CommentOut(BaseModel):
    id: str
    author: str
    avatar: str
    content: str
    time: str
    is_mine: bool


class UploadOut(BaseModel):
    image_path: str  # 形如 /uploads/forum/<uuid>.png


class LikeOut(BaseModel):
    liked: bool
    likes: int


# ===== Helpers =====
def _avatar_url(name: str) -> str:
    """统一用 DiceBear 生成卡通头像。"""
    return (
        "https://api.dicebear.com/7.x/notionists/svg"
        f"?seed={name or 'Felix'}&backgroundColor=transparent"
    )


def _format_time(ts) -> str:
    """前端展示用的相对时间。"""
    from datetime import datetime, timezone
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = now - ts
    secs = int(delta.total_seconds())
    if secs < 60:
        return f"{max(secs, 1)} 秒前"
    if secs < 3600:
        return f"{secs // 60} 分钟前"
    if secs < 86400:
        return f"{secs // 3600} 小时前"
    if secs < 86400 * 30:
        return f"{secs // 86400} 天前"
    return ts.strftime("%Y-%m-%d")


async def _try_resolve_current_user_id(
    authorization: Optional[str],
    db: AsyncSession,
) -> Optional[str]:
    """宽松解析当前用户：用于公开但识别 is_mine 的接口。"""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1]
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            return None
        row = await db.execute(select(User.id).where(User.username == username))
        return row.scalar_one_or_none()
    except JWTError:
        return None


async def _aggregate_counts(db: AsyncSession, post_ids: list[str], me_id: Optional[str]):
    """一次性把多帖子的 likes / comment_count / liked_by_me 拉出来，避免 N+1。"""
    if not post_ids:
        return {}, {}, set()

    likes_rows = await db.execute(
        select(PostLike.post_id, func.count(PostLike.id))
        .where(PostLike.post_id.in_(post_ids))
        .group_by(PostLike.post_id)
    )
    likes_map = {pid: cnt for pid, cnt in likes_rows.all()}

    cmt_rows = await db.execute(
        select(PostComment.post_id, func.count(PostComment.id))
        .where(PostComment.post_id.in_(post_ids))
        .group_by(PostComment.post_id)
    )
    cmt_map = {pid: cnt for pid, cnt in cmt_rows.all()}

    liked_by_me: set[str] = set()
    if me_id:
        my_rows = await db.execute(
            select(PostLike.post_id)
            .where(PostLike.user_id == me_id)
            .where(PostLike.post_id.in_(post_ids))
        )
        liked_by_me = {pid for (pid,) in my_rows.all()}

    return likes_map, cmt_map, liked_by_me


# ===== Routes =====
@router.get("/posts", response_model=List[PostOut], summary="拉取帖子列表")
async def list_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[Optional[str], Header()] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    me_id = await _try_resolve_current_user_id(authorization, db)

    rows = await db.execute(
        select(Post).order_by(desc(Post.created_at)).offset(offset).limit(limit)
    )
    posts = rows.scalars().all()

    likes_map, cmt_map, liked_by_me = await _aggregate_counts(
        db, [p.id for p in posts], me_id,
    )

    return [
        PostOut(
            id=p.id,
            author=p.author_name,
            avatar=_avatar_url(p.author_name),
            content=p.content,
            image_path=p.image_path,
            likes=likes_map.get(p.id, 0),
            liked_by_me=p.id in liked_by_me,
            comment_count=cmt_map.get(p.id, 0),
            time=_format_time(p.created_at),
            is_mine=(p.user_id is not None and p.user_id == me_id),
            is_bot=(p.user_id is None),
        )
        for p in posts
    ]


@router.post(
    "/posts",
    response_model=PostOut,
    status_code=201,
    summary="发布新帖子",
)
async def create_post(
    body: PostCreate,
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    post = Post(
        user_id=current.id,
        author_name=current.username,
        content=body.content,
        image_path=body.image_path,
    )
    db.add(post)
    await db.flush()
    await db.refresh(post)

    return PostOut(
        id=post.id,
        author=post.author_name,
        avatar=_avatar_url(post.author_name),
        content=post.content,
        image_path=post.image_path,
        likes=0,
        liked_by_me=False,
        comment_count=0,
        time=_format_time(post.created_at),
        is_mine=True,
        is_bot=False,
    )


@router.delete("/posts/{post_id}", status_code=204, summary="删除自己的帖子")
async def delete_post(
    post_id: str,
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    if post.user_id != current.id:
        raise HTTPException(status_code=403, detail="只能删除自己发布的帖子")
    await db.delete(post)
    return None


# ===== 图片上传 =====
@router.post("/upload", response_model=UploadOut, summary="上传配图（5MB 内）")
async def upload_image(
    file: Annotated[UploadFile, File(description="图片文件")],
    current: Annotated[User, Depends(get_current_user)],
):
    """
    保存到 backend/uploads/forum/<uuid><ext>，返回可直接挂在 <img :src> 上的路径。
    校验：扩展名白名单 + 体积上限。失败一律 4xx，不让前端拿到 500。
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise HTTPException(status_code=400, detail="仅支持 png/jpg/jpeg/gif/webp")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    target = UPLOAD_DIR / name

    # 流式落盘 + 体积守门
    written = 0
    try:
        with target.open("wb") as out:
            while True:
                chunk = await file.read(64 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_IMAGE_BYTES:
                    out.close()
                    target.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="图片大小不得超过 5MB")
                out.write(chunk)
    except HTTPException:
        raise
    except Exception:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="上传失败，请重试")
    finally:
        await file.close()

    return UploadOut(image_path=f"/uploads/forum/{name}")


# ===== 点赞（切换式幂等） =====
@router.post("/posts/{post_id}/like", response_model=LikeOut, summary="点赞 / 取消点赞")
async def toggle_like(
    post_id: str,
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")

    existing = await db.execute(
        select(PostLike)
        .where(PostLike.user_id == current.id)
        .where(PostLike.post_id == post_id)
    )
    row = existing.scalar_one_or_none()
    if row is None:
        db.add(PostLike(user_id=current.id, post_id=post_id))
        liked = True
    else:
        await db.delete(row)
        liked = False

    await db.flush()

    cnt_row = await db.execute(
        select(func.count(PostLike.id)).where(PostLike.post_id == post_id)
    )
    return LikeOut(liked=liked, likes=int(cnt_row.scalar_one() or 0))


# ===== 评论 =====
@router.get(
    "/posts/{post_id}/comments",
    response_model=List[CommentOut],
    summary="拉取评论列表",
)
async def list_comments(
    post_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[Optional[str], Header()] = None,
):
    me_id = await _try_resolve_current_user_id(authorization, db)

    rows = await db.execute(
        select(PostComment)
        .where(PostComment.post_id == post_id)
        .order_by(PostComment.created_at.asc())
    )
    comments = rows.scalars().all()

    return [
        CommentOut(
            id=c.id,
            author=c.author_name,
            avatar=_avatar_url(c.author_name),
            content=c.content,
            time=_format_time(c.created_at),
            is_mine=(me_id is not None and c.user_id == me_id),
        )
        for c in comments
    ]


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommentOut,
    status_code=201,
    summary="发表评论",
)
async def create_comment(
    post_id: str,
    body: CommentCreate,
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")

    comment = PostComment(
        post_id=post_id,
        user_id=current.id,
        author_name=current.username,
        content=body.content,
    )
    db.add(comment)
    await db.flush()
    await db.refresh(comment)

    return CommentOut(
        id=comment.id,
        author=comment.author_name,
        avatar=_avatar_url(comment.author_name),
        content=comment.content,
        time=_format_time(comment.created_at),
        is_mine=True,
    )


@router.delete(
    "/comments/{comment_id}",
    status_code=204,
    summary="删除自己的评论",
)
async def delete_comment(
    comment_id: str,
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    严格的所有权校验：只能删除自己发布的评论。
    - 找不到 → 404
    - 不是作者 → 403
    """
    comment = await db.get(PostComment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="评论不存在")
    if comment.user_id != current.id:
        raise HTTPException(status_code=403, detail="只能删除自己发布的评论")

    await db.delete(comment)
    return None
