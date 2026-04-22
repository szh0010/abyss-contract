import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class PlayerSession(Base):
    """玩家游戏会话"""
    __tablename__ = "player_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    player_name: Mapped[str] = mapped_column(String(50), default="无名者")

    # 核心状态
    debt: Mapped[int] = mapped_column(Integer, default=500000)
    greed_value: Mapped[int] = mapped_column(Integer, default=0)
    current_stage: Mapped[int] = mapped_column(Integer, default=1)
    mental_state: Mapped[str] = mapped_column(String(20), default="清醒")

    # 结局标记
    is_fallen: Mapped[bool] = mapped_column(Boolean, default=False)
    ending_type: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default=None
    )

    # 统计
    total_gamble_count: Mapped[int] = mapped_column(Integer, default=0)
    total_refuse_count: Mapped[int] = mapped_column(Integer, default=0)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    def __repr__(self) -> str:
        return f"<Player {self.player_name} | debt:{self.debt} | greed:{self.greed_value}>"

    @property
    def mental_level(self) -> str:
        if self.greed_value < 25:
            return "清醒"
        elif self.greed_value < 50:
            return "动摇"
        elif self.greed_value < 80:
            return "迷失"
        else:
            return "失控"
