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
更新时间: 2026-02-08 (修复 RSS → HTML 爬取)
