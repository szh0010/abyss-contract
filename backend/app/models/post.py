"""
深渊树洞 · 帖子表：一对多 —— 一个用户可发多个帖子。
- image_path 留作后续上传扩展（当前可为空）
- likes 简单计数；点赞功能后续可加
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    # 冗余的作者展示名：方便机器人种子帖也能落库（user_id 为 NULL）
    author_name: Mapped[str] = mapped_column(String(50), default="匿名")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    likes: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="posts")

    def __repr__(self) -> str:
        return f"<Post {self.id} by {self.author_name}>"
