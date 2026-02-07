# Cloud927 Daily Report - 项目经验与错误总结

## 项目概述
自动化技术日报生成器，从 HN/GitHub/HuggingFace 抓取数据，使用 Gemini LLM 生成中文日报并保存到 Obsidian。

## 关键错误与解决方案

### 1. .env 配置格式错误
**错误**: `.env` 第一行只有 API Key 值，缺少 `GEMINI_API_KEY=` 前缀
```
# 错误
AIzaSyDTv8g8L80yN-04xtow3zCLdFwcPmZQlkE
# 正确
GEMINI_API_KEY=AIzaSyDTv8g8L80yN-04xtow3zCLdFwcPmZQlkE
```
**解决**: 补全 key=value 格式

### 2. google-generativeai API 变更
**错误**: 使用了已弃用的 `from google import genai`
```
from google import genai  # 错误
import google.generativeai as genai  # 正确
```
**解决**: 使用 `google.generativeai` 包，正确 API:
- `genai.configure(api_key=...)`
- `genai.GenerativeModel(model_name, system_instruction=...)`
- `model.generate_content(contents=[...])`

### 3. Gemini 模型名称错误
**错误**: `gemini-2.0-flash-exp` 不存在
```
# 可用模型列表
models/gemini-2.0-flash
models/gemini-2.5-flash
models/gemini-1.5-pro
```
**解决**: 使用 `gemini-2.0-flash`

### 4. system_instruction 位置错误
**错误**: 放在 `generation_config` 中
```python
# 错误
response = client.generate_content(
    contents=[prompt],
    generation_config={"system_instruction": ...}  # 不支持
)
# 正确
model = genai.GenerativeModel(
    "gemini-2.0-flash",
    system_instruction=SYSTEM_PROMPT
)
response = model.generate_content(contents=[prompt])
```

### 5. logger 未定义错误
**错误**: 函数中直接使用 `logger` 但未定义
```python
# 错误
def fetch_all_data_parallel():
    logger.info("...")  # NameError

# 解决: 在函数内创建 logger
from src.utils.logger import setup_logger
logger = setup_logger("fetcher")
```

### 6. as_completed 使用错误
**错误**: 直接遍历 dict
```python
# 错误
for key, future in as_completed(futures):  # futures 是 dict

# 正确
for future in as_completed(futures.values()):
```

### 7. feedparser timeout 参数
**错误**: `feedparser.parse(url, timeout=30)` 不支持 timeout
```
parse() got an unexpected keyword argument 'timeout'
```
**解决**: 使用 `requests` 手动获取后 parse

### 8. RSS 依赖不稳定 → 改为 HTML 爬取
**问题**: feedparser 依赖的 RSSHub 服务不稳定，经常返回 503 错误
**解决**: 使用 `requests + BeautifulSoup` 直接爬取原始 HTML
```python
# 替换 feedparser
response = requests.get(url, headers={"User-Agent": "..."})
soup = BeautifulSoup(response.text, "html.parser")
articles = soup.select("article.Box-row")  # CSS 选择器
```
**经验**:
- RSS 服务是第三方封装，可能失效或限流
- 直接爬取 HTML 更稳定，但需要维护选择器
- 建议同时保留 mock 数据作为 fallback

### 9. requirements.txt 同步
**错误**: 修改代码后忘记更新依赖声明
```
# 旧
feedparser
# 新
beautifulsoup4
```
**解决**: 每次修改依赖时同步更新 requirements.txt

### 10. HN 24h 新鲜度过滤
**需求**: 只获取最近 24 小时内的热门故事
**实现**:
```python
def _is_recent(self, story_time: int, max_age_seconds: int = 86400) -> bool:
    current_time = int(time.time())
    return (current_time - story_time) <= max_age_seconds
```
**经验**: 数据过滤应该在 fetch 层完成，减少 LLM 处理噪音

## 架构经验

### 成功的模式
1. **ETL 架构清晰**: Extract -> Transform -> Generate -> Load
2. **并行抓取**: ThreadPoolExecutor 提升效率
3. **重试机制**: tenacity 指数退避
4. **环境隔离**: venv + dotenv

### 待改进 (已解决部分)
1. ~~GitHub/HuggingFace RSS 网络不稳定~~ ✅ 已改为 HTML 爬取
2. ~~缺少 GitHub API 直接调用作为 fallback~~ ✅ 已添加 mock 数据 fallback
3. 日志轮转可优化
4. 未来可能需要添加请求缓存避免重复爬取
5. HTML 选择器可能需要随网站改版更新

## 依赖版本
```
google-generativeai==0.8.6
beautifulsoup4==4.12.3
requests==2.32.5
tenacity==9.1.4
python-dotenv==1.2.1
```
**注意**: `feedparser` 已移除，改为 `beautifulsoup4`

