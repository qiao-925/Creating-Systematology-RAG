# 【impl】Research Kernel MVP 开发

> 一句话目标：跑通 问题→取证→综合→判断→启发 研究型 Agent 全链路

## Checkpoint

| CP | 内容 | 状态 |
|----|------|------|
| 1 | Phase 1.1-1.4 研究内核（state/tools/agent/guardrails） | ✅ |
| 2 | Phase 2 服务层接入（rag_service research 路由） | ✅ |
| 3 | Phase 3.1-3.2 前端适配 + 可观测性 | ✅ |
| 4 | 代码清洗（deprecated 标记 + 文档同步） | ✅ |
| 5 | 静态审查 Bug 修复（6 issues，2 review 轮次） | ✅ |
| 6 | Phase 1.5 + 3.3 端到端验证 | ⬜ |

## 当前上下文

- 决策：LlamaIndex AgentWorkflow，并行新建策略，5 工具集（vector_search/hybrid_search/record_evidence/synthesize/reflect）
- 阻塞：端到端验证需要真实 LLM API key + 已构建知识库索引
- 下一动作：运行端到端验证，确认 4 条 MVP 成功信号
- 测试：63 passed（59 新 + 4 legacy）
- CP-5 修复清单：
  - [high] research mode 忽略用户选择模型 → create_llm(model_id=self.model_id)
  - [high] record_evidence 预算耗尽后仍追加 → 预检 + 回归测试
  - [medium] research 回复不持久化 → save_to_chat_manager
  - [high] run_sync() asyncio.run() 在 Streamlit 崩溃 → ThreadPoolExecutor
  - [high] _research_agent 缓存在换模型后失效 → model_id 变更检测
  - [medium/low] 死代码 + 无用 import → 删除
- 延后项：研究进度展示（细粒度）、LlamaIndex Observers 接入、Context 序列化

## 关键文件

**内核**：`backend/business/research_kernel/` (state.py, agent.py, tools/, prompts/)
**服务层**：`backend/business/rag_api/rag_service.py`
**前端**：`frontend/components/research_display.py`, `query_handler/research.py`, `config_panel/`
**计划**：`docs/research/harness-engineering/MVP Version/MVP执行总计划.md`

---
*Issue: #13 | Updated: 2026-04-08 16:28 | Git: aa3c4c4 → commit pending*
