"""
反诈人格档案 —— 评估结果持久化
与 PlayerSession（游戏会话）解耦，按 player_name 唯一索引。
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    player_name: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, default="无名者"
    )

    # ===== 人格评估核心字段 =====
    personality_type: Mapped[str | None] = mapped_column(
        String(40), nullable=True,
        comment="人格类型，如 '赛博送钱观音'"
    )
    trait_analysis: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="性格分析文本（DeepSeek 生成的毒舌幽默评价）"
    )
    precautions: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="针对该人格的防诈注意事项（教育意义部分）"
    )

    # ===== 勋章列表（JSON） =====
    # 结构: [{"id": "vigilant", "name": "识破骗局", "icon": "shield",
    #        "tier": "gold", "unlocked": true, "acquired_at": "..."}]
    medals: Mapped[list] = mapped_column(
        JSON, default=list,
        comment="已获得的勋章列表"
    )

    # 答题原始记录（便于后续复盘/调优）
    last_answers: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    def __repr__(self) -> str:
        return f"<UserProfile {self.player_name} | {self.personality_type or '未评估'}>"
