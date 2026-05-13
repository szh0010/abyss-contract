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

    # DeepSeek LLM
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

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
