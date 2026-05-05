import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.game_stage import GameStage


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
    debt: Mapped[int] = mapped_column(Integer, default=0, comment="负债金额（套路贷阶段）")
    greed_value: Mapped[int] = mapped_column(Integer, default=0)
    current_stage: Mapped[int] = mapped_column(Integer, default=1)
    mental_state: Mapped[str] = mapped_column(String(20), default="清醒")

    # ===== 状态机字段 =====
    game_stage: Mapped[str] = mapped_column(
        String(20),
        default=GameStage.BAIT.value,
        comment="当前游戏阶段"
    )

    # ===== 阶段进度追踪 =====
    bait_wins: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="养猪阶段连赢次数（达到3次触发stage_hook）"
    )

    hook_rounds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="高端局已玩局数（用于控制K的输赢策略）"
    )

    trap_triggered: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否已触发杀猪逻辑"
    )

    # ===== 套路贷相关 =====
    loan_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="借款总额（套路贷阶段）"
    )

    loan_accepted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否接受借款协议"
    )

    # ===== 终局锁定 =====
    account_frozen: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="账户是否被冻结（终局）"
    )

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
