"""OpenAI GPT client for backup insight generation."""

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.llm.base_client import BaseLLMClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI GPT models."""

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self.model = model
        self.client = OpenAI(api_key=api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        logger.info("OpenAI generate: model=%s", self.model)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
