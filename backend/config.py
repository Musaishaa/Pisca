from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    llm_provider: str = "none"
    llm_model: str = "llama3.2:3b"
    llm_base_url: str = "http://localhost:11434"
    database_url: str = f"sqlite:///{(BASE_DIR / 'data' / 'pisca.db').as_posix()}"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
