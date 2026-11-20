from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config import ENV_FILE, settings


class WhatsappConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    # SQLite file path, or a Postgres URL like postgres://user:pass@localhost:5432/landlord
    WHATSAPP_DB: str = str(settings.DATA_DIR / "whatsapp.db")


whatsapp_settings = WhatsappConfig()
