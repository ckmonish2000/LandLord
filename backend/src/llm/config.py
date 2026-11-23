from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config import ENV_FILE


class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    # Google AI Studio key (https://aistudio.google.com/apikey). Set it in backend/.env.
    GEMINI_API_KEY: SecretStr | None = None
    LLM_MODEL: str = "gemini-3.5-flash"
    LLM_TEMPERATURE: float = 0.3
    LLM_TIMEOUT_SECONDS: float = 60
    LLM_MAX_RETRIES: int = 2


llm_settings = LLMConfig()
