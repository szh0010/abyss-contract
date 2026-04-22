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


settings = Settings()
