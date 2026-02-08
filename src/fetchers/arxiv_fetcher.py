"""ArXiv Paper Fetcher via API."""

import logging
import time
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class ArxivFetcher:
    """Fetch AI papers from ArXiv API."""

    ARXIV_API = "http://export.arxiv.org/api/query"

    # AI-related categories
    AI_CATEGORIES = [
        "cs.AI",  # Artificial Intelligence
        "cs.LG",  # Machine Learning
        "cs.CL",  # Computation and Language (NLP)
        "cs.NE",  # Neural and Evolutionary Computing
        "stat.ML",  # Machine Learning
    ]

    def __init__(self):
        self.source_name = "arXiv"

    def _parse_arxiv_date(self, date_str: str) -> int:
        """Parse ArXiv date format to timestamp."""
        if not date_str:
            return int(time.time())

        try:
            # ArXiv format: "2024-01-15T10:30:00Z"
            dt = datetime.strptime(date_str.replace("Z", "+00:00"), "%Y-%m-%dT%H:%M:%S%z")
            return int(dt.timestamp())
        except ValueError:
            return int(time.time())

    def _parse_entry(self, entry: Any) -> dict:
        """Parse individual ArXiv entry."""
        import xml.etree.ElementTree as ET

        # Handle both BeautifulSoup and ElementTree
        if hasattr(entry, 'find'):
            # BeautifulSoup
            title = entry.find("title")
            title_text = title.get_text().replace("\n", " ").strip() if title else "No title"

            summary = entry.find("summary")
            abstract = summary.get_text().replace("\n", " ").strip() if summary else ""

            link = entry.find("link")
            pdf_url = ""
            html_url = ""
            if link:
                href = link.get("href", "")
                if "pdf" in href:
                    pdf_url = href
                else:
                    html_url = href

            # Alternative links
            for alt_link in entry.find_all("link", rel="alternate"):
                href = alt_link.get("href", "")
                if "pdf" in href:
                    pdf_url = href
                elif "text/html" in href:
                    html_url = href

            # Published date
            published = entry.find("published")
            timestamp = self._parse_arxiv_date(published.get_text()) if published else int(time.time())

            # Authors
            authors = []
            for author in entry.find_all("author"):
                name = author.find("name")
                if name:
                    authors.append(name.get_text())

            # Categories
            categories = []
            for cat in entry.find_all("category"):
                cat_term = cat.get("term")
                if cat_term:
                    categories.append(cat_term)

            # DOI if available
            doi = ""
            for id_link in entry.find_all("link", rel="self"):
                href = id_link.get("href", "")
                if "doi.org" in href:
                    doi = href

            return {
                "title": title_text,
                "abstract": abstract[:500] if len(abstract) > 500 else abstract,
                "url": html_url or pdf_url,
                "pdf_url": pdf_url,
                "authors": authors[:5],  # Limit to 5 authors
                "categories": categories,
                "timestamp": timestamp,
                "published_at": published.get_text() if published else "",
                "doi": doi,
                "source": self.source_name,
                "source_type": "paper",
            }
        else:
            # ElementTree
            return {
                "title": entry.findtext("title", "No title").replace("\n", " ").strip(),
                "abstract": entry.findtext("summary", "").replace("\n", " ").strip()[:500],
                "url": "",
                "authors": [a.findtext("name") for a in entry.findall("author")[:5]],
                "categories": [c.get("term") for c in entry.findall("category")],
                "timestamp": int(time.time()),
                "source": self.source_name,
            }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _query_arxiv(
        self,
        categories: list[str] | None = None,
        max_results: int = 50,
        sort_by: str = "submittedDate",
        sort_order: str = "descending"
    ) -> str:
        """Query ArXiv API."""
        if categories is None:
            categories = self.AI_CATEGORIES

        # Build query
        cat_query = " OR ".join(f"cat:{cat}" for cat in categories)
        query = f"({cat_query}) AND (ti:AI OR ti:\"machine learning\" OR ti:NLP OR ti:\"deep learning\" OR abs:AI OR abs:\"machine learning\")"

        params = {
            "search_query": query,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
            "start": 0,
        }

        url = f"{self.ARXIV_API}?{urlencode(params)}"
        logger.debug(f"ArXiv query URL: {url[:100]}...")

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Cloud927/3.0)",
            "Accept": "application/atom+xml",
        }

        response = requests.get(url, timeout=60, headers=headers)
        response.raise_for_status()
        return response.text

    def fetch(
        self,
        categories: list[str] | None = None,
        max_results: int = 30,
        days_back: int = 7
    ) -> list[dict]:
        """
        Fetch AI papers from ArXiv.

        Args:
            categories: ArXiv categories to query
            max_results: Maximum number of results
            days_back: Only fetch papers from last N days

        Returns:
            List of paper dictionaries
        """
        logger.info(f"Fetching up to {max_results} papers from ArXiv")

        try:
            xml_content = self._query_arxiv(categories=categories, max_results=max_results)

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(xml_content, "xml")
            entries = soup.find_all("entry")

            papers = []
            cutoff_time = int(time.time()) - (days_back * 86400)

            for entry in entries:
                paper = self._parse_entry(entry)

                # Apply days filter
                if paper["timestamp"] < cutoff_time:
                    continue

                papers.append(paper)

            logger.info(f"Fetched {len(papers)} papers from ArXiv (last {days_back} days)")
            return papers

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch from ArXiv: {e}")
            return self._get_mock_papers()

    def _get_mock_papers(self) -> list[dict]:
        """Return mock papers when fetch fails."""
        logger.warning("Using mock data for ArXiv")
        return [{
            "title": "[模拟论文] AI领域的最新研究进展",
            "abstract": "这是模拟数据，当ArXiv无法访问时使用。",
            "url": "https://arxiv.org/abs/2401.00001",
            "authors": ["Author One", "Author Two"],
            "categories": ["cs.AI"],
            "timestamp": int(time.time()),
            "source": self.source_name,
            "source_type": "paper",
        }]


if __name__ == "__main__":
    fetcher = ArxivFetcher()

    # Fetch papers
    papers = fetcher.fetch(max_results=10, days_back=14)

    print(f"Fetched {len(papers)} papers from arXiv:\n")
    for paper in papers[:5]:
        print(f"- {paper['title']}")
        print(f"  Authors: {', '.join(paper['authors'][:3])}")
        print(f"  Categories: {', '.join(paper['categories'])}")
        print(f"  URL: {paper['url']}")
        print()
