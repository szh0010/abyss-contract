"""
当前登录用户档案：关卡进度 / 防骗得分 / 已解锁勋章。
为前端「主大厅」与「AbyssGame」提供冷启动 / 跨设备同步。
"""
from typing import Annotated, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.game_state import GameState
from app.models.user_medal import UserMedal
from app.services.auth_service import get_current_user


router = APIRouter(prefix="/api/user", tags=["用户档案"])


class MedalOut(BaseModel):
    id: str
    name: str
    icon: str
    tier: str
    unlocked_at: str


class ProfileResponse(BaseModel):
    id: str
    username: str
    current_stage: int
    score: int
    medals: List[MedalOut]


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="获取当前用户的关卡进度 / 得分 / 勋章",
)
async def get_profile(
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    gs = await db.get(GameState, current.id)
    current_stage = gs.current_stage if gs else 1
    score = gs.score if gs else 0

    rows = await db.execute(
        select(UserMedal)
        .where(UserMedal.user_id == current.id)
        .order_by(UserMedal.unlocked_at.asc())
    )
    medals = [
        MedalOut(
            id=m.medal_id,
            name=m.name,
            icon=m.icon,
            tier=m.tier,
            unlocked_at=m.unlocked_at.isoformat(),
        )
        for m in rows.scalars().all()
    ]

    return ProfileResponse(
        id=current.id,
        username=current.username,
        current_stage=current_stage,
        score=score,
        medals=medals,
    )
