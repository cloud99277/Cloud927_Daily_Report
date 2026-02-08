"""Dual-layer report generator using LLM abstraction layer.

Layer 1 (preprocessor): Gemini Flash summarizes each news item and assigns importance.
Layer 2 (insight): Claude generates the full report with deep analysis.
"""

from datetime import datetime
from typing import Any

from src.config import Config
from src.llm.base_client import BaseLLMClient
from src.llm.factory import create_llm_client
from src.utils.logger import setup_logger

logger = setup_logger("generator_v3")

# 6 sectors matching the clustering categories
SECTORS = ["AI前沿", "创业/投融资", "金融/宏观", "Web3/Crypto", "科技政策", "全球重大事件"]


class ReportGenerator:
    """Dual-layer report generator.

    Uses a fast preprocessor model to summarize and score items, then
    an insight model to produce the final report.
    """

    PREPROCESSOR_SYSTEM = (
        "你是新闻预处理助手。对每条新闻输出一行，格式严格为:\n"
        "importance(1-10)|200字以内中文摘要\n"
        "不要输出其他内容。importance 越高代表对科技从业者决策价值越大。"
    )

    INSIGHT_SYSTEM = """你是 Cloud927 — 个人决策参考系统。
你的目标：帮助读者在 2 分钟内抓住当天最关键的信号，并在需要时提供深度洞察。

## 输出结构

### 快速扫描层（2 分钟阅读）

1. **一句话核心信号** — 今天最值得关注的一件事
2. **六大板块速览**（每个板块最多 Top 3）
   板块：AI前沿 | 创业/投融资 | 金融/宏观 | Web3/Crypto | 科技政策 | 全球重大事件
   每条格式：`[来源数] 标题 — 一句话要点`
   来源数 >= 3 的条目标记为「多源验证」
3. **行动清单**（最多 3 条，必须是今天就能做的具体动作）

### 深度洞察层（可选阅读）

挑选 2-3 个最重要的话题，每个展开为：
- 发生了什么
- 为什么重要
- 对你意味着什么
- 建议行动

## 规则
- 全部使用简体中文
- cross_source_count >= 3 的条目优先展示并标注
- 保持客观，区分事实与推测
- 引用具体来源和链接
"""

    def __init__(self, config: Config | None = None):
        cfg = config or Config()
        llm_cfg = cfg.llm

        preprocessor_cfg = llm_cfg.get("preprocessor", {
            "provider": "gemini",
            "model": "gemini-2.0-flash",
            "api_key_env": "GEMINI_API_KEY",
        })
        insight_cfg = llm_cfg.get("insight", {
            "provider": "claude",
            "model": "claude-sonnet-4-20250514",
            "api_key_env": "ANTHROPIC_API_KEY",
        })

        self.preprocessor: BaseLLMClient = create_llm_client(preprocessor_cfg)
        self.insight: BaseLLMClient = create_llm_client(insight_cfg)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_report(
        self,
        items: list[dict],
        clusters: dict[str, list[dict]],
        timeline: dict[str, Any],
        date: datetime | None = None,
    ) -> str:
        """Orchestrate both LLM layers and return the final report.

        Args:
            items: Deduplicated news items (with cross_source_count / reported_by).
            clusters: Category -> list of items from the Clusterer.
            timeline: Timeline tracker output with "new" and "updated" entities.
            date: Report date (defaults to today).

        Returns:
            The final markdown report string.
        """
        if date is None:
            date = datetime.now()
        date_str = date.strftime("%Y-%m-%d")

        # Layer 1 — preprocess: summarise + score each item
        logger.info("Layer 1: preprocessing %d items", len(items))
        summaries = self._preprocess(items)

        # Layer 2 — insight: generate the full report
        logger.info("Layer 2: generating insight report")
        user_prompt = self._build_insight_prompt(
            items, summaries, clusters, timeline, date_str,
        )
        report = self.insight.generate(self.INSIGHT_SYSTEM, user_prompt)
        logger.info("Report generated: %d chars", len(report))
        return report

    # ------------------------------------------------------------------
    # Layer 1 — Preprocessor
    # ------------------------------------------------------------------

    def _preprocess(self, items: list[dict]) -> list[dict]:
        """Use the preprocessor LLM to summarise and score items.

        Returns a list of dicts with keys: title, summary, importance.
        """
        if not items:
            return []

        batch_text = self._build_preprocess_prompt(items)
        raw = self.preprocessor.generate(self.PREPROCESSOR_SYSTEM, batch_text)
        return self._parse_preprocess_response(raw, items)

    def _build_preprocess_prompt(self, items: list[dict]) -> str:
        """Build the user prompt for the preprocessor."""
        lines = [f"共 {len(items)} 条新闻，请逐条处理:\n"]
        for i, item in enumerate(items, 1):
            title = item.get("title", "")
            source = item.get("source", "")
            content = (item.get("content", "") or "")[:300]
            cross = item.get("cross_source_count", 1)
            lines.append(
                f"[{i}] ({source}, 来源数={cross}) {title}"
            )
            if content:
                lines.append(f"    {content}")
        return "\n".join(lines)

    @staticmethod
    def _parse_preprocess_response(
        raw: str, items: list[dict]
    ) -> list[dict]:
        """Parse preprocessor output into structured summaries."""
        results = []
        raw_lines = [ln.strip() for ln in raw.strip().splitlines() if ln.strip()]

        for idx, item in enumerate(items):
            if idx < len(raw_lines):
                line = raw_lines[idx]
                # Strip leading "[N] " prefix if the model echoed it
                if line.startswith("["):
                    _, _, line = line.partition("]")
                    line = line.strip()
                parts = line.split("|", 1)
                try:
                    importance = int(parts[0].strip())
                except (ValueError, IndexError):
                    importance = 5
                summary = parts[1].strip() if len(parts) > 1 else item.get("title", "")
            else:
                importance = 5
                summary = item.get("title", "")

            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "source": item.get("source", ""),
                "summary": summary,
                "importance": importance,
                "cross_source_count": item.get("cross_source_count", 1),
                "reported_by": item.get("reported_by", []),
            })
        return results

    # ------------------------------------------------------------------
    # Layer 2 — Insight prompt builder
    # ------------------------------------------------------------------

    def _build_insight_prompt(
        self,
        items: list[dict],
        summaries: list[dict],
        clusters: dict[str, list[dict]],
        timeline: dict[str, Any],
        date_str: str,
    ) -> str:
        """Build the user prompt for the insight model."""
        parts: list[str] = []
        parts.append(f"# Cloud927 日报数据 — {date_str}\n")
        parts.append(self._format_sector_data(summaries, clusters))
        parts.append(self._format_timeline(timeline))
        parts.append(self._format_generation_instructions(date_str))
        return "\n".join(parts)

    def _format_sector_data(
        self,
        summaries: list[dict],
        clusters: dict[str, list[dict]],
    ) -> str:
        """Format clustered items with preprocessor summaries."""
        # Build a lookup from title -> summary dict
        summary_map: dict[str, dict] = {}
        for s in summaries:
            summary_map[s["title"]] = s

        lines: list[str] = ["## 板块数据\n"]

        for sector in SECTORS:
            cluster_items = clusters.get(sector, [])
            if not cluster_items:
                continue

            lines.append(f"### {sector} ({len(cluster_items)} 条)\n")

            for i, item in enumerate(cluster_items[:5], 1):
                title = item.get("title", "")
                url = item.get("url", "")
                source = item.get("source", "")
                cross = item.get("cross_source_count", 1)

                sm = summary_map.get(title, {})
                importance = sm.get("importance", 5)
                summary = sm.get("summary", title)

                lines.append(
                    f"{i}. **[{title}]({url})**"
                )
                lines.append(
                    f"   来源: {source} | 重要性: {importance}/10 | 来源数: {cross}"
                )
                if cross >= 3:
                    reported = ", ".join(item.get("reported_by", []))
                    lines.append(f"   多源验证: {reported}")
                lines.append(f"   摘要: {summary}")
                lines.append("")

        # Items not in any sector
        clustered_titles = set()
        for sector_items in clusters.values():
            for it in sector_items:
                clustered_titles.add(it.get("title", ""))

        unclustered = [s for s in summaries if s["title"] not in clustered_titles]
        if unclustered:
            lines.append(f"### 其他 ({len(unclustered)} 条)\n")
            for s in sorted(unclustered, key=lambda x: x["importance"], reverse=True)[:5]:
                lines.append(
                    f"- [{s['title']}]({s['url']}) (重要性: {s['importance']}/10, "
                    f"来源数: {s['cross_source_count']})"
                )
                lines.append(f"  摘要: {s['summary']}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _format_timeline(timeline: dict[str, Any]) -> str:
        """Format timeline tracking data."""
        lines = ["## 趋势追踪\n"]

        new_entities = timeline.get("new", [])
        updated_entities = timeline.get("updated", [])

        if new_entities:
            lines.append("**新出现的实体:**\n")
            for item in new_entities[:5]:
                entity = item.get("entity", "Unknown")
                event = item.get("first_event", {})
                title = event.get("title", "")[:60]
                lines.append(f"- {entity}: {title}")

        if updated_entities:
            lines.append("\n**持续追踪的实体:**\n")
            for item in updated_entities[:5]:
                entity = item.get("entity", "Unknown")
                new_event = item.get("new_event", {})
                title = new_event.get("title", "")[:60]
                lines.append(f"- {entity}: {title}")

        if not new_entities and not updated_entities:
            lines.append("暂无趋势数据。")

        return "\n".join(lines)

    @staticmethod
    def _format_generation_instructions(date_str: str) -> str:
        """Final instructions appended to the insight prompt."""
        return f"""
---

## 生成要求

请根据以上数据生成 {date_str} 的 Cloud927 日报。

1. 快速扫描层：一句话核心信号 + 六板块 Top 3 + 行动清单(<=3)
2. 深度洞察层：2-3 个最重要话题展开分析
3. cross_source_count >= 3 的条目优先展示并标注「多源验证」
4. 全部使用简体中文
"""
