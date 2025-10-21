"""Centralized LLM configuration for the project."""

import os

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# LLM Configuration - can be overridden via environment variables
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:1234/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "dummy")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))


def get_llm() -> BaseChatModel:
    """Get configured LLM instance.

    Returns:
        Configured BaseChatModel instance (ChatOpenAI, ChatOllama, etc.)
    """
    return ChatOpenAI(
        model=LLM_MODEL, temperature=LLM_TEMPERATURE, base_url=LLM_BASE_URL, api_key=LLM_API_KEY
    )


def get_embedding_model():
    """Get configured embedding instance.

    Returns:
        Configured embedding instance (ChatOpenAI, ChatOllama, etc.)
    """
    return OpenAIEmbeddings(
        model="text-embedding-nomic-embed-text-v1.5",
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        check_embedding_ctx_length=False,
    )
