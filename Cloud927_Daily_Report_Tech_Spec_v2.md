# Project: Cloud927 Automated Daily Insight Generator (Agent Teams Edition)
## Version: 2.0 (Hardened)

## 1. Project Overview (项目概述)
构建一个高鲁棒性的 Python 自动化系统，通过 API 和 RSS 并行获取全球前沿科技资讯（Hacker News, GitHub, Hugging Face），利用 Google Gemini API 进行**分级摘要与深度合成**，最终生成结构化的 Markdown 日报并自动归档至 Obsidian 知识库。

**核心目标**：零人工干预 (Zero-Touch)，防幻觉 (Anti-Hallucination)，防 Token 溢出。

## 2. Core Architecture: ETL Pipeline (核心架构)

采用 **ETL (Extract, Transform, Load)** 架构，引入**中间件 (Middleware)** 处理数据清洗：

1.  **Extract (抓取层)**: `SourceFetcher`。并行获取多源数据，实现指数退避重试 (Exponential Backoff)。
2.  **Transform (处理层 - 关键升级)**: `ContentProcessor`。
    * **Token Budgeting**: 对不同来源实施严格的字符数截断。
    * **Sanitization**: 清洗 HTML 标签，仅保留纯文本。
3.  **Generate (生成层)**: `LLMClient`。调用 Gemini API，注入 System Prompt。
4.  **Load (存储层)**: `ObsidianWriter`。处理文件锁与路径冲突。

## 3. Data Sources & Limits (数据源与限流策略)
*为防止 Context Window 爆炸，严格执行 "Top N" 策略。*

| Source           | Endpoint / Method          | Selection Logic                      | Token Constraint (Per Item)                             |
| :--------------- | :------------------------- | :----------------------------------- | :------------------------------------------------------ |
| **Hacker News**  | API: `.../topstories.json` | Score > 150 的前 **5** 条            | 仅取 Title + URL + Top 3 Comments (每条评论限 200 字符) |
| **GitHub**       | `feedparser` (RSS)         | Python & AI Trending 前 **5** 个项目 | Description 限 300 字符，Readme (如有) 仅取首段         |
| **Hugging Face** | `feedparser` (RSS)         | Daily Papers 前 **3** 篇             | Title + Abstract (限 500 字符)                          |

## 4. Tech Stack & Dependencies (技术栈)
* **Language**: Python 3.10+
* **Core Libs**:
    * `google-generativeai` (LLM Interface)
    * `requests` & `feedparser` (Network)
    * `tenacity` (Robust Retry Logic - **Mandatory**)
    * `python-dotenv` (Security - **Mandatory**)
    * `pydantic` (Data Validation - Optional but Recommended)

## 5. Security & Safety Rails (安全护栏 - 新增)
1.  **Environment Variables**:
    * 所有敏感 Key (`GEMINI_API_KEY`, `OBSIDIAN_VAULT_PATH`) 必须通过 `.env` 加载。
    * 代码中严禁出现硬编码 Key。
    * **Action**: Agent 必须创建 `.env.example` 模板。
2.  **Content Safety**:
    * **No Image Generation**: 禁止 LLM 生成 Markdown 图片链接 `![]()`，除非链接来自 GitHub API 的 `owner.avatar_url` 字段。防止出现“死链”或“红叉”。
    * **Link Validation**: 生成的 Markdown 中所有 `[Link]` 必须来自原始数据 Input，严禁 LLM 自行编造 URL。

## 6. LLM Prompt Strategy (Prompt 工程优化)
**Role**: You are "Cloud927", a pragmatic tech lead and AI researcher.

**Input Data**: (JSON format containing sanitized titles, urls, summaries)

**Instruction**:
Analyze the input data. Ignore marketing fluff. Focus on **engineering value** and **impact**.

**Output Format**: Strictly follow this Markdown structure:

```markdown
# 📅 Cloud927 Daily Insight - {YYYY-MM-DD}

## 🚨 Top Signal (今日头条)
> *One most important news item.*
- **Core Insight**: (Why does this matter? 1 sentence)
- **Source**: [Original Link]

## 🛠️ Engineering & Tools (工具)
- **[Project Name]**: (What problem does it solve?) [Link]
- ...

## 💡 Hacker Perspective (观点)
- (Summary of a high-quality discussion or thought piece) [Link]

## 📝 Research (论文)
- **[Paper Title]**: (Key innovation/result) [Link]