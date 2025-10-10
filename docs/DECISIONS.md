# 技术决策记录（Architecture Decision Records）

## ADR-001: 选择LlamaIndex作为RAG框架

**日期**: 2025-10-07

**状态**: 已接受

**背景**: 需要一个成熟的RAG框架来快速构建知识库问答系统

**决策**: 使用LlamaIndex作为核心RAG框架

**理由**:
- 专门为RAG场景设计，API简洁易用
- 原生支持多种向量数据库和LLM
- 内置引用溯源功能（CitationQueryEngine）
- 活跃的社区和完善的文档

**后果**: 
- 依赖LlamaIndex的更新和维护
- 学习曲线相对较低

---

## ADR-002: 使用DeepSeek API作为LLM

**日期**: 2025-10-07

**状态**: 已接受

**背景**: 需要选择合适的大语言模型服务

**决策**: 使用DeepSeek开放平台提供的API

**理由**:
- 性价比高
- 中文能力强
- 兼容OpenAI API格式，易于集成
- 适合长期运营的应用

**实现**: 通过OpenAI SDK配置base_url为DeepSeek端点

---

## ADR-003: 选择Chroma作为向量数据库

**日期**: 2025-10-07

**状态**: 已接受

**背景**: 需要为约500个Markdown文件构建向量索引

**决策**: 使用Chroma作为向量数据库

**理由**:
- 轻量级，易于部署和维护
- 支持本地持久化存储
- 与LlamaIndex集成良好
- 适合中等规模知识库（<1000文档）
- 开源且活跃维护

**备注**: 若未来知识库规模显著扩大或性能不足，可考虑迁移至Qdrant或Milvus

---

## ADR-004: 使用本地Embedding模型

**日期**: 2025-10-07

**状态**: 已接受，但保留调整空间

**背景**: 需要选择文本向量化方案

**决策**: 初期使用本地Embedding模型（bge-base-zh-v1.5或m3e-base）

**理由**:
- 成本考虑：本地模型无API调用费用
- 隐私保护：数据不离开本地
- 中文优化：bge和m3e专门针对中文优化
- 足够满足中等规模知识库需求

**设计原则**: 
- 模型配置设计为可切换
- 便于未来根据性能需求切换至API服务

**潜在问题**: 本地推理速度可能慢于API服务

---

## ADR-005: 使用Streamlit构建UI

**日期**: 2025-10-07

**状态**: 已接受

**背景**: 需要一个快速可用的Web界面

**决策**: 使用Streamlit构建用户界面

**理由**:
- 极简API，快速开发
- 原生支持Python，无需前后端分离
- 自动处理状态管理
- 适合数据应用和原型开发
- 遵守奥卡姆剃刀原则

**设计原则**: 简洁版UI，只包含核心功能
- 对话窗口
- 引用溯源展示
- 文档上传/URL输入

**备注**: 若未来需要更复杂的交互或更好的性能，可考虑迁移至FastAPI + React

---

## ADR-006: 项目长期上下文管理策略

**日期**: 2025-10-07

**状态**: 已接受

**背景**: 项目可能持续数月开发，需要确保上下文持久化

**决策**: 建立多层次的文档体系
- `CHANGELOG.md` - 记录开发活动
- `docs/DECISIONS.md` - 记录技术决策（本文档）
- `TODO.md` - 跟踪待办事项
- `plan.md` - 总体规划

**理由**:
- 便于长期项目的上下文恢复
- 帮助新开发者快速上手
- 记录决策原因，避免重复讨论

---

## ADR-007: 使用LlamaIndex官方数据加载器

**日期**: 2025-10-07

**状态**: 已接受（重构进行中）

**背景**: 
- 初始实现自定义了`MarkdownLoader`和`WebLoader`（约300行代码）
- 发现LlamaIndex提供了官方数据加载器组件
- 存在"重复造轮子"的问题

**决策**: 重构数据加载层，使用LlamaIndex官方组件
- 使用`SimpleDirectoryReader`替代自定义`MarkdownLoader`
- 使用`SimpleWebPageReader`替代自定义`WebLoader`

**理由**:

**1. 遵循"不要重复造轮子"原则**
- 官方组件经过充分测试和社区验证
- 减少维护负担和潜在bug

**2. 代码简化**
- 从~300行减少到~50行（减少83%）
- 提高代码可读性和可维护性

**3. 功能更强大**
- `SimpleDirectoryReader`支持40+种文件格式
- 自动提取标准元数据（文件路径、名称、类型、时间戳等）
- 内置错误处理和日志

**4. 易于扩展**
- 未来可轻松添加PDF、DOCX、JSON等格式
- 统一的API接口

**对比分析**:

