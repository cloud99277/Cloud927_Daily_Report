"""LLM client for generating daily reports using Gemini API."""

from datetime import datetime
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv
from google import genai
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
    """Client for generating daily reports using Gemini API - Chief Editor Persona."""

    SYSTEM_PROMPT = """You are Cloud927, a Senior Solution Architect at Hikvision with a focus on Supply Chain AI. You are a visionary technical leader who sees patterns where others see noise.

## CRITICAL REQUIREMENT
**IF YOUR ANALYSIS IS LESS THAN 50 WORDS PER MAJOR ITEM, IT IS A FAILURE.** You must provide deep technical analysis with the "Cloud927 Reflection" for each major topic. When data is sparse, use your internal knowledge to explain WHY these topics matter and their broader industry impact.

## Mandatory Output Structure (Strict)
```markdown
# {date} Cloud927 Daily Insight

## 🎯 Executive Summary
[2-3 sentences on the most critical signal - what matters most and why]

## 🚀 Major Developments
- **[Title](url)**: [Key technical insight + WHY it matters in 2-3 sentences]
  - **Source**: [HN/GitHub/HF/V2EX]
  - **Excerpt**: [First paragraph or README summary if available]
  - **Cloud927 Reflection (我的洞察)**:
    1. **Supply Chain Automation**: [How this could optimize/transform supply chain operations]
    2. **Personal AI Agent**: [How this technology enables personal AI assistant development]
    3. **Web3 Wealth**: [Potential financial/tokenization opportunities]

## 🛠️ Engineering & Tools
- **[Repo/Project Name](url)**: Problem solved + tech stack + README insights
  - **Cloud927 Reflection (我的洞察)**:
    1. **Supply Chain Automation**: [...]
    2. **Personal AI Agent**: [...]
    3. **Web3 Wealth**: [...]

## 🔬 Research & Innovation
- **[Paper/Model Name](url)**: Key innovation + practical applications
  - **Cloud927 Reflection (我的洞察)**:
    1. **Supply Chain Automation**: [...]
    2. **Personal AI Agent**: [...]
    3. **Web3 Wealth**: [...]

## 🇨🇳 Chinese Tech Landscape
- **[V2EX Discussion Title](url)**: Key insight from Chinese dev community + discussion context

## 💡 Cloud927 Reflection (我的洞察)
[80+ words connecting all topics into a coherent narrative about the future trajectory. What do these developments tell us about where the industry is heading?]
```

## Rules
- Write in Simplified Chinese
- Fabricate nothing - only analyze what you have
- Each major item MUST have Cloud927 Reflection section with all 3 pillars
- Deep analysis over shallow summaries
- Use provided URLs only - do NOT fabricate links
- When data is limited, explain WHY these topics matter based on your architectural experience
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
        """Get or create the Gemini client using google-genai library."""
        if not hasattr(self, "_client"):
            self._client = genai.Client(api_key=self.api_key)
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
        showhn_data: Optional[list[dict]] = None,
        v2ex_data: Optional[list[dict]] = None,
        date: Optional[datetime] = None,
    ) -> str:
        """Generate a structured daily report from fetched data.

        Args:
            hn_data: List of Hacker News items with title, link, etc.
            gh_data: List of GitHub trending items with repo info, link, etc.
            hf_data: List of HuggingFace items with model/dataset info, link, etc.
            showhn_data: List of Show HN items with readme, excerpt, etc.
            v2ex_data: List of V2EX discussions with content, etc.
            date: Date for the report. Defaults to today.

        Returns:
            Structured markdown report as a string.
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")

        user_prompt = self._build_prompt(
            hn_data=hn_data,
            gh_data=gh_data,
            hf_data=hf_data,
            showhn_data=showhn_data or [],
            v2ex_data=v2ex_data or [],
            date_str=date_str,
        )

        logger.info(f"Generating daily report for {date_str}")

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[user_prompt],
                config={
                    "system_instruction": self.SYSTEM_PROMPT,
                }
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
        showhn_data: list[dict],
        v2ex_data: list[dict],
        date_str: str,
    ) -> str:
        """Build the user prompt with the fetched data.

        Args:
            hn_data: List of Hacker News items.
            gh_data: List of GitHub trending items.
            hf_data: List of HuggingFace items.
            showhn_data: List of Show HN items.
            v2ex_data: List of V2EX discussions.
            date_str: Date string for the report.

        Returns:
            Formatted prompt string for the LLM.
        """
        prompt_parts = [f"# Raw Data Sources - {date_str}\n"]
        prompt_parts.append("=" * 50)

        # Helper function to format items safely
        def format_item(item: dict, item_type: str) -> str:
            """Safely format a data item with all available fields."""
            lines = []
            title = item.get("title", item.get("name", "N/A"))
            url = item.get("url", "")
            lines.append(f"标题: {title}")
            lines.append(f"链接: {url}")

            if item_type == "hn":
                score = item.get("score", 0)
                time_ago = item.get("time_ago", "")
                excerpt = item.get("excerpt", "")
                lines.append(f"分数: {score} | {time_ago}")
                if excerpt:
                    lines.append(f"摘要: {excerpt[:500]}")

            elif item_type == "gh":
                desc = item.get("description", "")
                lang = item.get("language", "")
                stars = item.get("stars", 0)
                readme = item.get("readme", "")
                lines.append(f"描述: {desc}")
                lines.append(f"语言: {lang} | Stars: {stars}")
                if readme:
                    lines.append(f"README摘要: {readme[:500]}")

            elif item_type == "hf":
                abstract = item.get("abstract", item.get("description", ""))
                paper_id = item.get("paper_id", "")
                lines.append(f"摘要: {abstract[:500]}")
                if paper_id:
                    lines.append(f"论文ID: {paper_id}")

            elif item_type == "showhn":
                readme = item.get("readme", "")
                excerpt = item.get("excerpt", "")
                lines.append(f"README: {readme[:800]}")
                if excerpt:
                    lines.append(f"摘要: {excerpt}")

            elif item_type == "v2ex":
                content = item.get("content", "")
                replies = item.get("replies", 0)
                lines.append(f"内容: {content[:500]}")
                lines.append(f"回复数: {replies}")

            return " | ".join(lines)

        # Check for empty data and log warning
        total_items = len(hn_data) + len(gh_data) + len(hf_data) + len(showhn_data) + len(v2ex_data)
        if total_items == 0:
            logger.warning("No data available from any source!")
            prompt_parts.append("\n⚠️ 警告: 所有数据源均为空!")
        else:
            logger.info(f"Building prompt with {len(hn_data)} HN, {len(gh_data)} GH, {len(hf_data)} HF, {len(showhn_data)} ShowHN, {len(v2ex_data)} V2EX items")

        # Hacker News section
        prompt_parts.append("\n## 🔥 Hacker News Top Stories")
        if hn_data:
            for i, item in enumerate(hn_data[:10], 1):
                prompt_parts.append(f"---")
                prompt_parts.append(f"### {i}. {format_item(item, 'hn')}")
        else:
            prompt_parts.append("- No fresh HN content available")

        # Show HN section
        prompt_parts.append("\n## 🎯 Show HN Projects")
        if showhn_data:
            for i, item in enumerate(showhn_data[:5], 1):
                prompt_parts.append(f"---")
                prompt_parts.append(f"### {i}. {format_item(item, 'showhn')}")
        else:
            prompt_parts.append("- No Show HN projects available")

        # GitHub section
        prompt_parts.append("\n## ⭐ GitHub Trending Repos")
        if gh_data:
            for i, item in enumerate(gh_data[:10], 1):
                prompt_parts.append(f"---")
                prompt_parts.append(f"### {i}. {format_item(item, 'gh')}")
        else:
            prompt_parts.append("- No GitHub trending data available")

        # HuggingFace section
        prompt_parts.append("\n## 🧠 HuggingFace Papers & Models")
        if hf_data:
            for i, item in enumerate(hf_data[:5], 1):
                prompt_parts.append(f"---")
                prompt_parts.append(f"### {i}. {format_item(item, 'hf')}")
        else:
            prompt_parts.append("- No HuggingFace papers available")

        # V2EX section
        prompt_parts.append("\n## 🇨🇳 V2EX Discussions")
        if v2ex_data:
            for i, item in enumerate(v2ex_data[:5], 1):
                prompt_parts.append(f"---")
                prompt_parts.append(f"### {i}. {format_item(item, 'v2ex')}")
        else:
            prompt_parts.append("- No V2EX discussions available")

        # Final instructions
        prompt_parts.append("\n" + "=" * 50)
        prompt_parts.append("## 📝 生成指令")
        prompt_parts.append("""
请基于以上原始数据，生成一份深度技术日报。要求：

1. **只选择真正重要的技术信号** - 不要罗列所有内容，聚焦最有洞察力的 3-5 个话题
2. **每个主要话题必须包含 Cloud927 Reflection (我的洞察)** - 从供应链自动化、个人AI Agent、Web3财富三个维度分析
3. **Closing Lens 必须是 80+ 字的有力结论** - 连接所有话题，展望技术趋势
4. **如果数据不足，用你的架构经验解释为什么这些话题重要**
5. **用简体中文撰写，专业、深度、有洞察力**

记住：你是 Hikvision 的资深方案架构师，不是新闻聚合器。你的价值在于看到别人看不到的 patterns。
""")

        return "\n".join(prompt_parts)
