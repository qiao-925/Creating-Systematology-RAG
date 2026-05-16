# 2026-01-21 【refactor】Prompt模板集中管理与优化-完成总结

## 1. 任务概述

| 字段 | 内容 |
|------|------|
| 任务类型 | refactor |
| 触发方式 | 用户请求 |
| 目标 | 优化RAG回答模板并集中管理所有prompt |

## 2. 关键步骤

### 2.1 优化 CHAT_MARKDOWN_TEMPLATE

**用户需求**：
- 客观第一，启发性回答
- 幽默风格，提升可读性
- 批判性视角
- DeepSeek风格格式

**实施内容**：
- 重写模板，加入4大核心原则：客观为本、启发优先、批判视角、推理透明
- 调整表达风格：严肃内容轻松表达、学术幽默
- 格式优化：引用块、emoji点缀、段落留白

### 2.2 集中管理 Prompt 模板

**背景**：模板分散在多处（根目录、代码中、agentic目录）

**实施内容**：
1. 创建 `prompts/` 目录结构
2. 提取代码中的模板为 `.txt` 文件
3. 迁移现有模板文件
4. 修改 `templates.py` 为文件加载模式
5. 更新所有引用

### 2.3 清理过期模板

**分析发现**：
- `chat.txt` - 活跃使用 ✅
- `simple.txt` - 仅遗留引擎使用
- `standard.txt` - 未使用 ❌
- `detailed.txt` - 未使用 ❌

**清理结果**：删除3个未使用模板，保留活跃模板

## 3. 交付结果

### 3.1 新增文件

```
prompts/
├── README.md              # 使用说明
├── rag/chat.txt           # RAG回答模板（主力）
├── query/rewrite.txt      # 查询改写模板
└── agentic/planning.txt   # Agent规划模板
```

### 3.2 修改文件

| 文件 | 改动 |
|------|------|
| `backend/.../formatting/templates.py` | 重写为文件加载模式（171→83行） |
| `backend/.../fastapi_routers/chat.py` | 更新为 `get_template()` 调用 |
| `backend/.../core/engine.py` | 更新为 `get_template()` 调用 |
| `backend/.../core/legacy_engine.py` | 更新为 `get_template()` 调用 |
| `backend/.../agentic/prompts/loader.py` | 更新模板路径 |
| `backend/.../processing/query_processor.py` | 更新模板路径 |
| `config/prompts/README.md` | 更新为迁移说明 |

### 3.3 删除文件

- `query_rewrite_template.txt`（根目录）
- `config/prompts/query_rewrite_template.txt`
- `prompts/rag/simple.txt`
- `prompts/rag/standard.txt`
- `prompts/rag/detailed.txt`

## 4. 技术要点

### 4.1 文件加载模式

```python
from backend.business.rag_engine.formatting.templates import get_template, reload_templates

# 获取模板
template = get_template()

# 热更新
reload_templates()
```

### 4.2 向后兼容

- 新路径不存在时自动回退旧路径
- 文件加载失败时使用内置默认模板

## 5. 验证

- [x] Lint 检查通过
- [x] 所有引用更新完成
- [x] 目录结构符合预期

## 6. 后续建议

- 持续迭代 `chat.txt` 模板，根据实际效果优化
- 可考虑添加模板版本管理
