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

    SYSTEM_PROMPT = """你是一个专业的技术资讯助手，负责将每日收集的技术新闻和资讯整理成结构化的中文日报。

## 工作要求

1. **语言**: 生成简体中文内容
2. **格式**: 使用 Markdown 格式，保持清晰的层次结构
3. **内容来源**: 必须严格使用提供的信息源，**不要**添加或编造任何链接
4. **摘要风格**: 简洁明了，突出技术要点和重要信息

## 日报结构

请按以下结构生成日报：

```
# {date} 技术日报

## Hacker News 热门

- [标题](链接) - 简要描述/技术要点

## GitHub Trending

- [仓库名](链接) - 简述项目功能和特点

## HuggingFace 精选

- [模型/数据集名](链接) - 简述用途和亮点

## 今日总结

一段总结今日技术热点的话。
```

## 注意事项

- 只使用提供的信息，不要添加超出范围的内容
- 保持摘要简洁，每条不超过两句话
- 链接必须是原始来源，不要转换或简化
- 如果某部分没有内容，相应章节可以省略或标记为"暂无"
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
        """Build the user prompt with the fetched data.

        Args:
            hn_data: Hacker News data.
            gh_data: GitHub data.
            hf_data: HuggingFace data.
            date_str: Date string for the report.

        Returns:
            Formatted prompt string.
        """
        prompt_parts = [f"# 科技日报数据 - {date_str}\n"]

        # Hacker News section
        prompt_parts.append("## Hacker News 热门项目")
        if hn_data:
            for item in hn_data:
                title = item.get("title", "N/A")
                link = item.get("link", "")
                points = item.get("points", 0)
                prompt_parts.append(f"- {title} ({points} points) - {link}")
        else:
            prompt_parts.append("暂无HN热门内容")

        prompt_parts.append("")

        # GitHub section
        prompt_parts.append("## GitHub Trending")
        if gh_data:
            for item in gh_data:
                repo = item.get("repo", "")
                desc = item.get("description", "")
                link = item.get("link", "")
                lang = item.get("language", "")
                stars = item.get("stars", 0)
                lang_info = f"[{lang}]" if lang else ""
                prompt_parts.append(f"- {repo} {lang_info} ({stars} stars) - {desc} - {link}")
        else:
            prompt_parts.append("暂无GitHub trending内容")

        prompt_parts.append("")

        # HuggingFace section
        prompt_parts.append("## HuggingFace 精选")
        if hf_data:
            for item in hf_data:
                name = item.get("name", "")
                link = item.get("link", "")
                desc = item.get("description", "")
                downloads = item.get("downloads", 0)
                prompt_parts.append(f"- {name} ({downloads} downloads) - {desc} - {link}")
        else:
            prompt_parts.append("暂无HuggingFace精选内容")

        prompt_parts.append("")
        prompt_parts.append("请根据以上数据生成结构化的中文技术日报。")

        return "\n".join(prompt_parts)
