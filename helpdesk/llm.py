"""One function that returns a chat model, so the rest of the code doesn't care
which provider is used. Switch with LLM_PROVIDER / LLM_MODEL in .env."""
from langchain_core.language_models.chat_models import BaseChatModel

from . import config


def get_llm() -> BaseChatModel:
    if config.LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=config.LLM_MODEL, base_url=config.OLLAMA_URL, temperature=0)
    if config.LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI  # needs GOOGLE_API_KEY

        return ChatGoogleGenerativeAI(model=config.LLM_MODEL, temperature=0)
    if config.LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI  # needs OPENAI_API_KEY

        return ChatOpenAI(model=config.LLM_MODEL, temperature=0)
    raise ValueError(f"Unknown LLM_PROVIDER: {config.LLM_PROVIDER}")
