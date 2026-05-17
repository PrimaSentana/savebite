from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:prima@localhost:5432/savebite"
    SECRET_KEY: str = "3451c5993b4c6c48c69427b883faab766eb8507a3325a7058977ab7c7cc8ff2c"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

settings = Settings()