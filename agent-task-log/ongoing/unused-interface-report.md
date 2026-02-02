# 未使用/过期接口初筛（2026-02-02）

说明：以下为“高置信”候选，基于全仓 `rg` 搜索 + 主入口（`frontend/main.py`、`backend/business/chat/manager.py`、`backend/business/rag_api/rag_service.py`）手动核对。

**已清理（2026-02-02）**：
- 已删除：`legacy_engine.py`、`simple_engine.py`、`github_link.py`、`vector_version_utils.py`、`github_import.py`
- 已删除：`chat_input_with_mode.py`、`sidebar.py`、`keyword_extractor.py`、`build_keyword_cloud.py`
- 已删除：`backend/infrastructure/data_loader.py`（兼容入口）
- 已删除：`test_query_engine.py`、`test_github_link.py`
- 已调整：相关导出/文档/测试索引

## A. 遗留实现（仅在 `__init__` 导出/测试引用）

- `backend/business/rag_engine/core/legacy_engine.py`  
  - 现象：`QueryEngine` 只在导出层出现，生产链路未见调用。  
  - 证据：`backend/business/rag_engine/__init__.py:31`、`backend/business/rag_engine/core/__init__.py:6`

- `backend/business/rag_engine/core/simple_engine.py`  
  - 现象：`SimpleQueryEngine` 只在导出层出现。  
  - 证据：`backend/business/rag_engine/__init__.py:34`、`backend/business/rag_engine/core/__init__.py:7`

## B. 全仓无引用（仅本文件命中）

- `backend/infrastructure/github_link.py`  
  - 现象：`generate_github_url/get_display_title` 全仓无引用。

- `backend/infrastructure/vector_version_utils.py`  
  - 现象：版本化向量库工具函数全仓无引用。

- `backend/infrastructure/data_loader/github_import.py`  
  - 现象：同名能力已被 `data_loader.service/github_sync` 接管，本文件未被引用。

## C. UI 组件未被主入口使用

- `frontend/components/chat_input_with_mode.py`  
  - 现象：`render_chat_input_with_mode` 无引用。

- `frontend/components/sidebar.py`  
  - 现象：`render_sidebar` 无引用。

- `frontend/components/config_panel/panel.py:render_sidebar_config`  
  - 现象：仅定义未被调用（`render_advanced_config` 仍在使用）。

## D. 工具脚本专用（不在运行链路，暂保留）

- `backend/business/rag_engine/processing/keyword_extractor.py`  
  - 现象：仅被 `scripts/build_keyword_cloud.py` 动态导入使用（离线词云工具）。

## 额外疑点（需确认，暂保留）

（暂无）

---

## 自动扫描结果（2026-02-02）

本次全局静态扫描（AST import）未发现新的**高置信**“可安全删除”候选。  
扫描工具会将大量 `__init__.py`/入口脚本识别为“未使用”（属于误报），因此仅记录摘要：

- **tests-only 命中**：`backend.business.rag_api.rag_service`（疑似动态导入导致的误报）
- **未使用列表**：主要为各包的 `__init__.py` 与 `app.py` 入口（可忽略）

---

如果你希望我**直接清理**其中某几项，请告诉我优先级（例如：先删 UI 旧组件，再删 legacy engine），我可以逐项做“可回滚”的改动并补充回归检查。
