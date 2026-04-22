from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.player import PlayerSession
from app.schemas.player import PlayerCreate, PlayerStatus
from app.schemas.game import GameStageResponse, PlayerChoice, ChoiceResult
from app.services.game_engine import GameEngine

router = APIRouter(prefix="/api/game", tags=["游戏核心"])


@router.post("/start", response_model=GameStageResponse, summary="开始新游戏")
async def start_game(
    player: PlayerCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建新的游戏会话，返回第一阶段数据"""
    engine = GameEngine(db)
    return await engine.start_new_game(player.player_name)


@router.post("/choose", response_model=ChoiceResult, summary="提交玩家选择")
async def make_choice(
    choice: PlayerChoice,
    db: AsyncSession = Depends(get_db),
):
    """处理玩家的选择，返回K的回应和状态变化"""
    engine = GameEngine(db)
    return await engine.process_choice(choice.session_id, choice.choice)


@router.get("/status/{session_id}", response_model=PlayerStatus, summary="获取玩家状态")
async def get_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取当前游戏会话的玩家状态"""
    result = await db.execute(
        select(PlayerSession).where(PlayerSession.id == session_id)
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="游戏会话不存在")
    return player


@router.get("/stage/{session_id}", response_model=GameStageResponse, summary="获取当前阶段")
async def get_current_stage(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取当前阶段的剧情数据"""
    engine = GameEngine(db)
    return await engine.get_current_stage(session_id)