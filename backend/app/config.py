from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App Config"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )

    DATABASE_URL: str = "sqlite+aiosqlite:///./abyss_contract.db"
    SECRET_KEY: str = "abyss-contract-secret-key"
    APP_DEBUG: bool = True
    INITIAL_DEBT: int = 500000
    MAX_GREED: int = 100
    GREED_INCREASE_ON_GAMBLE: int = 15
    GREED_DECREASE_ON_REFUSE: int = 5
    TOTAL_STAGES: int = 7

    # DeepSeek LLM（保留兼容，旧路径可继续使用；新路径已切到 Coze）
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Coze 智能体（国内版） —— 反诈守护者主用
    # 默认值仅用于本地调试；生产请通过 .env 注入 COZE_API_TOKEN
    COZE_API_TOKEN: str = ""
    COZE_BOT_ID: str = "7641078571066687542"
    COZE_GAME_BOT_ID: str = "7641579479487528987"  # 反诈剧本杀专线智能体
    COZE_BASE_URL: str = "https://api.coze.cn"
    COZE_USER_ID: str = "abyss_default_user"      # 与 Coze 端会话归集字段对应
    COZE_TIMEOUT_SECONDS: float = 45.0
    COZE_POLL_INTERVAL_SECONDS: float = 1.0

    # ===== JWT =====
    JWT_SECRET_KEY: str = "abyss-jwt-change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # 数值引擎
    DEBT_DECREASE_ON_REJECT: int = 5000
    GREED_INCREASE_ON_BARGAIN: int = 5
    GREED_INCREASE_ON_VIOLENCE: int = 2
    GOOD_ENDING_DEBT_THRESHOLD: int = 485000


settings = Settings()
