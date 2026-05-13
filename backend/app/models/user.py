"""
账号体系：User —— 与 UserProfile（人格档案）、PlayerSession（游戏会话）解耦。
通过 username 去关联两个业务表。
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)

    current_level: Mapped[int] = mapped_column(
        Integer, default=1, comment="闯关进度（1 = 第 1 关）"
    )
    total_score: Mapped[int] = mapped_column(
        Integer, default=0, comment="累计积分"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    def __repr__(self) -> str:
        return f"<User {self.username} | lv.{self.current_level} | score:{self.total_score}>"
