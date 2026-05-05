"""
游戏阶段枚举 - 五阶段杀猪盘流程
"""
from enum import Enum


class GameStage(str, Enum):
    """游戏阶段枚举"""
    BAIT = "stage_bait"        # 序曲-养猪阶段（强制玩家赢）
    HOOK = "stage_hook"        # 第一幕-高端局（K故意输，诱导加注）
    TRAP = "stage_trap"        # 第二幕-杀猪阶段（玩家加注必输）
    CONTRACT = "stage_contract" # 第三幕-套路贷（筹码归零，诱导借款）
    VERDICT = "stage_verdict"   # 终局-强制冻结（账户锁死）
