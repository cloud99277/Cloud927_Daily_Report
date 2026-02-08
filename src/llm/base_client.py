"""Abstract base class for LLM clients."""

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Base class that all LLM clients must implement."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response from the LLM.

        Args:
            system_prompt: System-level instruction for the model.
            user_prompt: User-level input for the model.

        Returns:
            The generated text response.
        """
