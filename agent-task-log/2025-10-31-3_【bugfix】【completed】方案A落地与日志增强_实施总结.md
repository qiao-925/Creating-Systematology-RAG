# 方案A落地与日志增强（实施总结）

- 日期：2025-10-31
- 变更目标：
  - 在低相关/无来源/空答案时触发兜底生成，避免空回应
  - 增强检索与生成阶段的详细日志与 trace 字段，利于学习与诊断
- 相关文件：`src/query_engine.py`

## 关键改动
- 在 `QueryEngine.query()` 中新增“输出守护 + 纯LLM定义类回答”兜底分支：
  - 触发条件：`sources == []`、`max_score < SIMILARITY_THRESHOLD`、`answer.strip()==""`
  - 兜底提示词：中文结构化输出；声明基于通用知识推理；禁止捏造引用；末尾固定注释行
  - 双重兜底：LLM异常或返回空文本时给出最小可用占位文本
- 增强日志：
  - 检索统计：`top_k, chunks, min/avg/max 分数, threshold, high_quality_count`
  - 触发兜底的原因、LLM耗时、输出长度
  - 控制台 `print` 与 `logger` 双通道输出，使 Streamlit/CLI 均可见
- 扩展 trace：
  - `retrieval`: `min_score, max_score, avg_score, threshold, high_quality_count`
  - `llm_generation`: `fallback_used, fallback_reason, response_length`

## 代码引用
- 兜底触发与提示：
```startLine:endLine:src/query_engine.py
+            # ===== 兜底策略（方案A）：输出守护 + 纯LLM定义类回答 =====
+            # 计算更多统计信息，便于日志观测
+            scores_list = [s['score'] for s in sources if s.get('score') is not None]
+            avg_score = sum(scores_list) / len(scores_list) if scores_list else 0.0
+            min_score = min(scores_list) if scores_list else 0.0
+            max_score_logged = max_score  # 与上方计算一致，仅为可读性
+            
+            logger.debug(
+                "检索统计: top_k=%s, chunks=%s, min=%.3f, avg=%.3f, max=%.3f, threshold=%.3f",
+                self.similarity_top_k,
+                len(sources),
+                min_score,
+                avg_score,
+                max_score_logged,
+                self.similarity_threshold,
+            )
...
+            if fallback_reason:
+                print(f"🛟  触发兜底生成（原因: {fallback_reason}）")
+                logger.info(
+                    "触发兜底生成: reason=%s, chunks=%s, min=%.3f, avg=%.3f, max=%.3f, threshold=%.3f",
+                    fallback_reason,
+                    len(sources),
+                    min_score,
+                    avg_score,
+                    max_score_logged,
+                    self.similarity_threshold,
+                )
```
- trace 扩展：
```startLine:endLine:src/query_engine.py
+                trace_info["retrieval"] = {
+                    "time_cost": round(retrieval_time, 2),
+                    "top_k": self.similarity_top_k,
+                    "chunks_retrieved": len(sources),
+                    "chunks": sources,
+                    "avg_score": round(_avg, 3),
+                    "min_score": round(_min, 3),
+                    "max_score": round(_max, 3),
+                    "threshold": self.similarity_threshold,
+                    "high_quality_count": _hq,
+                }
+                trace_info["llm_generation"] = {
+                    "model": self.model,
+                    "response_length": len(answer),
+                    "fallback_used": bool('fallback_reason' in locals() and fallback_reason),
+                    "fallback_reason": fallback_reason if 'fallback_reason' in locals() else None,
+                }
```

## 使用与观测建议
- 观察控制台与 `query_engine` 日志：
  - 关注 `检索统计` 与 `触发兜底生成` 记录，检查阈值是否合适
  - 如常见 `low_similarity`，可考虑调低阈值或接入 Reranker（方案C）
- 在 UI 场景下：输出末尾有固定注释，提醒来源不足且为通用知识推理

## 风险与回退
- 风险：兜底可能在个别情况下覆盖了仍有价值但低分的来源
- 回退：可将 `SIMILARITY_THRESHOLD` 调至更低（如 0.3），或暂时关闭兜底分支（条件判断处短路）

---
本次改动遵循最小改动原则，未改动外部接口签名；如需进一步提升稳定性，建议后续推进方案B（Hybrid）与方案C（检索增强）。
