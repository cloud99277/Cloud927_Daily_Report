# Cloud927 AI Daily Briefing Generator v4.1

**个人决策参考系统** — 以 AI 科技为核心，辐射投融资/金融/国内热点/政策/社会事件。

> 目的：提升赚钱能力，需要行动指导。
> 阅读体验：快速扫描（2分钟）+ 关键话题深度洞察

---

## 🎯 v4.1 核心升级

| 维度 | v4.0 | v4.1 | 提升 |
|------|------|------|------|
| **数据源** | 29个 | 29个 | 优化板块 |
| **覆盖板块** | 6大板块 | 6大板块 | 调整聚焦 |
| **合规过滤** | 无 | 三版本 | 自动生成 |
| **洞察去重** | 无 | 历史追踪 | 避免重复 |
| **输出格式** | 两层阅读 | 两层阅读 | 决策友好 |

---

## 📊 六大板块覆盖

| 板块 | 定位 | 数据源数 | 核心价值 |
|------|------|---------|---------|
| **🤖 AI前沿** | 核心主线 | 10个 | 技术趋势 + 商业机会 |
| **💰 创业/投融资** | 钱往哪流 | 3个 | 融资动向 + 创业风向 |
| **📊 金融/宏观** | 大环境 | 5个 | 经济数据 + 市场信号 |
| **🇨🇳 中国国内热点** | 本土关注 | 5个 | 国内动态 + 社会热点 |
| **📜 科技政策** | 规则变化 | 3个 | 监管动向 + 政策影响 |
| **🌍 全球重大事件** | 黑天鹅 | 3个 | 地缘政治 + 社会事件 |

### v4.1 板块调整说明

- **删除**: Web3/Crypto 板块（市场关注度下降）
- **新增**: 中国国内热点板块（Top 5 热点，更贴近本土决策需求）

---

## 🏗️ 架构设计

### 双层 LLM 架构

```
第一层：Gemini Flash（预处理）
  ├─ 输入：原始新闻数据（标题+URL）
  ├─ 处理：摘要提取 + 分类标签 + 重要性初评
  └─ 输出：结构化数据（200字摘要 + 分类 + 分数）
  └─ 成本：低（~$0.01/天）

第二层：Claude Opus 4.5（洞察生成）
  ├─ 输入：预处理后的结构化数据
  ├─ 处理：跨源综合分析 + 深度洞察 + 行动建议
  └─ 输出：完整日报（快速扫描 + 深度洞察）
  └─ 成本：中（~$0.10-0.20/天）
```

### 数据流水线 (v4.1)

```
Fetch (29源并行)
  ↓
Deduplicate (跨源去重)
  ↓
Cluster (六大板块分类)
  ↓
Timeline Track (实体追踪)
  ↓
LLM Layer 1: Gemini Flash (预处理)
  ↓
Insight History Check (洞察去重)
  ↓
LLM Layer 2: Claude Opus (洞察生成)
  ↓
Compliance Filter (合规过滤)
  ↓
Save to Obsidian (三版本)
```

---

## 📋 日报内容架构

### 两层阅读结构

**第一层：快速扫描（2分钟）**
- 一句话核心信号
- 六大板块 Top 3 标题 + 重要性评级
- 今日行动清单（最多3条可执行建议）

**第二层：深度洞察（选读）**
- 每天 2-3 个最重要话题展开
- 结构：发生了什么 → 为什么重要 → 对你意味着什么 → 建议行动

---

## 🚀 快速开始

### 环境配置

```bash
# 克隆项目
git clone https://github.com/yourusername/Cloud927_Daily_Report.git
cd Cloud927_Daily_Report

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入：
# - GEMINI_API_KEY
# - ANTHROPIC_AUTH_TOKEN
# - OBSIDIAN_VAULT_PATH (你的 Obsidian 笔记路径)
```

### 运行

```bash
python main.py
```