| 特性 | 自定义实现 | SimpleDirectoryReader |
|------|----------|---------------------|
| 代码量 | ~300行 | ~10行 |
| 支持格式 | 仅MD | 40+格式 |
| 元数据 | 手动提取 | 自动标准化 |
| 错误处理 | 手动 | 内置 |
| 维护成本 | 高 | 低（官方维护） |
| 扩展性 | 需手动编码 | 配置即可 |

**实施计划**:
1. 添加依赖包：`llama-index-readers-file`、`llama-index-readers-web`
2. 重构`src/data_loader.py`，使用官方组件
3. 更新调用方代码（`main.py`、`app.py`）
4. 更新相关测试
5. 更新文档（README、ARCHITECTURE等）

**影响范围**:
- ✅ 不影响核心架构（索引、查询、对话层）
- ✅ 仅影响数据加载层（约15%代码）
- ✅ 向后兼容（功能保持不变）

**后果**:
- 短期：需要2-3小时重构时间
- 长期：降低维护成本，提高代码质量和可扩展性

**备注**: 
- 保留`DocumentProcessor`类中有价值的文本清理逻辑（可选）
- 标题提取逻辑已移除，使用文件名作为标题（遵循简化原则）

---

## ADR-008: 集成 GitHub 数据源

**日期**: 2025-10-10

**状态**: 已接受

**背景**: 
- 现有系统支持本地 Markdown 文件和网页数据源
- 越来越多技术文档和开源项目托管在 GitHub
- 需要一种便捷方式从 GitHub 仓库导入文档作为知识库

**决策**: 集成 GitHub 仓库作为第三种数据源，使用 LlamaIndex 的 `GithubRepositoryReader`

**理由**:

**1. 技术选型：使用 GithubRepositoryReader 而非 GithubClient**
- `GithubRepositoryReader` 是高层封装，专为文档加载设计
- 返回标准 `Document` 对象，可直接用于索引
- 自动处理文件遍历、内容读取、元数据提取
- `GithubClient` 是底层 API 客户端，需要手动处理所有逻辑

**2. 架构一致性**
- 与现有 `MarkdownLoader` 和 `WebLoader` 保持相同的设计模式
- 统一的 API 接口：`load_repository()` 和便捷函数 `load_documents_from_github()`
- 元数据标准化：`source_type`, `repository`, `branch` 等

**3. 简洁实现原则**
- 暂不支持文件类型过滤（保持简单）
- 暂不支持子目录过滤（遵循最小改动）
- 暂不集成到 Streamlit UI（保持 CLI 为主）

**实施方案**:
- 依赖：`llama-index-readers-github>=0.2.0`
- 配置：环境变量支持 `GITHUB_TOKEN` 和 `GITHUB_DEFAULT_BRANCH`
- CLI：新增 `import-github` 命令
- 测试：8 个单元测试 + 1 个集成测试

**对比分析**:

| 特性 | GithubRepositoryReader | GithubClient |
|------|----------------------|--------------|
| 定位 | 文档加载器 | API 客户端 |
| 返回值 | Document 列表 | 原始 API 数据 |
| 使用难度 | 低（开箱即用） | 高（需手动处理） |
| 代码量 | ~90 行 | ~200+ 行 |
| 维护成本 | 低（官方维护） | 高（自行维护） |

**影响范围**:
- ✅ 不影响现有数据加载器（隔离良好）
- ✅ 不影响索引和查询模块（统一接口）
- ✅ 测试覆盖率提升：data_loader 从 30% → 53%

**后续扩展**:
- 如需文件类型过滤：可参考 `GithubRepositoryReader` 的 `filter_file_extensions` 参数
- 如需子目录过滤：可添加 `filter_directories` 参数
- 如需 UI 集成：可在 Streamlit 中添加仓库输入表单

**决策记录**: 本集成遵循"奥卡姆剃刀"原则，保持简单实用，后续根据实际需求迭代优化。

---

## ADR-009: 集成维基百科知识增强

**日期**: 2025-10-10

**状态**: 已接受

**背景**: 
- 本地知识库虽然专业，但可能缺乏通识背景知识
- 用户查询涉及的概念可能需要额外的百科解释
- 需要在本地知识库和外部知识源之间找到平衡

**决策**: 实现混合模式的维基百科知识增强系统

**核心方案**:

1. **双模式设计**:
   - **预索引模式**: 构建索引时预加载核心概念的维基百科内容
   - **实时查询模式**: 查询时动态检索维基百科补充（智能触发）

2. **智能触发策略**:
   ```python
   触发条件:
   - 本地结果相关度 < 阈值（默认0.6）
   - 本地结果为空
   - 用户显式请求（查询包含"维基百科"等关键词）
   ```

3. **技术实现**:
   - 使用 `llama-index-readers-wikipedia` 官方 Reader
   - `HybridQueryEngine` 类实现混合查询逻辑
   - 动态临时索引（不持久化维基百科内容）
   - LLM 提取关键词 + 自动语言检测

