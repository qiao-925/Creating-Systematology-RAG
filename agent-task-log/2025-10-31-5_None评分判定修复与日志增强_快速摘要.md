# None 评分判定修复与日志增强（快速摘要）

- 日期：2025-10-31
- 目标：避免将 `score=None` 当作 0 误判为低相关并触发兜底；增强检索统计日志与 trace 字段
- 涉及文件：`src/query_engine.py`

## 症状与根因
- 症状：查询经常显示“最高相似度: 0.00”，触发兜底，回答偏向通用推理，知识库利用不足。
- 根因：`CitationQueryEngine` 返回的来源 `score` 可能为 `None`；原逻辑用 `s.get('score', 0)` 计算最高分，导致 `None → 0`，被误判为低相关。

## 调整要点
- 评分判定
  - 仅对“有数值分数”的来源统计 `min/avg/max` 与 `high_quality_count`。
  - `max_score` 在“全部为 None”时为 None；此时不再判定为低相关，不触发兜底（除非无来源或答案空白）。
- 兜底触发
  - 触发条件由：`no_sources | (numeric max < 阈值) | empty_answer`；不再因“无分数”触发。
- 日志与 trace 增强
  - 控制台/日志新增：`numeric_scores_count` 与 `scores_none_count`。
  - trace.retrieval 新增：`min_score/max_score/avg_score/threshold/high_quality_count/numeric_scores_count/scores_none_count`。

## 关键代码引用
- None 安全的统计与判定：
```146:158:src/query_engine.py
numeric_scores = [s.get('score') for s in sources if s.get('score') is not None]
max_score = max(numeric_scores) if numeric_scores else None
high_quality_sources = [
    s for s in sources
    if (s.get('score') is not None) and (s.get('score') >= self.similarity_threshold)
]
...
if max_score is not None:
    ... # 仅在存在数值分时进行低相关/良好判定
else:
    logger.info("检索评分缺失：所有来源的score为None（chunks=%s），跳过低相关判定，仅依据其他条件兜底", len(sources))
```
- 兜底条件调整与日志：
```176:195:src/query_engine.py
fallback_reason = None
if not sources:
    fallback_reason = "no_sources"
elif (max_score_logged is not None) and (max_score_logged < self.similarity_threshold):
    fallback_reason = f"low_similarity({max_score_logged:.2f}<{self.similarity_threshold})"
elif not answer or not answer.strip():
    fallback_reason = "empty_answer"
```
- 检索统计与 trace 扩展：
```166:174:src/query_engine.py
logger.debug(
    "检索统计: top_k=%s, chunks=%s, numeric=%s, none=%s, min=%s, avg=%s, max=%s, threshold=%.3f",
    ...
)
```
```244:254:src/query_engine.py
"high_quality_count": _hq,
"numeric_scores_count": len(_scores),
"scores_none_count": _none_count,
```

## 复测建议
- 用“定义类/通用常识”问题再次查询，日志中应出现 `scores_none_count`，但不应再因为“0.00”触发兜底。
- 如确实检索为空，应看到 `reason=no_sources` 的兜底；若生成为空，则 `reason=empty_answer`。

## 后续可选（若需要）
- 在 UI 聊天页未构建索引时（`index_built=False`）给出显著提醒与跳转入口。
- 接入 Reranker/Hybrid 以提升召回质量（另案推进）。
