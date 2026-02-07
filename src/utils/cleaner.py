"""Text cleaning utilities."""

import re
from html import unescape


def strip_html(html: str) -> str:
    """Remove HTML tags from text."""
    if not html:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)
    # Unescape HTML entities
    text = unescape(text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def truncate(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, preserving word boundaries."""
    if not text or len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # Try to cut at word boundary
    last_space = truncated.rfind(' ')
    if last_space > max_chars * 0.8:
        truncated = truncated[:last_space]
    return truncated.strip()


def sanitize_text(text: str, max_chars: int = 1000) -> str:
    """Clean and truncate text for LLM consumption."""
    if not text:
        return ""
    cleaned = strip_html(text)
    return truncate(cleaned, max_chars)
