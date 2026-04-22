from pydantic import BaseModel, Field


class GameStageResponse(BaseModel):
    """返回给前端的当前阶段数据"""
    session_id: str = ""
    stage_number: int
    stage_title: str
    k_dialogue: str
    option_a: str
    option_b: str
    player_debt: int
    player_greed: int
    player_mental_state: str
    is_game_over: bool = False
    ending_type: str | None = None


class PlayerChoice(BaseModel):
    """玩家提交的选择"""
    session_id: str = Field(..., description="游戏会话ID")
    choice: str = Field(..., pattern="^[AB]$", description="玩家选择：A或B")


class ChoiceResult(BaseModel):
    """选择后的结果反馈"""
    k_response: str
    debt_change: int
    greed_change: int
    new_debt: int
    new_greed: int
    new_mental_state: str
    next_stage: int | None
    is_game_over: bool = False
    ending_type: str | None = None