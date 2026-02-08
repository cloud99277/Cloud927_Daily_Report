"""Twitter/X AI Fetcher via Nitter RSS."""

from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup

from src.fetchers.base_fetcher import BaseFetcher
from src.models import NewsItem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TwitterFetcher(BaseFetcher):
    """Fetch AI-related tweets via Nitter RSS."""

    NITTER_INSTANCES = [
        "nitter.net",
        "nitter.privacydev.net",
        "nitter.poast.org",
    ]

    AI_ACCOUNTS = [
        "elonmusk",
        "sama",
        "AndrewYNg",
        "JeffDean",
        "ylecun",
    ]

    def __init__(self):
        super().__init__(source_name="twitter", source_type="social", language="en")
        self.nitter_instance = self.NITTER_INSTANCES[0]

    def _fetch_raw(self) -> list[dict]:
        """Fetch tweets from all AI accounts via Nitter RSS."""
        all_tweets: list[dict] = []
        for username in self.AI_ACCOUNTS:
            tweets = self._fetch_user_rss(username)
            all_tweets.extend(tweets)
        all_tweets.sort(key=lambda x: x.get("pub_date", ""), reverse=True)
        return all_tweets[:50]

    def _fetch_user_rss(self, username: str) -> list[dict]:
        """Fetch RSS feed for a single user."""
        url = f"https://{self.nitter_instance}/{username}/rss"
        try:
            resp = self._make_request(url)
            soup = BeautifulSoup(resp.text, "xml")
            items = []
            for item in soup.find_all("item")[:5]:
                title_tag = item.find("title")
                link_tag = item.find("link")
                desc_tag = item.find("description")
                pub_tag = item.find("pubDate")

                items.append({
                    "title": title_tag.get_text() if title_tag else "",
                    "url": link_tag.get_text() if link_tag else "",
                    "description": desc_tag.get_text() if desc_tag else "",
                    "pub_date": pub_tag.get_text() if pub_tag else "",
                    "username": username,
                })
            return items
        except Exception as e:
            logger.debug(f"Failed to fetch @{username}: {e}")
            return []

    def _parse_item(self, raw_item: Any) -> NewsItem:
        """Convert tweet dict into NewsItem."""
        tweet = raw_item
        username = tweet.get("username", "")
        title_text = tweet.get("title", "")

        content = self._clean_html(tweet.get("description", ""))
        timestamp = self._parse_date(tweet.get("pub_date", ""))

        return NewsItem(
            title=f"@{username}: {title_text}" if username else title_text,
            url=tweet.get("url", ""),
            source=self.source_name,
            timestamp=timestamp,
            content=content[:300],
            source_type=self.source_type,
            language=self.language,
            metadata={"author": username},
        )
