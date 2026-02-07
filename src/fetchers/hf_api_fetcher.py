"""HuggingFace API Fetcher using JSON API instead of HTML scraping."""

import logging
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Mock data as fallback
MOCK_PAPERS = [
    {
        "name": "Llama 3: The Future of Open LLMs",
        "abstract": "This paper introduces Llama 3, a state-of-the-art open language model with improved reasoning and multilingual capabilities.",
        "url": "https://huggingface.co/papers/llama3",
        "tags": ["llm", "transformer", "multilingual"],
    },
    {
        "name": "Stable Diffusion 3: Improved Text-to-Image",
        "abstract": "A novel diffusion model architecture that significantly improves text understanding and image quality.",
        "url": "https://huggingface.co/papers/sd3",
        "tags": ["diffusion", "vision", "multimodal"],
    },
    {
        "name": "Efficient Vision Transformers Survey",
        "abstract": "A comprehensive survey of methods to improve the efficiency of Vision Transformers.",
        "url": "https://huggingface.co/papers/efficient-vits",
        "tags": ["vision", "efficiency", "survey"],
    },
]


class HuggingFaceAPIFetcher:
    """Fetch daily papers from HuggingFace JSON API."""

    def __init__(self):
        self.api_url = "https://huggingface.co/api/daily_papers"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_json(self) -> dict | None:
        """Fetch JSON from API with retry logic."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        response = requests.get(self.api_url, timeout=30, headers=headers)
        response.raise_for_status()
        return response.json()

    def _parse_paper(self, paper_data: dict) -> dict[str, Any]:
        """Parse paper data from API response."""
        # API returns papers in different formats, handle common patterns
        name = paper_data.get("title") or paper_data.get("name", "Unknown Paper")

        # Get abstract - might be in different fields
        abstract = (
            paper_data.get("abstract")
            or paper_data.get("description")
            or paper_data.get("summary", "No abstract available")
        )

        # Get URL - might need construction
        paper_id = paper_data.get("id") or paper_data.get("paperId")
        if paper_id:
            url = f"https://huggingface.co/papers/{paper_id}"
        else:
            url = paper_data.get("url", "https://huggingface.co/papers")

        # Get tags
        tags = paper_data.get("tags", [])
        if isinstance(tags, str):
            import json
            try:
                tags = json.loads(tags)
            except (json.JSONDecodeError, TypeError):
                tags = [tags] if tags else []

        return {
            "name": name,
            "abstract": abstract[:500] if len(abstract) > 500 else abstract,
            "url": url,
            "tags": tags[:5],  # Limit to 5 tags
        }

    def fetch(self) -> list[dict[str, Any]]:
        """Fetch daily papers from HuggingFace API."""
        logger.info("Starting HF API papers fetch")

        try:
            data = self._fetch_json()

            if not data:
                logger.warning("Empty response from HF API, using mock data")
                return MOCK_PAPERS

            papers = []

            # Handle different API response formats
            # Format 1: {"papers": [...]} or {"daily_papers": [...]}
            if isinstance(data, dict):
                for key in ["papers", "daily_papers", "items", "results"]:
                    if key in data and isinstance(data[key], list):
                        paper_list = data[key]
                        break
                else:
                    # Try to find any list in the response
                    paper_list = []
                    for value in data.values():
                        if isinstance(value, list):
                            paper_list = value
                            break
            elif isinstance(data, list):
                paper_list = data
            else:
                paper_list = []

            for paper_data in paper_list[:5]:
                if isinstance(paper_data, dict):
                    paper = self._parse_paper(paper_data)
                    papers.append(paper)

            if papers:
                logger.info(f"Fetched {len(papers)} papers from HF API")
                return papers[:3]  # Return top 3
            else:
                logger.warning("No papers parsed from HF API, using mock data")
                return MOCK_PAPERS

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch from HF API: {e}, using mock data")
            return MOCK_PAPERS
        except Exception as e:
            logger.error(f"Error parsing HF API response: {e}, using mock data")
            return MOCK_PAPERS

    def to_json(self) -> str:
        """Return papers as JSON string."""
        import json
        return json.dumps(self.fetch(), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import json

    fetcher = HuggingFaceAPIFetcher()
    papers = fetcher.fetch()
    print(json.dumps(papers, indent=2, ensure_ascii=False))
