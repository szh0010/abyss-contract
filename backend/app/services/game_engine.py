from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.player import PlayerSession
from app.models.choice import ChoiceRecord
from app.config import settings
from app.data.story_scripts import ALL_STAGES
from app.schemas.game import GameStageResponse, ChoiceResult


ABYSS_ENDING_TEXT = (
    "\n\n"
    "====================\n\n"
    "（你听到远处传来警笛声。不，那不是来救你的。）\n"
    "（你的手机屏幕亮了：您的账户已被冻结）\n"
    "（K 的笑容在黑暗中渐渐消失。）\n"
    "（从始至终，你都只是棋盘上的一枚棋子。）\n\n"
    "【深渊结局：万劫不复】"
)

REBIRTH_ENDING_TEXT = (
    "\n\n"
    "====================\n\n"
    "（K 沉默了很久。）\n"
    "（他站起身，拿起那件黑色外套，头也不回地走了。）\n"
    "（窗外，天亮了。你拨通了法律援助热线。）\n"
    "（这条路会很长，但至少——你还站在路上。）\n\n"
    "【新生结局：破晓之光】"
)


class GameEngine:
    """游戏核心引擎"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_new_game(self, player_name: str) -> GameStageResponse:
        player = PlayerSession(
            player_name=player_name,
            debt=settings.INITIAL_DEBT,
            greed_value=0,
            current_stage=1,
            mental_state="清醒",
        )
        self.db.add(player)
        await self.db.flush()

        stage_data = ALL_STAGES[0]
        return GameStageResponse(
            session_id=player.id,
            stage_number=1,
            stage_title=stage_data["stage_title"],
            k_dialogue=stage_data["k_dialogue"],
            option_a=stage_data["option_a_text"],
            option_b=stage_data["option_b_text"],
            player_debt=player.debt,
            player_greed=player.greed_value,
            player_mental_state=player.mental_state,
        )

    async def process_choice(self, session_id: str, choice: str) -> ChoiceResult:
        result = await self.db.execute(
            select(PlayerSession).where(PlayerSession.id == session_id)
        )
        player = result.scalar_one_or_none()
        if not player:
            raise HTTPException(status_code=404, detail="会话不存在")
        if player.ending_type is not None:
            raise HTTPException(status_code=400, detail="游戏已结束")

        stage_index = player.current_stage - 1
        if stage_index >= len(ALL_STAGES):
            raise HTTPException(status_code=400, detail="已超出剧本范围")

        stage = ALL_STAGES[stage_index]
        debt_before = player.debt
        greed_before = player.greed_value

        if choice == "A":
            player.debt += stage["debt_change_a"]
            player.greed_value = min(
                player.greed_value + settings.GREED_INCREASE_ON_GAMBLE,
                settings.MAX_GREED
            )
            player.total_gamble_count += 1
            k_response = stage.get("k_response_a", "......")
            choice_type = stage["option_a_type"]
            choice_text = stage["option_a_text"]
        else:
            player.debt = max(0, player.debt + stage["debt_change_b"])
            player.greed_value = max(
                player.greed_value - settings.GREED_DECREASE_ON_REFUSE, 0
            )
            player.total_refuse_count += 1
            k_response = stage.get("k_response_b", "......")
            choice_type = stage["option_b_type"]
            choice_text = stage["option_b_text"]

        player.mental_state = player.mental_level

        is_game_over = False
        ending = None
        next_stage = player.current_stage + 1

        if (player.greed_value >= settings.MAX_GREED
                or player.total_gamble_count >= 4
                or player.debt >= 2000000):
            is_game_over = True
            ending = "abyss"
            player.is_fallen = True
            player.ending_type = "abyss"
            next_stage = None
            k_response += ABYSS_ENDING_TEXT

        elif next_stage > len(ALL_STAGES) and player.greed_value < 50:
            is_game_over = True
            ending = "rebirth"
            player.ending_type = "rebirth"
            next_stage = None
            k_response += REBIRTH_ENDING_TEXT
        else:
            player.current_stage = next_stage

        record = ChoiceRecord(
            session_id=session_id,
            stage_number=stage["stage_number"],
            choice=choice,
            choice_type=choice_type,
            choice_text=choice_text,
            debt_before=debt_before,
            debt_after=player.debt,
            greed_before=greed_before,
            greed_after=player.greed_value,
            k_response=k_response,
        )
        self.db.add(record)

        return ChoiceResult(
            k_response=k_response,
            debt_change=player.debt - debt_before,
            greed_change=player.greed_value - greed_before,
            new_debt=player.debt,
            new_greed=player.greed_value,
            new_mental_state=player.mental_state,
            next_stage=next_stage,
            is_game_over=is_game_over,
            ending_type=ending,
        )

    async def get_current_stage(self, session_id: str) -> GameStageResponse:
        result = await self.db.execute(
            select(PlayerSession).where(PlayerSession.id == session_id)
        )
        player = result.scalar_one_or_none()
        if not player:
            raise HTTPException(status_code=404, detail="会话不存在")

        stage_index = player.current_stage - 1
        if stage_index >= len(ALL_STAGES):
            raise HTTPException(status_code=400, detail="游戏已结束")

        stage = ALL_STAGES[stage_index]
        dialogue = stage["k_dialogue"]
        if player.greed_value >= 50 and stage.get("k_dialogue_high_greed"):
            dialogue = stage["k_dialogue_high_greed"]

        return GameStageResponse(
            session_id=player.id,
            stage_number=stage["stage_number"],
            stage_title=stage["stage_title"],
            k_dialogue=dialogue,
            option_a=stage["option_a_text"],
            option_b=stage["option_b_text"],
            player_debt=player.debt,
            player_greed=player.greed_value,
            player_mental_state=player.mental_state,
            is_game_over=player.ending_type is not None,
            ending_type=player.ending_type,
        )