4. **来源溯源**:
   - 分区展示：本地知识库 vs 维基百科
   - 维基百科结果标记 [W1], [W2] 并显示 URL
   - 本地结果显示文件名和路径

**关键决策点**:

**决策1: 实时查询触发策略 → 智能触发**
- ❌ 方案A: 始终查询（体验好但慢）
- ✅ 方案B: 智能触发（平衡性能和效果）
- ❌ 方案C: 手动开关（用户体验差）

**理由**: 
- 智能触发既保证性能，又在需要时提供补充
- 用户无需手动控制，自动化程度高
- 可通过阈值调节触发灵敏度

**决策2: 关键词提取方法 → LLM 提取**
- ✅ 方案A: 使用 LLM 提取关键实体（准确但慢）
- ❌ 方案B: NLP 分词 + TF-IDF（快但可能不准）

**理由**:
- LLM 能理解上下文，提取更准确的实体
- 维基百科查询次数有限（1-3次），性能影响可接受
- 提取质量直接影响维基百科结果相关性

**决策3: 维基百科内容索引方式 → 动态临时索引**
- ✅ 方案A: 动态临时索引（不持久化）
- ❌ 方案B: 持久化索引（混入主索引）

**理由**:
- 动态索引保证维基百科内容始终最新
- 避免主索引污染，便于管理
- 节省存储空间
- 缺点：每次查询需要重新向量化（可接受，仅2-3个页面）

**技术实现**:

```python
# 数据加载
def load_documents_from_wikipedia(pages, lang, ...):
    reader = WikipediaReader()
    docs = reader.load_data(pages=pages, lang=lang)
    # 增强元数据：source_type="wikipedia"
    return docs

# 混合查询引擎
class HybridQueryEngine:
    def query(question):
        # 1. 本地检索
        local_answer, local_sources = self.local_engine.query(question)
        
        # 2. 判断是否需要维基百科
        if self._should_query_wikipedia(local_sources, question):
            keywords = self._extract_keywords(question)  # LLM提取
            lang = self._detect_language(question)       # 中英文检测
            wiki_docs = self._query_wikipedia(keywords, lang)
            wikipedia_sources = self._retrieve_from_wiki_docs(wiki_docs, question)
        
        # 3. 合并答案
        final_answer = self._merge_answers(question, local_answer, 
                                           local_sources, wikipedia_sources)
        
        return final_answer, local_sources, wikipedia_sources
```

**配置参数**:
```env
ENABLE_WIKIPEDIA=true              # 是否启用
WIKIPEDIA_AUTO_LANG=true           # 自动检测语言
WIKIPEDIA_THRESHOLD=0.6            # 触发阈值（0-1）
WIKIPEDIA_MAX_RESULTS=2            # 最多结果数
WIKIPEDIA_PRELOAD_CONCEPTS=...     # 预索引概念列表
```

**影响**:

**优点**:
- ✅ 知识覆盖更全面（本地专业 + 维基通识）
- ✅ 自动化程度高（智能触发，无需用户干预）
- ✅ 来源清晰可溯源（分区展示）
- ✅ 支持多语言（中英文自动切换）
- ✅ 性能可控（智能触发，仅在需要时查询）

**缺点**:
- ⚠️ 增加查询延迟（触发时需等待维基百科 API）
- ⚠️ 依赖外部服务（维基百科可用性）
- ⚠️ 增加 LLM API 调用（关键词提取）

**风险与应对**:

| 风险 | 应对方案 |
|------|---------|
| 维基百科 API 限流 | 添加重试机制，设置超时 |
| 查询速度变慢 | 可关闭功能，或提高触发阈值 |
| 关键词提取不准 | 回退到简单分词方案 |
| 语言检测错误 | 允许用户手动选择语言 |
| 内容质量参差不齐 | 通过相似度过滤低质量结果 |

**监控指标**:
- 维基百科触发率（多少查询触发了维基百科）
- 维基百科命中率（触发后是否找到相关内容）
- 平均查询延迟（启用/禁用维基百科对比）
- 用户满意度（通过反馈收集）

**未来增强**:
1. **缓存机制**: 缓存热门查询的维基百科结果
2. **评分融合**: 合并本地和维基百科的相关度评分
3. **多语言支持**: 支持更多语言维基百科
4. **自定义概念库**: 允许用户自定义预索引概念
5. **溯源可视化**: 图形化展示知识来源树

**决策记录**: 维基百科集成实现了"专业知识+通识背景"的混合模式，在保持本地知识库权威性的同时，提供了更全面的知识覆盖。智能触发策略平衡了性能和效果，分区展示保证了来源的清晰可溯源。

---


