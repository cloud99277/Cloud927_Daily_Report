"""Claude API client for insight generation."""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.llm.base_client import BaseLLMClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ClaudeClient(BaseLLMClient):
    """Client for Anthropic Claude models.

    Uses raw httpx instead of the anthropic SDK to avoid extra headers
    that some proxy services reject.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        base_url: str | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = (base_url or "https://api.anthropic.com").rstrip("/")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        logger.info("Claude generate: model=%s", self.model)
        resp = httpx.post(
            f"{self.base_url}/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]
