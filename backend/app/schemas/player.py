from pydantic import BaseModel, Field
from datetime import datetime


class PlayerCreate(BaseModel):
    """创建新游戏会话"""
    player_name: str = Field(default="无名者", max_length=50)


class PlayerStatus(BaseModel):
    """玩家当前状态"""
    id: str
    player_name: str
    debt: int
    greed_value: int
    current_stage: int
    mental_state: str
    is_fallen: bool
    ending_type: str | None
    total_gamble_count: int
    total_refuse_count: int

    class Config:
        from_attributes = True