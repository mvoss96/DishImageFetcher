from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DB_PATH: str = Field(default="cache.db")
    API_KEY: str = Field(default="")
    CSE_ID: str = Field(default="")

    class Config:
        env_file = ".env"