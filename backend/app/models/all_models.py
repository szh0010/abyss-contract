"""
统一引出口：所有 SQLAlchemy 模型在这里集中 import 一次，
方便 init_db / Alembic / 测试夹具拿到一个完整的元数据快照。

新接的四张持久化表：
  - User         (users)            ：账号 + 密码哈希
  - GameState    (game_states)      ：1:1，关卡 / 防骗得分
  - UserMedal    (user_medals)      ：1:N，已解锁勋章
  - Post         (posts)            ：1:N，深渊树洞帖子

兼容遗留：
  - PlayerSession / StoryStage / ChoiceRecord / UserProfile
"""
from app.database import Base

from app.models.user import User
from app.models.game_state import GameState
from app.models.user_medal import UserMedal
from app.models.post import Post

# 兼容老业务表，避免 init_db 漏建
from app.models.player import PlayerSession
from app.models.story import StoryStage
from app.models.choice import ChoiceRecord
from app.models.user_profile import UserProfile

__all__ = [
    "Base",
    "User",
    "GameState",
    "UserMedal",
    "Post",
    "PlayerSession",
    "StoryStage",
    "ChoiceRecord",
    "UserProfile",
]