日报自动保存到：
```
{OBSIDIAN_VAULT_PATH}/10_Daily_Reports/02_Daily_Reports/YYYY-MM/YYYY-MM-DD.md
```

---

## 📁 项目结构

```
Cloud927_Daily_Report/
├── main.py                          # 入口点
├── config.yaml                      # 配置文件（数据源、LLM、处理参数）
├── requirements.txt                 # 依赖
├── .env.example                     # 环境变量模板
│
├── src/
│   ├── models.py                    # 统一数据模型（NewsItem）
│   ├── pipeline.py                  # 数据流水线编排
│   │
│   ├── fetchers/                    # 29个数据源
│   │   ├── base_fetcher.py          # Fetcher基类
│   │   ├── hn_fetcher.py            # Hacker News
│   │   ├── github_fetcher.py        # GitHub Trending
│   │   ├── arxiv_fetcher.py         # ArXiv
│   │   ├── reddit_fetcher.py        # Reddit
│   │   ├── twitter_fetcher.py       # Twitter/X
│   │   ├── ai_news_fetcher.py       # AI官方博客
│   │   ├── hf_fetcher.py            # HuggingFace
│   │   ├── ph_fetcher.py            # Product Hunt
│   │   │
│   │   ├── news/                    # 新闻源
│   │   │   ├── base_rss_fetcher.py
│   │   │   ├── bbc_fetcher.py
│   │   │   ├── reuters_fetcher.py
│   │   │   ├── ap_news_fetcher.py
│   │   │   ├── ft_fetcher.py
│   │   │   ├── bloomberg_fetcher.py
│   │   │   └── ...
│   │   │
│   │   ├── crypto/                  # Web3/Crypto源
│   │   │   ├── coindesk_fetcher.py
│   │   │   ├── theblock_fetcher.py
│   │   │   ├── decrypt_fetcher.py
│   │   │   └── ...
│   │   │
│   │   ├── startup/                 # 创业/投融资源
│   │   │   ├── techcrunch_fetcher.py
│   │   │   ├── 36kr_fetcher.py
│   │   │   └── ...
│   │   │
│   │   ├── finance/                 # 金融/宏观源
│   │   │   ├── yahoo_finance_fetcher.py
│   │   │   └── ...
│   │   │
│   │   ├── policy/                  # 科技政策源
│   │   │   └── techpolicy_fetcher.py
│   │   │
│   │   └── china/                   # 中文源
│   │       ├── sina_fetcher.py
│   │       ├── caixin_fetcher.py
│   │       └── ...
│   │
│   ├── processor/                   # 数据处理
│   │   ├── deduplicator.py          # 跨源去重
│   │   ├── clustering.py            # 六大板块分类
│   │   └── timeline_tracker.py      # 实体追踪
│   │
│   ├── llm/                         # LLM抽象层
│   │   ├── base_client.py           # 基类
│   │   ├── gemini_client.py         # Gemini Flash
│   │   ├── claude_client.py         # Claude Opus
│   │   ├── openai_client.py         # GPT（备选）
│   │   └── factory.py               # 工厂函数
│   │
│   ├── storage/                     # 存储
│   │   └── obsidian_writer.py       # Obsidian集成
│   │
│   ├── generator_v3.py              # 日报生成器
│   ├── config.py                    # 配置加载
│   └── utils/
│       ├── logger.py                # 日志
│       └── ...
│
└── docs/
    └── CHANGELOG.md                 # 版本日志
```

---

## 🔧 配置说明

### config.yaml 核心配置

```yaml
# 数据源配置
fetchers:
  hn:
    enabled: true
    timeout: 10
    limit: 20

  # ... 其他28个源

# LLM配置
llm:
  preprocessor:
    provider: gemini
    model: gemini-2.0-flash
    api_key_env: GEMINI_API_KEY

  insight:
    provider: claude
    model: claude-opus-4-5
    api_key_env: ANTHROPIC_AUTH_TOKEN
    base_url: "https://code.newcli.com/claude/droid"  # 可选代理

# 处理参数
processor:
  max_workers: 12
  dedup_threshold: 0.85
  time_window_hours: 24
```

