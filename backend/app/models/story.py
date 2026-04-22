import uuid
from sqlalchemy import String, Integer, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class StoryStage(Base):
    """剧情阶段定义"""
    __tablename__ = "story_stages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    stage_number: Mapped[int] = mapped_column(Integer, unique=True)
    stage_title: Mapped[str] = mapped_column(String(50))

    k_dialogue: Mapped[str] = mapped_column(Text)
    k_dialogue_high_greed: Mapped[str | None] = mapped_column(Text, nullable=True)

    option_a_text: Mapped[str] = mapped_column(String(200))
    option_a_type: Mapped[str] = mapped_column(String(20), default="gamble")
    option_b_text: Mapped[str] = mapped_column(String(200))
    option_b_type: Mapped[str] = mapped_column(String(20), default="refuse")

    debt_change_a: Mapped[int] = mapped_column(Integer, default=0)
    debt_change_b: Mapped[int] = mapped_column(Integer, default=0)
    is_final_stage: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<Stage {self.stage_number}: {self.stage_title}>"