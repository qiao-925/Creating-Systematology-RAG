# 前端测试体系

## 概述

前端测试体系位于 `frontend/tests/` 目录，与 `frontend/` 代码结构完全对应，实现前后端测试分离，提高测试定位效率。

## 目录结构

```
frontend/tests/
├── __init__.py
├── conftest.py                    # 前端测试专用 fixtures
├── README.md                      # 本文档
├── test_main.py                   # 对应 frontend/main.py
├── components/                    # 对应 frontend/components/
│   ├── __init__.py
│   ├── test_sidebar.py           # 对应 frontend/components/sidebar.py
│   ├── test_chat_display.py      # 对应 frontend/components/chat_display.py
│   ├── test_quick_start.py       # 对应 frontend/components/quick_start.py
│   ├── test_session_loader.py    # 对应 frontend/components/session_loader.py
│   ├── test_file_viewer.py        # 对应 frontend/components/file_viewer.py
│   ├── test_query_handler.py     # 对应 frontend/components/query_handler.py
│   └── query_handler/            # 对应 frontend/components/query_handler/
│       ├── __init__.py
│       ├── test_streaming.py     # 对应 frontend/components/query_handler/streaming.py
│       └── test_non_streaming.py # 对应 frontend/components/query_handler/non_streaming.py
├── utils/                         # 对应 frontend/utils/
│   ├── __init__.py
│   ├── test_sources.py           # 对应 frontend/utils/sources.py
│   ├── test_cleanup.py            # 对应 frontend/utils/cleanup.py
│   ├── test_helpers.py            # 对应 frontend/utils/helpers.py
│   └── test_state.py             # 对应 frontend/utils/state.py
├── settings/                      # 对应 frontend/settings/
│   ├── __init__.py
│   ├── test_main.py              # 对应 frontend/settings/main.py
│   ├── test_data_source.py       # 对应 frontend/settings/data_source.py
│   ├── test_dev_tools.py         # 对应 frontend/settings/dev_tools.py
│   └── test_system_status.py     # 对应 frontend/settings/system_status.py
└── integration/                   # 前端集成测试
    ├── __init__.py
    ├── test_main_flow.py         # 主页面流程测试
    ├── test_query_flow.py        # 查询流程测试
    └── test_page_navigation.py   # 页面导航测试
```

## 文件映射关系

### 测试文件命名规范

- **规则**：`test_<源文件名>.py`
- **示例**：
  - `frontend/components/sidebar.py` → `frontend/tests/components/test_sidebar.py`
  - `frontend/utils/sources.py` → `frontend/tests/utils/test_sources.py`
  - `frontend/settings/main.py` → `frontend/tests/settings/test_main.py`

### 测试类命名规范

- **规则**：`Test<源文件名（首字母大写）>`
- **示例**：
  - `test_sidebar.py` → `TestSidebar`
  - `test_sources.py` → `TestSources`
  - `test_main.py` → `TestMain`

## 测试运行

### 运行所有前端测试

```bash
pytest frontend/tests/
```

### 运行特定测试文件

```bash
pytest frontend/tests/components/test_sidebar.py
```

### 运行特定测试类

```bash
pytest frontend/tests/components/test_sidebar.py::TestSidebar
```

### 运行特定测试方法

```bash
pytest frontend/tests/components/test_sidebar.py::TestSidebar::test_render_sidebar_structure
```

### 运行集成测试

```bash
pytest frontend/tests/integration/
```

## 测试分类

### 单元测试

- **位置**：`frontend/tests/components/`, `frontend/tests/utils/`, `frontend/tests/settings/`
- **目的**：测试单个组件或函数的独立功能
- **特点**：使用 Mock 隔离依赖，快速执行

### 集成测试

- **位置**：`frontend/tests/integration/`
- **目的**：测试多个组件协同工作的完整流程
- **特点**：验证组件间的交互和集成

## Fixtures

前端测试专用的 fixtures 定义在 `frontend/tests/conftest.py` 中：

- `mock_streamlit`: Mock Streamlit 模块
- `mock_session_state`: Mock Streamlit session_state
- `mock_rag_service`: Mock RAGService
- `mock_chat_manager`: Mock ChatManager
- `mock_index_manager`: Mock IndexManager

## 注意事项

1. **Mock Streamlit**：所有测试都需要 Mock Streamlit 组件，避免启动真实 Streamlit 服务器
2. **导入路径**：测试文件中的导入路径使用 `frontend.*`
3. **共享 Fixtures**：`frontend/tests/conftest.py` 可以导入 `tests/conftest.py` 的通用 fixtures
4. **测试发现**：pytest 会自动发现 `frontend/tests/` 中的测试

## 迁移历史

前端测试从 `tests/ui/` 和 `tests/regression/` 迁移而来，实现了：

- 前后端测试分离
- 测试结构与代码结构一致
- 命名规范统一
- 减少定位负担

## 相关文档

- 项目测试文档：`tests/README.md`
- 前端代码结构：`frontend/README.md`（如果有）

