"""The chat model agents use. Today Gemini; swap the provider here and agents don't change.

Returns a LangChain chat model, so LangGraph can use it directly:

    llm = get_llm()
    llm.invoke("Summarise this complaint in one line: ...")
    llm.bind_tools([...])                    # tool calling inside a LangGraph node
    llm.with_structured_output(MySchema)     # typed answers
"""

from functools import lru_cache

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from src.llm.config import llm_settings
from src.llm.exceptions import LLMNotConfigured


@lru_cache
def get_llm(model: str | None = None, temperature: float | None = None) -> BaseChatModel:
    """Shared chat model, created once per (model, temperature).

    Leave both empty for the defaults from config (LLM_MODEL, LLM_TEMPERATURE).
    Safe to share across threads (the worker pool runs agents in parallel).
    """
    if llm_settings.GEMINI_API_KEY is None:
        raise LLMNotConfigured("set GEMINI_API_KEY in backend/.env")
    return ChatGoogleGenerativeAI(
        model=model or llm_settings.LLM_MODEL,
        api_key=llm_settings.GEMINI_API_KEY,
        temperature=llm_settings.LLM_TEMPERATURE if temperature is None else temperature,
        timeout=llm_settings.LLM_TIMEOUT_SECONDS,
        max_retries=llm_settings.LLM_MAX_RETRIES,
    )
