"""Global settings. Values can be overridden by environment variables or backend/.env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / ".env"


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore", env_ignore_empty=True)

    APP_NAME: str = "__PROJECT_NAME__"
    DATA_DIR: Path = BASE_DIR / "data"
    DATABASE_URL: str | None = None  # None: SQLite file in DATA_DIR

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL or f"sqlite:///{self.DATA_DIR / 'app.db'}"


settings = Config()
