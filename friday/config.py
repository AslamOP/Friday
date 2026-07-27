from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class FridayConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    openrouter_api_key: str = ""
    opencode_zen_api_key: str = ""
    ollama_url: str = "http://127.0.0.1:11434"
    database_url: str = "sqlite+aiosqlite:///./data/friday.db"
    log_level: str = "INFO"

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent
    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

@lru_cache()
def get_config() -> FridayConfig:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        return FridayConfig(_env_file=str(env_path))
    return FridayConfig()
