# Cloud927 Daily Report Generator

Automated daily tech report generator that fetches news from multiple sources and generates deep analysis using Gemini API.

## Chief Editor - 从"搬运工"到"首席编辑"

**Cloud927** 现在是一位 Hikvision 资深方案架构师，专注于供应链 AI 领域。

## Features

- **Multi-source aggregation**: HN, GitHub Trending, HuggingFace Papers, V2EX, Show HN
- **Deep content extraction**: GitHub README + HN blog first paragraphs
- **Chief Editor Persona**: 三支柱分析 (供应链自动化 / 个人AI Agent / Web3财富)
- **Parallel fetching**: ThreadPoolExecutor for concurrent API calls
- **LLM-powered analysis**: Gemini 2.0 Flash for structured reports
- **Obsidian integration**: Auto-saves to monthly subfolders
- **Retry logic**: Exponential backoff for resilience

## Data Sources

| Source | Description |
|--------|-------------|
| Hacker News | Top stories (24h filter) |
| Show HN | New product launches |
| GitHub Trending | Popular repos + README |
| HuggingFace | Daily papers (JSON API) |
| V2EX | Chinese developer ecosystem |

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

Reports are saved to:
```
OBSIDIAN_VAULT_PATH/{MM}_Daily_Reports/YYYY-MM/YYYY-MM-DD.md
```

## Output Format

```markdown
# 2026-02-08 Cloud927 Daily Insight

## 🎯 Executive Summary
## 🚀 Major Developments (with Cloud927 Reflection)
## 🛠️ Engineering & Tools
## 🔬 Research & Innovation
## 🇨🇳 Chinese Tech Landscape
## 💡 Cloud927 Reflection (我的洞察)
```

## Project Structure

```
├── main.py                 # Entry point
├── src/
│   ├── fetchers/           # Data sources
│   │   ├── hn_fetcher.py       # HN + excerpt extraction
│   │   ├── hn_show_fetcher.py  # Show HN
│   │   ├── github_fetcher.py   # GitHub + README
│   │   ├── hf_fetcher.py       # HuggingFace HTML
│   │   ├── hf_api_fetcher.py   # HuggingFace API
│   │   └── v2ex_fetcher.py     # V2EX
│   ├── generator.py        # Chief Editor LLM client
│   ├── storage.py          # Obsidian writer + monthly folders
│   └── utils/              # Logger, cleaner
├── .env.example            # Environment template
└── requirements.txt        # Dependencies
```

## Tech Stack

- Python 3.12+
- google-genai (Gemini API)
- beautifulsoup4 (HTML parsing)
- tenacity (Retry logic)
- python-dotenv (Config)

## Cloud927 Reflection Framework

每个主要技术信号都会从三个维度分析：

1. **Supply Chain Automation** - 供应链自动化应用
2. **Personal AI Agent** - 个人AI助手开发
3. **Web3 Wealth** - Web3财富机会
