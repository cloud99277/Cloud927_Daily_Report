"""Gemini Flash client for preprocessing tasks."""

import os

from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential

from src.llm.base_client import BaseLLMClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class GeminiClient(BaseLLMClient):
    """Client for Google Gemini models."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self.model = model
        self.client = genai.Client(api_key=api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        logger.info("Gemini generate: model=%s", self.model)
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return response.text
