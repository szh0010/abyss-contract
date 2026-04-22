from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App Config"""
    DATABASE_URL: str = "sqlite+aiosqlite:///./abyss_contract.db"
    SECRET_KEY: str = "abyss-contract-secret-key"
    DEBUG: bool = True
    INITIAL_DEBT: int = 500000
    MAX_GREED: int = 100
    GREED_INCREASE_ON_GAMBLE: int = 15
    GREED_DECREASE_ON_REFUSE: int = 5
    TOTAL_STAGES: int = 7

    class Config:
        env_file = ".env"


settings = Settings()