"""
账号体系：User —— 与 UserProfile（人格档案）、PlayerSession（游戏会话）解耦。
通过 username 去关联两个业务表。

关联：
  - game_state ：1:1，关卡 / 防骗得分（GameState）
  - medals     ：1:N，已解锁勋章（UserMedal）
  - posts      ：1:N，深渊树洞帖子（Post）
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
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

    # ===== 关系（lazy 字符串引用，避免循环 import） =====
    game_state = relationship(
        "GameState",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    medals = relationship(
        "UserMedal",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    posts = relationship(
        "Post",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.username} | lv.{self.current_level} | score:{self.total_score}>"
