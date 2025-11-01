# 空回应诊断与后处理流程（快速摘要）

- 日期：2025-10-31
- 任务：分析空回应原因；梳理检索后处理流程；提出质量优化方向
- 相关文件：`src/query_engine.py`、`src/config.py`

## 现象复盘
```
💬 查询: 什么是系统科学？它的核心思想是什么？
2025-10-31 08:30:06 - query_engine - DEBUG - 查询设备: cuda:0 (GPU加速)
⚠️  检索质量较低（最高相似度: 0.00），答案可能更多依赖模型推理
2025-10-31 08:30:06 - query_engine - WARNING - 检索质量较低，最高相似度: 0.00，阈值: 0.5
```

## 结论（为何出现“空回应”）
- 当前实现使用 `CitationQueryEngine` 直接生成答案；当检索结果为空/极低相关时，模型在“无上下文”的默认提示词下可能返回空字符串或极短文本。
- 代码仅记录“检索质量较低”的日志，并未做任何兜底/改写/外部补充；因此 `answer = str(response)` 可能为空，被原样返回，表现为“空回应”。

证据（关键逻辑）：
- 检索与生成：
```
126:            response: Response = self.query_engine.query(question)
131:            answer = str(response)
```
- 质量评估仅日志告警，无策略分支：
```
146:            high_quality_sources = [s for s in sources if s.get('score', 0) >= self.similarity_threshold]
153:            if max_score < self.similarity_threshold:
154:                print(f"⚠️  检索质量较低（最高相似度: {max_score:.2f}），答案可能更多依赖模型推理")
155:                logger.warning(f"检索质量较低，最高相似度: {max_score:.2f}，阈值: {self.similarity_threshold}")
```
- 返回路径：
```
179:            print(f"✅ 查询完成，找到 {len(sources)} 个引用来源")
181:            return answer, sources, trace_info
```

## 当前检索后处理流程（概述）
1) 执行 `CitationQueryEngine.query()` → 得到 `response`
2) 提取 `answer = str(response)` 与 `sources = response.source_nodes`
3) 以 `SIMILARITY_THRESHOLD=0.5` 过滤低质量来源，仅打印告警/信息日志
4) 可选：收集 `trace_info`（耗时、chunks、avg_score、响应长度）
5) 直接返回 `(answer, sources, trace_info)`；未做任何兜底或重试/改写

## 影响
- 在“定义类/常识类”问题（如“什么是系统科学”）且知识库召回为空或极低相关时，容易出现空白或极短回答。
- 无兜底与外部补充时，答案质量/稳定性受限；用户体验不佳。

## 优化方向（供决策）
- 方案A（兜底生成）：当 `max_score < 阈值` 或 `sources == []` 时，切换到“纯LLM定义类回答”的提示词模板，明确允许基于通用知识进行解释，并在答案中标注“基于一般知识推理”。
- 方案B（外部补充）：启用/增强 `HybridQueryEngine` 的维基百科补充逻辑，在低相关时自动查询并合并答案（项目已内置该引擎）。
- 方案C（检索增强）：
  - 提升 `similarity_top_k`（如 3→5）
  - 引入 Reranker（LlamaIndex Reranker）
  - 动态/更低阈值（如 0.5→0.3），或自适应阈值
  - Query Rewrite（自动补全/重写查询关键词）
- 方案D（输出守护）：若 `answer.strip()==""` 或长度过短，触发一次兜底生成或给出“未检索到相关资料”的解释性输出，避免空白。

## 建议的最小闭环（低风险先行）
- 第一步：加入“输出守护+兜底生成”（方案A+D），确保永不返回空白答案。
- 第二步：打开 `HybridQueryEngine` 的低相关触发（方案B），优先补充通用百科来源。
- 第三步：试探性调降阈值至 `0.3` 并观察日志（方案C，易回退）。

> 若同意上述顺序，我将先在 `src/query_engine.py` 增加低相关兜底分支与输出守护，再提供小范围可配置化参数，严格遵循最小改动原则。
