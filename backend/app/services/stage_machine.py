"""
状态机核心逻辑 - 剧本控命运，AI 控表现
纯 Python 控制阶段流转、发牌作弊、筹码结算
"""
import random
from app.models.game_stage import GameStage


class StageMachine:
    """游戏阶段状态机 - 绝对控制游戏命运"""

    @staticmethod
    def deal_cards_with_cheat(
        stage: str,
        player_chips: int,
        k_chips: int,
        player_action: str = None,
        player_bet: int = 0
    ) -> tuple[int, int]:
        """
        发牌作弊机制 - 根据阶段和玩家行为控制牌面

        返回: (player_card, k_card)
        """
        # stage_bait: 养猪阶段，强制玩家赢
        if stage == GameStage.BAIT:
            k_card = random.randint(1, 7)  # K 拿小牌
            player_card = random.randint(k_card + 1, 10)  # 玩家必定更大
            return player_card, k_card

        # stage_trap: 杀猪阶段，玩家大额加注必输
        if stage == GameStage.TRAP:
            if player_action == "raise" and player_bet >= 3000:
                # 玩家敢加注？强制发小牌给他
                player_card = random.randint(1, 5)
                k_card = random.randint(player_card + 1, 10)
                return player_card, k_card

        # 其他阶段：正常随机发牌
        cards = random.sample(range(1, 11), 2)
        return cards[0], cards[1]

    @staticmethod
    def check_stage_transition(
        current_stage: str,
        player_chips: int,
        bait_wins: int,
        hook_rounds: int,
        loan_accepted: bool
    ) -> tuple[bool, str | None, str]:
        """
        检查是否需要切换阶段

        返回: (是否切换, 新阶段, 切换原因)
        """
        # BAIT → HOOK: 连赢3局
        if current_stage == GameStage.BAIT and bait_wins >= 3:
            return True, GameStage.HOOK, "连赢3局，进入高端局"

        # HOOK → TRAP: 玩了5局以上
        if current_stage == GameStage.HOOK and hook_rounds >= 5:
            return True, GameStage.TRAP, "进入杀猪阶段"

        # TRAP → CONTRACT: 筹码归零
        if current_stage == GameStage.TRAP and player_chips <= 0:
            return True, GameStage.CONTRACT, "筹码归零，触发套路贷"

        # CONTRACT → VERDICT: 接受借款后继续游戏
        if current_stage == GameStage.CONTRACT and loan_accepted and hook_rounds >= 8:
            return True, GameStage.VERDICT, "进入终局审判"

        return False, None, ""

    @staticmethod
    def get_stage_config(stage: str) -> dict:
        """
        获取阶段配置（底注、UI主题等）
        """
        configs = {
            GameStage.BAIT: {
                "title": "序曲：新手福利",
                "hint": "前3局必赢，体验赚钱的快感！",
                "ante": 1000,
                "ui_theme": "golden"
            },
            GameStage.HOOK: {
                "title": "第一幕：高端局",
                "hint": "K 正式登场，赌注升级",
                "ante": 1000,
                "ui_theme": "dark"
            },
            GameStage.TRAP: {
                "title": "第二幕：深渊",
                "hint": "⚠️ 底注翻倍，风险激增",
                "ante": 2000,
                "ui_theme": "danger"
            },
            GameStage.CONTRACT: {
                "title": "第三幕：最后的机会",
                "hint": "接受借款，翻本在此一举",
                "ante": 5000,
                "ui_theme": "contract"
            },
            GameStage.VERDICT: {
                "title": "终局：审判",
                "hint": "账户已冻结，提现通道关闭",
                "ante": 0,
                "ui_theme": "frozen"
            }
        }
        return configs.get(stage, configs[GameStage.BAIT])

    @staticmethod
    def apply_stage_rules(stage: str, action: str, player_chips: int) -> dict:
        """
        应用阶段特殊规则

        返回: 规则修正参数
        """
        rules = {}

        if stage == GameStage.BAIT:
            rules["force_player_win"] = True

        if stage == GameStage.HOOK:
            rules["k_strategy"] = "friendly"  # K 前期友好

        if stage == GameStage.TRAP:
            if action == "raise":
                rules["force_player_lose"] = True
            rules["k_strategy"] = "aggressive"  # K 极度贪婪

        if stage == GameStage.VERDICT:
            rules["freeze_account"] = True  # 冻结账户

        return rules
