# Cloud927 版本日志

## v4.0 (2026-02-08) - 架构重构 + 六大板块覆盖

### 🎯 核心升级

#### 数据源扩展
- 从 8 个数据源扩展到 **29 个**
- 新增 **6 大板块分类**：AI前沿、创业/投融资、金融/宏观、Web3/Crypto、科技政策、全球重大事件
- 每个板块 3-5 个高质量数据源

#### 架构重构
- **统一数据模型**：所有 fetcher 输出 `NewsItem` 对象
- **Fetcher 基类**：公共逻辑集中，新增数据源只需实现 2 个方法
- **双层 LLM 架构**：
  - Layer 1: Gemini Flash（预处理，成本低）
  - Layer 2: Claude Opus 4.5（洞察生成，质量高）
- **LLM 抽象层**：支持多模型切换，修改 config.yaml 即可

#### 数据处理优化
- **跨源去重**：多源报道同一事件时合并元数据
- **聚类改进**：修复 bug，支持六大板块分类
- **实体追踪**：跟踪重要实体（公司、人物、事件）的演进

#### 输出格式升级
- **两层阅读结构**：
  - 快速扫描（2分钟）：一句话信号 + Top 3 + 行动清单
  - 深度洞察（选读）：2-3 个重要话题展开
- **决策友好**：每个洞察包含"对你意味着什么"和"建议行动"

### 📁 新增文件

**核心模块**
- `src/models.py` — 统一数据模型（NewsItem）
- `src/pipeline.py` — 数据流水线编排
- `src/fetchers/base_fetcher.py` — Fetcher 基类

**LLM 抽象层**
- `src/llm/base_client.py` — 基类接口
- `src/llm/gemini_client.py` — Gemini Flash 预处理
- `src/llm/claude_client.py` — Claude Opus 洞察（使用 raw httpx）
- `src/llm/openai_client.py` — GPT 备选方案
- `src/llm/factory.py` — 工厂函数

**新数据源**
- `src/fetchers/crypto/` — CoinDesk, The Block, Decrypt
- `src/fetchers/startup/` — TechCrunch, 36Kr, IT桔子
- `src/fetchers/finance/` — Yahoo Finance, FT, Bloomberg
- `src/fetchers/policy/` — TechPolicy RSS
- `src/fetchers/news/` — BBC, Reuters, AP News, FT, Bloomberg
- `src/fetchers/china/` — Sina, Caixin, iFeng, Pengpai, 今日热门

**存储**
- `src/storage/obsidian_writer.py` — Obsidian 集成

### 🔧 修改文件

**主要改动**
- `main.py` — 简化到 50 行，添加 `override=True` 到 load_dotenv
- `config.yaml` — 重新组织，新增 29 个数据源配置 + LLM 配置
- `src/config.py` — 支持 base_url 配置（代理支持）
- `src/generator_v3.py` — 重写 prompt，适配六大板块 + 两层阅读结构
- `src/processor/clustering.py` — 修复 bug，支持六大板块分类
- `src/processor/deduplicator.py` — 合并元数据逻辑
- `src/processor/timeline_tracker.py` — 实体追踪改进

**Fetcher 改造**
- 所有 18 个现有 fetcher 继承 `BaseFetcher`
- 统一输出 `NewsItem` 对象
- 支持 config.yaml 配置（enabled, timeout, limit）

### 🗑️ 删除文件

- `src/generator.py` — v2 generator（已废弃）
- `src/storage_v2.py` — 重复文件（已废弃）

### 🐛 Bug 修复

1. **LLM 导入问题**：改为懒加载，避免可选依赖缺失时导入失败
2. **聚类 bug**：修复子分类只放第一条就 break 的问题
3. **load_dotenv 覆盖**：添加 `override=True`，确保 .env 覆盖系统环境变量
4. **Claude API 代理支持**：使用 raw httpx 替代 anthropic SDK，绕过代理头部限制

### 📊 性能指标

| 指标 | v2.0 | v4.0 | 变化 |
|------|------|------|------|
| 数据源 | 8 | 29 | +262% |
| 覆盖板块 | 1 | 6 | 全面 |
| 抓取时间 | ~30s | ~30s | 并行优化 |
| 日报大小 | ~2000字 | ~4000字 | +100% |
| 日均成本 | ~$0.05 | ~$0.15 | 功能增强 |

### 🔐 安全性改进

- 支持代理服务（NewCLI 等）
- API key 完全隔离在 .env
- 无本地数据库，临时处理
- 日报仅保存到本地 Obsidian

### 📝 文档

- 完整重写 README.md
- 新增 CHANGELOG.md
- 代码注释完善

---

## v3.0 (2026-02-07) - 初版 v3 架构

### 特性
- 基础 v3 架构框架
- 18 个数据源
- Gemini 单层 LLM

---

## v2.0 (2026-02-06) - 8 数据源 + 优化排版

### 特性
- 8 个数据源聚合
- 优化排版和表格化
- Gemini API 集成
- Obsidian 保存

---

## 升级指南

### 从 v2.0 升级到 v4.0

1. **备份现有配置**
   ```bash
   cp .env .env.backup
   ```

2. **更新代码**
   ```bash
   git pull origin master
   ```

3. **更新依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置新的 API key**
   ```bash
   # 如果使用 Claude，需要配置 ANTHROPIC_AUTH_TOKEN
   # 编辑 .env，添加或更新：
   ANTHROPIC_AUTH_TOKEN=your_key_here
   ```

5. **运行**
   ```bash
   python main.py
   ```

### 配置迁移

v4.0 的 config.yaml 结构完全不同，建议：
1. 删除旧的 config.yaml
2. 使用新的 config.yaml（已包含所有 29 个源的配置）
3. 根据需要启用/禁用数据源

---

## 已知问题

### 数据源问题

- **RSSHub 源（14个）**：返回 403 Forbidden
  - 原因：RSSHub 公共实例限流
  - 解决：自建 RSSHub 实例或使用付费服务
  - 受影响源：v2ex, jinri_remai, sina, ifeng, pengpai, caixin, 36kr, itjuzi, china_policy 等

- **Reuters**：返回 404
  - 原因：URL 已变更
  - 解决：待更新 RSS 源

- **AP News**：SSL 错误
  - 原因：SSL 握手失败
  - 解决：待调查

### 模型问题

- **Claude API 代理**：需要使用 raw httpx，anthropic SDK 不兼容某些代理
  - 已解决：claude_client.py 使用 raw httpx

---

## 下一步计划

### v4.1 (计划)
- [ ] 修复 RSSHub 源（自建或替代）
- [ ] 修复 Reuters/AP News 源
- [ ] 增加数据源可靠性监控
- [ ] 优化 prompt 工程

### v5.0 (计划)
- [ ] 本地向量数据库（长期记忆）
- [ ] 用户反馈机制
- [ ] 多语言支持
- [ ] Web UI 仪表板

---

*Last Updated: 2026-02-08*