## 运行命令
```bash
./venv/bin/python main.py
```

---
生成时间: 2026-02-08
更新时间: 2026-02-08 (Chief Editor 升级)

---

# Cloud927 Chief Editor 升级 (2026-02-08)

## 新增数据源

### 1. HuggingFace API Fetcher
- **文件**: `src/fetchers/hf_api_fetcher.py`
- **API**: `https://huggingface.co/api/daily_papers`
- **优势**: JSON API 比 HTML 爬取更稳定

### 2. V2EX Fetcher
- **文件**: `src/fetchers/v2ex_fetcher.py`
- **源**: RSSHub `https://rsshub.app/v2ex/go/share`
- **作用**: 捕获中国开发者生态趋势

### 3. Show HN Fetcher
- **文件**: `src/fetchers/hn_show_fetcher.py`
- **源**: `https://news.ycombinator.com/show`
- **作用**: 专门获取新产品发布

## 深度内容提取

### GitHub README 提取
```python
def fetch_readme(self, owner: str, repo: str) -> str:
    # 获取原始 README.md (前 1000 字符)
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
```

### HN 博客首段提取
```python
def _fetch_first_paragraph(self, url: str) -> str:
    # 解析 HTML，提取第一个有意义的段落
```

## Chief Editor Persona

### 角色定义
```
You are Cloud927, a Senior Solution Architect at Hikvision
with a focus on Supply Chain AI.
```

### 强制输出结构
```markdown
## 🚀 Major Developments
- **[Title](url)**: Key insight
  - **Excerpt**: [README/首段]
  - **Cloud927 Reflection (我的洞察)**:
    1. **Supply Chain Automation**: [...]
    2. **Personal AI Agent**: [...]
    3. **Web3 Wealth**: [...]

## 💡 Cloud927 Reflection (Closing Lens)
80+ words connecting all topics
```

## 月度子文件夹组织
```
Obsidian/
└── 02_Daily_Reports/
    └── 2026-02/
        ├── 2026-02-07.md
        └── 2026-02-08.md
```

## 依赖更新
```
google-genai  # 已迁移
beautifulsoup4
requests
tenacity
python-dotenv
python-dateutil
```

## 运行
```bash
./venv/bin/python main.py
```

---

## Chief Editor 升级经验总结 (2026-02-08)

### 1. Agent Teams 协作模式

使用多 agent 并行工作，效率提升显著：
- **fetcher-agent**: 3 个新 fetcher (HF API, V2EX, Show HN)
- **content-agent**: README + 首段落深度提取
- **prompt-engineer**: Chief Editor Persona + 三支柱框架
- **backend-agent**: 月度文件夹 + google-genai 迁移

### 2. Prompt Engineering 经验

**有效的 Persona 定义**:
```
You are Cloud927, a Senior Solution Architect at Hikvision
with a focus on Supply Chain AI.
```

**强制结构化输出**:
- 每个 Major item 必须有 Reflection
- 三支柱维度防止 shallow 分析
- Closing Lens 80+ 字保证深度

### 3. 数据质量影响输出

| 数据字段 | LLM 输出质量 |
|---------|-------------|
| 仅标题 | 浅薄 summary |
| 标题 + README 摘要 | 深度技术分析 |
| 三支柱框架引导 | 结构化洞察 |

### 4. 依赖版本坑

```bash
# google-generativeai (旧) → google-genai (新)
pip uninstall google-generativeai
pip install google-genai
```

新 API:
```python
from google import genai
client = genai.Client(api_key=...)
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[prompt],
    config={"system_instruction": ...}
)
```

### 5. 成本记录

| 指标 | 数值 |
|-----|------|
| 总成本 | $4.24 |
| 耗时 | 27m 58s API |
| 代码变更 | +1142 / -189 行 |

### 6. Mock 数据策略

新 fetcher 必须有 mock fallback:
```python
MOCK_DATA = [...]

def fetch(self):
    try:
        return self._fetch_api()
    except Exception as e:
        logger.warning(f"API failed: {e}, using mock")
        return MOCK_DATA
```

### 7. RSSHub 稳定性问题

V2EX fetcher 依赖 RSSHub，可能失败。经验：
- 保留 mock 数据
- 添加重试逻辑
- 考虑直接爬取 V2EX HTML 作为备选

### 8. 文件路径迁移

旧: `OBSIDIAN_VAULT_PATH/YYYY-MM-DD.md`
新: `OBSIDIAN_VAULT_PATH/{MM}_Daily_Reports/YYYY-MM/YYYY-MM-DD.md`

迁移时需要兼容旧路径或手动迁移。

---

**经验**: 数据质量 × Prompt 工程 = 高质量输出

---

# Cloud927 v2.0 优化升级 (2026-02-08)

## 新增3个高价值数据源

