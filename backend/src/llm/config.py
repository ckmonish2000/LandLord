from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config import ENV_FILE


class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore", env_ignore_empty=True)

    # Any OpenAI-compatible server. Default: LM Studio's local server
    # (Developer tab → Start server; check it with `curl localhost:1234/v1/models`).
    LLM_BASE_URL: str = "http://localhost:1234/v1"
    LLM_MODEL: str = "qwen-local"  # the model id LM Studio lists for the loaded model
    LLM_API_KEY: SecretStr = SecretStr("lm-studio")  # LM Studio ignores it; hosted servers need a real key
    LLM_TEMPERATURE: float = 0.3
    LLM_TIMEOUT_SECONDS: float = 120  # local models on a laptop can be slow
    LLM_MAX_RETRIES: int = 1


llm_settings = LLMConfig()
