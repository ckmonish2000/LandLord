from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config import ENV_FILE


class AuthConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore", env_ignore_empty=True)

    # Secret used to sign auth tokens. Set a long random value in production.
    AUTH_SECRET: str = "dev-insecure-secret-change-me-in-production"
    TOKEN_TTL_MINUTES: int = 60


auth_settings = AuthConfig()
