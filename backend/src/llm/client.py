"""The chat model agents use. Today a local Qwen served by LM Studio; any
OpenAI-compatible server works by changing LLM_BASE_URL / LLM_MODEL. To switch to
another provider, change this file and agents don't change.

Returns a LangChain chat model, so LangGraph can use it directly:

    llm = get_llm()
    llm.invoke("Summarise this complaint in one line: ...")
    llm.with_structured_output(MySchema)     # typed answers (JSON schema enforced by LM Studio)
    llm.bind_tools([...])                    # tool calling, if the loaded model supports it
"""

from functools import lru_cache

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from src.llm.config import llm_settings


@lru_cache
def get_llm(model: str | None = None, temperature: float | None = None) -> BaseChatModel:
    """Shared chat model, created once per (model, temperature).

    Leave both empty for the defaults from config (LLM_MODEL, LLM_TEMPERATURE).
    Safe to share across threads (the worker pool runs agents in parallel).
    """
    return ChatOpenAI(
        base_url=llm_settings.LLM_BASE_URL,
        api_key=llm_settings.LLM_API_KEY,
        model=model or llm_settings.LLM_MODEL,
        temperature=llm_settings.LLM_TEMPERATURE if temperature is None else temperature,
        timeout=llm_settings.LLM_TIMEOUT_SECONDS,
        max_retries=llm_settings.LLM_MAX_RETRIES,
    )
