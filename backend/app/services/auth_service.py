"""
鉴权工具：SHA-256 预哈希 + bcrypt 散列 + JWT 签发与校验。

为什么要预哈希：
  bcrypt 协议硬上限就是 72 字节，而中文/Emoji 在 UTF-8 下每字符 3~4 字节，
  很容易越界；截断又会丢信息、导致不同密码碰撞。
  业界（Dropbox / Django 等）的标准做法是在 bcrypt 前先做一次 SHA-256，
  把任意长度的密码压成固定 64 字节十六进制串（纯 ASCII），
  这样既永远不超 72 字节，也不损失信息、不产生碰撞。

为什么直接用 bcrypt 包而不是 passlib：
  passlib 1.7.x 自启动会用 72 字节样本做自检，而 bcrypt ≥ 5.0 改为严格
  拒绝 72+ 字节输入，导致 passlib 初始化即抛 ValueError，整个鉴权路径
  被 500 炸穿。passlib 项目已长期停更，官方推荐直接用 bcrypt。
"""
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _prehash(raw: str) -> bytes:
    """
    SHA-256 预哈希：
      任意明文 → UTF-8 bytes → sha256 → 64 位十六进制字符串（纯 ASCII，64 字节）。
    输出固定长度且永远在 bcrypt 的 72 字节上限之下。
    bcrypt.hashpw / checkpw 接受 bytes，这里直接返回 ASCII bytes。
    """
    if raw is None:
        raw = ""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest().encode("ascii")


def hash_password(raw: str) -> str:
    """注册 / 改密：先 SHA-256 预哈希，再交给 bcrypt。返回 utf-8 字符串，便于入库。"""
    hashed = bcrypt.hashpw(_prehash(raw), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    """登录校验：同样走一遍预哈希，保持和 hash_password 对称。"""
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(_prehash(raw), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # 哈希串损坏等极端情况，直接判失败，不让接口 500
        return False


def create_access_token(subject: str, extra: dict | None = None) -> str:
    """签发 JWT。sub = username。"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """FastAPI 依赖：解析 Bearer token，返回当前用户。失败返回 401。"""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="凭证无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            raise credentials_error
    except JWTError:
        raise credentials_error

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_error
    return user
