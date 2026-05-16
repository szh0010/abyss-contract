"""
用户勋章解锁记录：一对多 —— 一个用户可解锁多枚勋章。
medal_id 直接落库为字符串 ID（如 'expert'、'iron_guardian'），与前端勋章字典一致。
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class UserMedal(Base):
    __tablename__ = "user_medals"
    __table_args__ = (
        UniqueConstraint("user_id", "medal_id", name="uq_user_medal"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    medal_id: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    icon: Mapped[str] = mapped_column(String(60), default="star")
    tier: Mapped[str] = mapped_column(String(20), default="gold")
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user = relationship("User", back_populates="medals")

    def __repr__(self) -> str:
        return f"<UserMedal u={self.user_id} m={self.medal_id}>"
