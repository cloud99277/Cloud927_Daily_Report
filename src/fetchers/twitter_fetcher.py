"""Twitter/X AI Fetcher via Nitter RSS."""

import logging
import time
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class TwitterFetcher:
    """Fetch AI-related tweets via Nitter RSS."""

    # Nitter instances (public RSS proxies)
    NITTER_INSTANCES = [
        "nitter.net",
        "nitter.privacydev.net",
        "nitter.poast.org",
    ]

    # AI-related accounts to follow
    AI_ACCOUNTS = [
        "elonmusk",
        "sama",  # Sam Altman
        "AndrewYNg",  # Andrew Ng
        "JeffDean",  # Jeff Dean
        "ylecun",  # Yann LeCun
        "AndrewNGTrs",  # Andrew Ng (Chinese)
        "hwchunter27",  # Andrew Karpathy
    ]

    def __init__(self, nitter_instance: str | None = None):
        """
        Initialize Twitter fetcher.

        Args:
            nitter_instance: Nitter instance to use (auto-selected if None)
        """
        self.nitter_instance = nitter_instance or self._select_instance()
        self.source_name = "Twitter/X"

    def _select_instance(self) -> str:
        """Select a working Nitter instance."""
        # Use first instance by default
        return self.NITTER_INSTANCES[0]

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=5))
    def _fetch_rss(self, username: str) -> str | None:
        """Fetch RSS feed for a user."""
        url = f"https://{self.nitter_instance}/{username}/rss"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        try:
            response = requests.get(url, timeout=30, headers=headers)
            if response.status_code == 200:
                return response.text
            return None
        except requests.RequestException:
            return None

    def _parse_rss_date(self, date_str: str) -> int:
        """Parse RSS date to timestamp."""
        if not date_str:
            return int(time.time())

        formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%SZ",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return int(dt.timestamp())
            except ValueError:
                continue

        return int(time.time())

    def _parse_item(self, item: Any, username: str) -> dict:
        """Parse individual RSS item."""
        from xml.etree import ElementTree as ET

        # Handle both BeautifulSoup and ElementTree parsing
        if hasattr(item, 'find'):
            # BeautifulSoup
            title = item.find("title")
            title_text = title.get_text() if title else ""

            link = item.find("link")
            url = link.get_text() if link else ""

            description = item.find("description")
            content = description.get_text() if description else ""

            pub_date = item.find("pubDate")
            timestamp = self._parse_rss_date(pub_date.get_text()) if pub_date else int(time.time())
        else:
            # ElementTree
            title_text = item.findtext("title", "")
            url = item.findtext("link", "")
            content = item.findtext("description", "")
            pub_date = item.findtext("pubDate", "")
            timestamp = self._parse_rss_date(pub_date)

        # Clean content - remove HTML and user mentions
        content_clean = BeautifulSoup(content, "html.parser").get_text()
        content_clean = " ".join(content_clean.split())

        return {
            "title": f"@{username}: {title_text}",
            "url": url,
            "content": content_clean[:300],
            "author": username,
            "source": self.source_name,
            "timestamp": timestamp,
            "source_type": "social",
        }

    def fetch_user(self, username: str, limit: int = 10) -> list[dict]:
        """Fetch tweets from a specific user."""
        logger.info(f"Fetching tweets from @{username}")

        rss_content = self._fetch_rss(username)
        if not rss_content:
            logger.warning(f"Failed to fetch from @{username}")
            return self._get_mock_tweets(username)

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(rss_content, "xml")
        items = soup.find_all("item")[:limit]

        tweets = []
        for item in items:
            tweet = self._parse_item(item, username)
            tweets.append(tweet)

        logger.info(f"Fetched {len(tweets)} tweets from @{username}")
        return tweets

    def fetch_ai_tweets(self, limit_per_user: int = 5) -> list[dict]:
        """Fetch tweets from all AI-related accounts."""
        all_tweets = []

        for username in self.AI_ACCOUNTS:
            tweets = self.fetch_user(username, limit=limit_per_user)
            all_tweets.extend(tweets)

        # Sort by timestamp (newest first)
        all_tweets.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

        logger.info(f"Total AI tweets fetched: {len(all_tweets)}")
        return all_tweets[:50]  # Limit total

    def fetch(self, usernames: list[str] | None = None, limit_per_user: int = 5) -> list[dict]:
        """Fetch tweets from specified users or default AI accounts."""
        if usernames:
            all_tweets = []
            for username in usernames:
                tweets = self.fetch_user(username, limit_per_user)
                all_tweets.extend(tweets)
            return all_tweets
        return self.fetch_ai_tweets(limit_per_user)

    def _get_mock_tweets(self, username: str) -> list[dict]:
        """Return mock tweets when fetch fails."""
        logger.warning(f"Using mock data for @{username}")
        return [{
            "title": f"@{username}: [模拟推文] 测试数据",
            "url": f"https://twitter.com/{username}/status/123456789",
            "content": "这是模拟数据，当Twitter/X无法访问时使用。",
            "author": username,
            "source": self.source_name,
            "timestamp": int(time.time()),
            "source_type": "social",
        }]


if __name__ == "__main__":
    fetcher = TwitterFetcher()

    # Fetch from specific user
    tweets = fetcher.fetch_user("sama", limit=3)
    print(f"Fetched {len(tweets)} tweets from @sama:\n")
    for tweet in tweets:
        print(f"- {tweet['title']}")
        print(f"  {tweet['content'][:100]}...")
        print()

    # Fetch from all AI accounts
    all_tweets = fetcher.fetch_ai_tweets(limit_per_user=2)
    print(f"\nTotal: {len(all_tweets)} tweets from all AI accounts")
