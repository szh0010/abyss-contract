import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ChoiceRecord(Base):
    """玩家选择记录"""
    __tablename__ = "choice_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("player_sessions.id")
    )
    stage_number: Mapped[int] = mapped_column(Integer)

    choice: Mapped[str] = mapped_column(String(10))
    choice_type: Mapped[str] = mapped_column(String(20))
    choice_text: Mapped[str] = mapped_column(String(200))

    debt_before: Mapped[int] = mapped_column(Integer)
    debt_after: Mapped[int] = mapped_column(Integer)
    greed_before: Mapped[int] = mapped_column(Integer)
    greed_after: Mapped[int] = mapped_column(Integer)

    k_response: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default_factory=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Choice @ Stage {self.stage_number} | {self.choice}>"