# 2026-01-29 【implementation】智能问题生成 - 词云交互 - 完成总结

**任务类型**: implementation  
**日期**: 2026-01-29  
**关联计划**: 2026-01-24-11_【plan】智能问题生成-词云交互设计  
**Agent**: Claude Opus 4.5

---

## 1. 结构检查（再收尾）

| 文件 | 行数 | 结论 |
|------|------|------|
| `frontend/components/keyword_cloud.py` | 247 | ✅ ≤300 |
| `backend/business/rag_engine/processing/keyword_extractor.py` | 317 | ⚠️ 超限 |

**遗留：结构问题**  
- `keyword_extractor.py` 超 300 行，建议：将 `_filter_semantic_fragments`、`SEMANTIC_BLOCKLIST` 及语义相关逻辑拆至独立模块（如 `semantic_filter.py`），或精简 `_is_complete_segment` / `_is_meaningful_word` 的重复判断。  
- 用户选择暂不处理，收尾照常进行。

---

## 2. 关键步骤与实施说明

1. **关键词提取（CP1）**  
   - 仅解析 PDF 标题，输出 `data/keyword_cloud.json`、`data/keyword_cloud_parsed_files.json`。  
   - 语义过滤：黑名单 + 去除「被更长词包含」的 3 字及以上片段，保证词云语义通顺。

2. **词云 UI（CP2）**  
   - 大框内 30 个气泡、不同颜色、持续浮动，展示「词(数量)」。  
   - 选词上限由 10 改为 5；词云展示由 60 改为 30。

3. **气泡与下方联动**  
   - 尝试：iframe 内改 parent.location、localStorage + 父页轮询，均受沙箱/跨域限制。  
   - 最终方案：**streamlit-iframe-event** + **data URL**。iframe 内点击后 `postMessage({ code: 0, token: JSON.stringify(selected) })`，组件转成返回值，Python 解析 `token` 写入 `session_state.keyword_cloud_selected`，与下方多选、「生成问题」一致。

4. **依赖**  
   - 新增 `streamlit-iframe-event>=0.0.9`；未安装时回退为 `components.html` 展示气泡 + 提示用下方多选。

---

## 3. 测试结果

- 本地执行 `uv sync` 安装 streamlit-iframe-event 成功。  
- 用户确认：点击气泡后，下方「已选词」与「生成问题」联动正常，收尾前主要交付已验收。

---

## 4. 交付结论

- 词云区：30 个浮动气泡、词(数量)、最多选 5，与下方多选/生成问题通过 streamlit-iframe-event 稳定联动。  
- 关键词数据：静态 JSON + 语义过滤，词云展示与已选词逻辑闭环。

---

## 5. 六维度优化分析

| 维度 | 亮点（✅） | 改进建议（⚠️） | 优先级 |
|------|------------|----------------|--------|
| **代码质量** | 词云 HTML/JS 内联封装清晰，postMessage 协议与 Python 解析职责分明。 | 气泡 HTML 字符串可抽到独立模板或小函数分段，减少 f-string 嵌套。 | 🟢 |
| **架构设计** | 前端选词与 session_state 单一数据源，回退路径（无 iframe-event 时用多选）明确。 | 依赖第三方 streamlit-iframe-event，长期可考虑自建轻量组件以可控协议回传。 | 🟢 |
| **性能** | data URL 内联 HTML，无额外请求；词云数据静态 JSON，无运行时分析。 | 若词表极大可只传前 30 条或按需分页；当前 30 条可接受。 | 🟢 |
| **测试** | 用户浏览器验收联动通过。 | 可补充：build_keyword_cloud 产出 JSON 的断言、keyword_extractor 语义过滤的单元测试。 | 🟡 |
| **可维护性** | 收尾日志与计划文档对应，关键方案（iframe-event + data URL）有注释说明。 | keyword_extractor 超 300 行，建议拆出语义过滤模块并补充入参/出参说明。 | 🟡 |
| **技术债务** | 无新增临时 hack，streamlit-iframe-event 复用其现有 code/token 协议。 | 若上游组件废弃或协议变更，需适配 postMessage 格式或切回自建组件。 | 🟢 |

---

## 6. 优先级汇总

| 优先级 | 项 | 建议处理时间 |
|--------|-----|--------------|
| 🟡 | keyword_extractor 拆分/精简至 ≤300 行；补充词云/语义过滤相关单测 | 本月内 |
| 🟢 | 气泡 HTML 模板化、长期组件策略与协议文档 | 季度内 |

---

## 7. 相关文件

| 操作 | 文件 |
|------|------|
| 修改 | `frontend/components/keyword_cloud.py` |
| 修改 | `backend/business/rag_engine/processing/keyword_extractor.py` |
| 修改 | `scripts/build_keyword_cloud.py`（调用方式未改） |
| 修改 | `pyproject.toml`（新增 streamlit-iframe-event） |
| 数据 | `data/keyword_cloud.json`、`data/keyword_cloud_parsed_files.json` |
