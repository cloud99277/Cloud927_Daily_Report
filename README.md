# Cloud927 Daily Report Generator

Automated daily tech report generator that fetches news from Hacker News, GitHub Trending, and HuggingFace, then generates a structured Chinese report using Gemini API.

## Features

- **Multi-source aggregation**: HN, GitHub Trending, HuggingFace papers
- **Parallel fetching**: ThreadPoolExecutor for concurrent API calls
- **LLM-powered summarization**: Gemini 2.0 Flash for report generation
- **Obsidian integration**: Auto-saves reports to your vault
- **Retry logic**: Exponential backoff for resilience

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY and OBSIDIAN_VAULT_PATH
```

## Usage

```bash
./venv/bin/python main.py
```

Reports are saved to `OBSIDIAN_VAULT_PATH/YYYY-MM-DD.md`.

## Project Structure

```
├── main.py                 # Entry point
├── src/
│   ├── fetchers/           # Data sources (HN, GitHub, HF)
│   ├── generator.py        # Gemini LLM client
│   ├── storage.py         # Obsidian writer
│   └── utils/             # Logger, cleaner
├── .env.example            # Environment template
└── requirements.txt       # Dependencies
```

## Tech Stack

- Python 3.12+
- google-generativeai (Gemini API)
- feedparser (RSS)
- tenacity (Retry logic)
- python-dotenv (Config)
