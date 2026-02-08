"""China Fetcher Base - RSSHub based fetchers for Chinese sources."""

import logging
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class RSSHubFetcher(ABC):
    """Base fetcher for Chinese sources via RSSHub."""

    def __init__(
        self,
        rsshub_url: str,
        source_name: str,
        timeout: int = 30,
        retry_attempts: int = 3
    ):
        self.rsshub_url = rsshub_url
        self.source_name = source_name
        self.timeout = timeout
        self.retry_attempts = retry_attempts

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_json(self) -> dict | None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        response = requests.get(self.rsshub_url, timeout=self.timeout, headers=headers)
        response.raise_for_status()
        return response.json()

    def _parse_timestamp(self, date_str: str) -> int:
        if not date_str:
            return int(time.time())
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return int(dt.timestamp())
        except ValueError:
            pass
        chinese_formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%m月%d日 %H:%M", "%Y年%m月%d日"]
        for fmt in chinese_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return int(dt.timestamp())
            except ValueError:
                continue
        return int(time.time())

    def _clean_html(self, html: str) -> str:
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        text = soup.get_text(strip=True)
        text = " ".join(text.split())
        return text[:500] if len(text) > 500 else text

    def _parse_item(self, item: dict) -> dict:
        return {
            "title": item.get("title", "No title"),
            "url": item.get("url", ""),
            "source": self.source_name,
            "timestamp": self._parse_timestamp(item.get("date") or item.get("pubDate") or item.get("created_at")),
            "content": self._clean_html(item.get("description") or item.get("content") or ""),
        }

    def fetch(self, limit: int = 20) -> list[dict]:
        logger.info(f"Fetching from {self.source_name}")
        try:
            data = self._fetch_json()
            if not data:
                return self._get_mock_data()
            items = []
            if isinstance(data, dict) and "items" in data:
                raw_items = data["items"]
            elif isinstance(data, dict):
                raw_items = data.get("items") or data.get("data") or data.get("results") or list(data.values())
            elif isinstance(data, list):
                raw_items = data
            else:
                raw_items = []
            for raw_item in raw_items[:limit]:
                if isinstance(raw_item, dict):
                    item = self._parse_item(raw_item)
                    items.append(item)
            logger.info(f"Fetched {len(items)} items from {self.source_name}")
            return items
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {self.source_name}: {e}")
            return self._get_mock_data()
        except Exception as e:
            logger.error(f"Failed to fetch {self.source_name}: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> list[dict]:
        import datetime
        logger.warning(f"Using mock data for {self.source_name}")
        return [{
            "title": f"【{self.source_name}】{datetime.datetime.now().strftime('%H:%M')} - 示例新闻标题",
            "url": "https://example.com",
            "source": self.source_name,
            "timestamp": int(time.time()),
            "content": "这是模拟数据，当数据源无法访问时使用。",
        }]


class ChinaNewsFetcher(RSSHubFetcher):
    """Base fetcher for Chinese news sources."""

    def __init__(self, rsshub_url: str, source_name: str):
        super().__init__(rsshub_url, source_name, timeout=30, retry_attempts=3)

    def _parse_item(self, item: dict) -> dict:
        parsed = super()._parse_item(item)
        parsed["source_type"] = "china_news"
        parsed["language"] = "zh"
        if "author" in item:
            parsed["author"] = item["author"]
        if "category" in item:
            categories = item["category"]
            if isinstance(categories, str):
                categories = [categories]
            parsed["categories"] = categories
        return parsed
