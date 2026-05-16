"""
游戏进度持久化：每个 User 一行（一对一）。
- current_stage：玩家解锁到的关卡序号（1 起步）
- score        ：累计防骗得分（0~100）
- last_updated ：最近一次 /game/submit 的时间
"""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class GameState(Base):
    __tablename__ = "game_states"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    current_stage: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    user = relationship("User", back_populates="game_state", uselist=False)

    def __repr__(self) -> str:
        return f"<GameState u={self.user_id} stage={self.current_stage} score={self.score}>"
