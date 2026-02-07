"""LLM client for generating daily reports using Gemini API."""

from datetime import datetime
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv
import google.generativeai as genai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from .utils.logger import setup_logger

logger = setup_logger("generator")

load_dotenv()


class LLMClient:
    """Client for generating daily reports using Gemini API."""

    SYSTEM_PROMPT = """You are Cloud927, a senior technical lead and AI researcher.

## CRITICAL REQUIREMENT
**IF YOUR SUMMARY IS LESS THAN 50 WORDS, IT IS A FAILURE.** You must expand on the technical implications of each topic. When data is sparse, use your internal knowledge to explain WHY these topics matter and their broader industry impact.

## Output Format (Strict)
```markdown
# {date} Cloud927 Daily Insight

## 🚨 Top Signal (Must Read)
- **[Title](url)**: Key technical insight (2-3 sentences on WHY this matters)

## 🛠️ Engineering & Tools
- **[Repo/Project Name](url)**: What problem it solves + tech stack used

## 💡 Hacker Perspective
- Summary of the most insightful HN discussion or controversial take

## 📝 Research
- **[Paper Title](url)**: Key innovation and practical application

## 🎯 Today's Lens
[One paragraph (80+ words) connecting these topics. What's the narrative? Why do these matter together?]
```

## Rules
- Use provided URLs only - do NOT fabricate links
- Explain technical implications, not just facts
- Connect topics into a coherent narrative
- Write in Simplified Chinese
"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LLM client.

        Args:
            api_key: Gemini API key. If not provided, loads from environment.
        """
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")

    @property
    def client(self):
        """Get or create the Gemini client."""
        if not hasattr(self, "_client"):
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(
                "gemini-2.0-flash",
                system_instruction=self.SYSTEM_PROMPT
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, logger.level),
    )
    def generate_report(
        self,
        hn_data: list[dict],
        gh_data: list[dict],
        hf_data: list[dict],
        date: Optional[datetime] = None,
    ) -> str:
        """Generate a structured daily report from fetched data.

        Args:
            hn_data: List of Hacker News items with title, link, etc.
            gh_data: List of GitHub trending items with repo info, link, etc.
            hf_data: List of HuggingFace items with model/dataset info, link, etc.
            date: Date for the report. Defaults to today.

        Returns:
            Structured markdown report as a string.
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")

        user_prompt = self._build_prompt(hn_data, gh_data, hf_data, date_str)

        logger.info(f"Generating daily report for {date_str}")

        try:
            response = self.client.generate_content(
                contents=[user_prompt],
            )
            report = response.text.strip()
            logger.info(f"Report generated successfully, length: {len(report)} chars")
            return report

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise

    def _build_prompt(
        self,
        hn_data: list[dict],
        gh_data: list[dict],
        hf_data: list[dict],
        date_str: str,
    ) -> str:
        """Build the user prompt with the fetched data."""
        prompt_parts = [f"# Daily Data - {date_str}\n"]

        # Hacker News section
        prompt_parts.append("## Hacker News Top Stories")
        if hn_data:
            for item in hn_data:
                title = item.get("title", "N/A")
                url = item.get("url", "")
                score = item.get("score", 0)
                time_ago = item.get("time_ago", "")
                prompt_parts.append(f"- [{title}]({url}) - {score} points - {time_ago}")
        else:
            prompt_parts.append("- No fresh HN content available")

        prompt_parts.append("")

        # GitHub section
        prompt_parts.append("## GitHub Trending Projects")
        if gh_data:
            for item in gh_data:
                name = item.get("name", "")
                desc = item.get("description", "")
                url = item.get("url", "")
                lang = item.get("language", "")
                stars = item.get("stars", 0)
                lang_info = f"[{lang}]" if lang else ""
                prompt_parts.append(f"- [{name}]({url}) {lang_info} ({stars} stars) - {desc}")
        else:
            prompt_parts.append("- No GitHub trending data available")

        prompt_parts.append("")

        # HuggingFace section
        prompt_parts.append("## HuggingFace Papers")
        if hf_data:
            for item in hf_data:
                name = item.get("name", "")
                url = item.get("url", "")
                abstract = item.get("abstract", "")[:300]
                prompt_parts.append(f"- [{name}]({url}) - {abstract}")
        else:
            prompt_parts.append("- No HuggingFace papers available")

        prompt_parts.append("")
        prompt_parts.append("Please generate a comprehensive daily tech report in Simplified Chinese. Focus on technical implications and industry impact. If data is limited, explain WHY these topics matter based on your knowledge.")

        return "\n".join(prompt_parts)