---

## 💡 核心特性

### 1. 统一数据模型

所有数据源输出统一的 `NewsItem` 对象：

```python
@dataclass
class NewsItem:
    title: str
    url: str
    source: str              # "hn", "github", "sina"
    timestamp: datetime
    content: str = ""        # 摘要
    score: float = 0         # 热度分数
    source_type: str = ""    # 对应六大板块
    language: str = "en"
    metadata: dict = field(default_factory=dict)
```

### 2. 跨源去重 + 聚类

- 多源报道同一事件时，合并元数据而非丢弃
- 记录"被N个源报道"作为重要性信号
- 自动分类到六大板块

### 3. 双层LLM优化

- **成本优化**：Gemini Flash 预处理（便宜快）
- **质量优化**：Claude Opus 洞察（深度强）
- **灵活切换**：修改 config.yaml 即可切换模型

### 4. 实体追踪

跟踪重要实体（公司、人物、事件）的演进：
- 新增实体
- 已有实体的更新
- 持续追踪的事件

### 5. 合规过滤 (v4.1 新增)

自动生成三个版本的日报：
- **原始版** (`_raw.md`)：完整内容，个人使用
- **公开版** (`_public.md`)：合规过滤后，可公开分享
- **合规报告** (`_compliance_report.md`)：详细记录所有修改

过滤规则：
- 🔴 **Red Rules**: 硬性阻断（加密货币、品牌诋毁、投资建议等）
- 🟠 **Orange Rules**: 软性重写（去金融化、宏观中性化）
- 🟡 **Yellow Rules**: 标注声明（AI生成声明、免责声明）

### 6. 洞察去重 (v4.1 新增)

轻量级历史追踪机制：
- 记录最近7天的深度洞察主题
- 生成日报时自动检查，避免重复分析
- 存储在 `data/insight_history.json`

---

## 📈 性能指标

| 指标 | 数值 |
|------|------|
| 数据源数 | 29个 |
| 平均抓取时间 | ~30秒（并行） |
| 去重效率 | 271 → 268 items |
| 日报生成时间 | ~2分钟 |
| 日报大小 | ~4000字 |
| 日均成本 | ~$0.15 |

---

## 🛠️ 技术栈

- **Python 3.12+**
- **google-genai** — Gemini Flash API
- **httpx** — HTTP客户端（支持代理）
- **beautifulsoup4** — HTML解析
- **tenacity** — 重试机制
- **pydantic** — 数据验证
- **python-dotenv** — 环境配置

---

## 🔐 安全性

- API key 存储在 `.env`（已加入 .gitignore）
- 支持代理服务（NewCLI等）
- 无本地数据库，所有数据临时处理
- 日报仅保存到本地 Obsidian

---

## 📝 版本历史

### v4.1 (2026-02-09)
- ✅ 板块调整：删除 Web3/Crypto，新增中国国内热点
- ✅ 合规过滤：自动生成三版本（原始/公开/合规报告）
- ✅ 洞察去重：轻量级历史追踪，避免重复分析
- ✅ 隐私保护：移除硬编码路径，完善 .gitignore

### v4.0 (2026-02-08)
- ✅ 数据源从8扩展到29
- ✅ 覆盖六大板块
- ✅ 双层LLM架构（Gemini + Claude）
- ✅ 跨源去重 + 聚类
- ✅ 两层阅读结构
- ✅ 实体追踪
- ✅ 统一数据模型

### v3.0 (2026-02-07)
- 初版v3架构

### v2.0 (2026-02-06)
- 8数据源 + 优化排版

---

## 🤝 贡献

欢迎提交 Issue 和 PR！

---

## 📄 许可证

MIT License

---

*Cloud927 — 帮你在噪音中找到信号*
