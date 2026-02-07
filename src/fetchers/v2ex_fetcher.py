"""V2EX Fetcher using RSSHub JSON endpoint for Chinese developer ecosystem trends."""

import logging
from datetime import datetime
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Mock data as fallback
MOCK_V2EX_POSTS = [
    {
        "title": "开源一个基于 AI 的代码审查工具",
        "url": "https://v2ex.com/t/1234567",
        "author": "developer1",
        "created_at": datetime.now().isoformat(),
        "content": "分享一个基于大语言模型的代码审查工具，可以自动检测代码中的潜在问题和优化建议。",
        "replies": 42,
        "views": 1234,
        "node": "分享创造",
    },
    {
        "title": "求助：如何设计高并发的消息队列系统",
        "url": "https://v2ex.com/t/1234568",
        "author": "backend_dev",
        "created_at": datetime.now().isoformat(),
        "content": "正在设计一个支持百万级并发的消息队列系统，遇到了一些架构上的困惑。",
        "replies": 28,
        "views": 856,
        "node": "问与答",
    },
    {
        "title": "Rust vs Go：微服务选型经验分享",
        "url": "https://v2ex.com/t/1234569",
        "author": "sys_arch",
        "created_at": datetime.now().isoformat(),
        "content": "基于一年的实际项目经验，对比一下 Rust 和 Go 在微服务开发中的优劣。",
        "replies": 156,
        "views": 5678,
        "node": "分享创造",
    },
]


class V2EXFetcher:
    """Fetch V2EX share posts via RSSHub JSON endpoint."""

    def __init__(self):
        self.api_url = "https://rsshub.app/v2ex/go/share"
        self.node_url = "https://v2ex.com/go/"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_json(self) -> dict | None:
        """Fetch JSON from RSSHub with retry logic."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        response = requests.get(self.api_url, timeout=30, headers=headers)
        response.raise_for_status()
        return response.json()

    def _parse_post(self, post_data: dict) -> dict[str, Any]:
        """Parse post data from RSSHub response."""
        # RSSHub format varies, handle common patterns
        title = post_data.get("title") or post_data.get("name", "Unknown Post")

        # Get URL
        url = post_data.get("url") or post_data.get("link", "")
        if url and not url.startswith("http"):
            url = f"https://v2ex.com{url}"

        # Get author
        author = post_data.get("author") or post_data.get("user") or post_data.get("username", "Anonymous")

        # Get content/description
        content = (
            post_data.get("content")
            or post_data.get("description")
            or post_data.get("summary", "")
        )
        # Strip HTML tags if present
        import re
        content = re.sub(r"<[^>]+>", "", content)

        # Get timestamps
        created_at = post_data.get("created_at") or post_data.get("pubDate") or post_data.get("date", "")
        if isinstance(created_at, (int, float)):
            created_at = datetime.fromtimestamp(created_at).isoformat()

        # Get stats
        replies = post_data.get("replies") or post_data.get("reply_count", 0)
        views = post_data.get("views") or post_data.get("view_count", 0)

        # Get node
        node = post_data.get("node") or post_data.get("category") or post_data.get("tag", "分享")

        return {
            "title": title,
            "url": url or f"https://v2ex.com/t/{post_data.get('id', '')}",
            "author": author,
            "created_at": created_at,
            "content": content[:300] if len(content) > 300 else content,
            "replies": replies,
            "views": views,
            "node": node,
        }

    def fetch(self) -> list[dict[str, Any]]:
        """Fetch V2EX share posts from RSSHub."""
        logger.info("Starting V2EX fetch")

        try:
            data = self._fetch_json()

            if not data:
                logger.warning("Empty response from RSSHub, using mock data")
                return MOCK_V2EX_POSTS

            posts = []

            # Handle RSSHub JSON response format
            # Format: {"items": [...]} or direct list
            if isinstance(data, dict) and "items" in data:
                items = data["items"]
            elif isinstance(data, dict):
                # Try to find items list
                for key in ["items", "posts", "data", "results"]:
                    if key in data and isinstance(data[key], list):
                        items = data[key]
                        break
                else:
                    items = list(data.values())
            elif isinstance(data, list):
                items = data
            else:
                items = []

            for post_data in items[:10]:
                if isinstance(post_data, dict):
                    post = self._parse_post(post_data)
                    posts.append(post)

            if posts:
                logger.info(f"Fetched {len(posts)} V2EX posts")
                return posts[:5]  # Return top 5
            else:
                logger.warning("No posts parsed from RSSHub, using mock data")
                return MOCK_V2EX_POSTS

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch V2EX: {e}, using mock data")
            return MOCK_V2EX_POSTS
        except Exception as e:
            logger.error(f"Error parsing V2EX response: {e}, using mock data")
            return MOCK_V2EX_POSTS

    def to_json(self) -> str:
        """Return posts as JSON string."""
        import json
        return json.dumps(self.fetch(), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import json

    fetcher = V2EXFetcher()
    posts = fetcher.fetch()
    print(json.dumps(posts, indent=2, ensure_ascii=False))
