# Prompt 模板管理

> 集中管理所有 LLM 提示词模板，便于迭代优化和版本控制。

## 1. 目录结构

```
prompts/
├── README.md           # 本文档
├── rag/
│   └── chat.txt        # RAG 回答模板（主力）⭐
├── query/
│   └── rewrite.txt     # 查询改写+意图理解
└── agentic/
    └── planning.txt    # 规划 Agent 系统提示
```

## 2. 模板说明

### 2.1 RAG 回答模板 (`rag/chat.txt`)

**核心原则**：
- 客观为本：基于知识库，坦诚边界
- 启发优先：挖掘"为什么"，不做搬运工
- 批判视角：指出局限和争议
- 幽默表达：严肃内容，轻松风格

**变量**：`{context_str}` - 知识库检索结果

### 2.2 查询改写模板 (`query/rewrite.txt`)

**功能**：意图理解 + 查询改写
**变量**：`{query}` - 原始查询
**输出**：JSON 格式

### 2.3 规划模板 (`agentic/planning.txt`)

**功能**：Agent 检索规划
**用途**：选择检索策略、决定是否改写查询

## 3. 使用方式

```python
from backend.business.rag_engine.formatting.templates import get_template, reload_templates

# 获取模板
template = get_template()

# 热更新（修改文件后）
reload_templates()
```

## 4. 修改指南

1. 直接编辑 `.txt` 文件
2. 测试效果
3. 调用 `reload_templates()` 热更新（或重启应用）

## 5. 版本记录

| 日期 | 变更 |
|------|------|
| 2026-01-21 | 清理未使用模板，保留 chat/rewrite/planning |
| 2026-01-21 | 初始化，集中管理所有模板 |