### 1. AI News Fetcher (官方博客)
| 来源 | URL | 类型 |
|------|-----|------|
| OpenAI | openai.com/blog/ | HTML |
| Anthropic | anthropic.com/news | HTML |
| Google DeepMind | deepmind.google/blog | HTML |
| Meta AI | ai.meta.com/blog | HTML |

**价值**: 获取第一手 AI 模型/产品发布信息

### 2. Product Hunt Fetcher (AI新品雷达)
- URL: producthunt.com/topics/ai
- 类型: HTML
- 价值: 发现最新的 AI 产品发布

### 3. Reddit AI Fetcher (社区深度讨论)
- 子版: r/LocalLLaMA, r/Artificial, r/MachineLearning
- API: reddit.com/{subreddit}/top.json
- 价值: 获取社区对 AI 技术的深度讨论

## v2.0 排版优化

### 设计理念
- **Less is More**: 只选 5-8 条最有价值的信号
- **表格优先**: 可扫描性 > 深度阅读
- **结构化洞察**: 概览表格 + 深度分析 + 行动建议

### v2.0 输出结构

```markdown
# 🤖 {date} AI Daily Briefing

> **核心发现一句话** - 一句话概括最重要信号

---

### 📊 信号强度概览
| 领域 | 热度 | 重要发现 |
|------|------|----------|
| AI模型 | 🔥🔥🔥 | xxx |
| 开源工具 | 🔥🔥 | xxx |

---

## 🚨 Top Signal (必读)
> **重要性**: ⭐⭐⭐⭐⭐ | **来源**: xxx

**[标题](url)**
- 关键洞察
- 商业影响

### Cloud927 深度解读
1. **供应链自动化** 💎
2. **个人AI Agent** 🤖
3. **Web3财富机会** 🪙

---

## 🛠️ 工程实践 (表格)
## 🔬 研究前沿 (表格)
## 🆕 产品雷达 (表格)
## 💬 社区声音
## 🇨🇳 国内动态

## 🎯 Cloud927 洞察
> **趋势判断**: 100+ words

> **行动建议**:
> - [立即可做]
> - [短期规划]
> - [长期观察]
```

### v2.0 vs v1.0 对比

| 维度 | v1.0 | v2.0 |
|------|------|------|
| 数据源 | 5个 | 8个 |
| 输出格式 | 纯文本 | 表格+结构化 |
| 信息密度 | 中 | 高 |
| 可扫描性 | 低 | 高 |
| 行动建议 | 无 | 3档建议 |

## 技术实现

### v2.0 主函数并行抓取
```python
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {
        "hn": executor.submit(fetch_hn_data),
        "gh": executor.submit(fetch_github_data),
        "hf": executor.submit(fetch_hf_data),
        "ai_news": executor.submit(fetch_ai_news_data),
        "ph": executor.submit(fetch_ph_data),
        "reddit": executor.submit(fetch_reddit_data),
        "v2ex": executor.submit(fetch_v2ex_data),
        "hn_show": executor.submit(fetch_hn_show_data),
    }
```

### v2.0 输出格式器
```python
def _format_item(self, item: dict, item_type: str) -> str:
    """表格化格式化每个数据项"""
    # 支持 8 种数据源类型格式化
```

## v2.0 关键改进

### 1. 数据源扩展 (5→8)
```
+ AI News (官方博客)
+ Product Hunt (新品雷达)
+ Reddit (社区讨论)
```

### 2. 排版优化
```
- 纯文本列表
+ 表格化概览
+ 信号强度可视化
+ 行动建议分层
```

### 3. 信息密度提升
- 概览表格: 一眼看清所有信号
- Top Signal: 深度三支柱分析
- 行动建议: 可执行的下一步

## 成本与效率

| 指标 | v1.0 | v2.0 |
|------|------|------|
| 数据源 | 5 | 8 |
| 执行时间 | ~60s | ~90s |
| 输出长度 | ~1500字 | ~2000字 |
| 信息密度 | 中 | 高 |

## v2.0 经验总结

### 1. 数据源选择原则
- **官方第一手**: AI News > HN > Reddit
- **深度讨论**: Reddit > HN > V2EX
- **新品发现**: Product Hunt > Show HN

### 2. 排版设计原则
- **可扫描性**: 表格 > 列表 > 纯文本
- **层次结构**: 概览 → 深度 → 行动
- **视觉引导**: emoji + 符号 + 分隔线

### 3. Prompt 优化
- **明确格式**: 给出完整模板
- **量化要求**: "5-8 items", "100+ words"
- **行动导向**: 添加行动建议层

### 4. Mock 数据策略
- 每个 fetcher 必须有 mock fallback
- mock 数据质量 = 演示效果
- 定期更新 mock 数据

---

**v2.0 核心理念**: 从"信息搬运"到"情报简报"
