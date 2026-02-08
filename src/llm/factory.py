"""Factory for creating LLM clients from config."""

import os
from typing import Dict, Any

from src.llm.base_client import BaseLLMClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_SUPPORTED_PROVIDERS = ["gemini", "claude", "openai"]


def _get_client_class(provider: str) -> type:
    """Lazy-import the client class for the given provider."""
    if provider == "gemini":
        from src.llm.gemini_client import GeminiClient
        return GeminiClient
    elif provider == "claude":
        from src.llm.claude_client import ClaudeClient
        return ClaudeClient
    elif provider == "openai":
        from src.llm.openai_client import OpenAIClient
        return OpenAIClient
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Supported: {_SUPPORTED_PROVIDERS}"
        )


def create_llm_client(config: Dict[str, Any]) -> BaseLLMClient:
    """Create an LLM client from a config dict.

    Args:
        config: Dict with keys: provider, model, api_key_env.

    Returns:
        An instance of the appropriate LLM client.

    Raises:
        ValueError: If provider is unknown.
        EnvironmentError: If the API key env var is not set.
    """
    provider = config["provider"]
    model = config["model"]
    api_key_env = config["api_key_env"]

    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise EnvironmentError(
            f"Environment variable {api_key_env} is not set"
        )

    client_cls = _get_client_class(provider)
    logger.info("Creating %s client: model=%s", provider, model)

    kwargs = {"api_key": api_key, "model": model}
    base_url = config.get("base_url") or os.environ.get("ANTHROPIC_BASE_URL")
    if base_url and provider == "claude":
        kwargs["base_url"] = base_url
    return client_cls(**kwargs)
