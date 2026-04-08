# UI布局重构 - 参考 Streamlit AI Assistant

> 参考目标：https://demo-ai-assistant.streamlit.app/  
> 源码：https://github.com/streamlit/demo-ai-assistant/blob/main/streamlit_app.py

---

## Checkpoint 状态表

| CP | 名称 | 状态 | 完成日期 |
|----|------|------|----------|
| CP1 | 移除侧边栏，建立单列居中布局 | ✅ 已完成 | 2026-01-31 |
| CP2 | 重构标题区域与 Restart 按钮 | ✅ 已完成 | 2026-01-31 |
| CP3 | 重构初始界面（建议问题 pills + 输入框） | ✅ 已完成 | 2026-01-31 |
| CP4 | 重构对话界面（气泡 + 底部输入） | ✅ 已完成 | 2026-01-31 |
| CP5 | 设置入口迁移与收尾测试 | ✅ 已完成 | 2026-01-31 |

---

## 背景与目标

### 背景

当前项目采用左右双栏布局（侧边栏 + 主内容区），参考 Streamlit 官方 AI Assistant Demo 后，发现其单列居中布局更加简洁清晰，交互逻辑一目了然。

### 目标

1. **抛弃侧边栏设计** → 采用单列居中布局
2. **标题居中** → 类似目标页面的风格
3. **设置按钮另找位置** → 放在标题行右侧
4. **"开启新对话"改为 Restart** → 功能相同，位置改到标题行

### 非目标（明确排除）

- 不改动后端逻辑
- 不改动 RAG 查询流程
- 不改动对话历史持久化逻辑
- 暂不实现历史会话列表（后续可考虑弹窗或独立页面）

---

## 技术方案

### 决策点：历史会话功能处理

**背景**：当前历史会话列表在侧边栏，移除侧边栏后需要决定如何处理。

**选项**：
1. **完全移除**：简化 MVP，后续再考虑
2. **迁移到弹窗/dialog**：保留功能，入口改为按钮触发弹窗
3. **迁移到独立页面**：使用 `st.Page` 多页面结构

**决策**：选择 **选项 1 - 完全移除**

**理由**：
- 参考目标页面也没有历史会话列表
- 简化首次重构范围，聚焦核心布局
- 后续可根据需要再添加

**日期**：2026-01-31

---

## 当前实现现状（以代码为准）

### 入口与整体渲染顺序

- **入口文件**：`frontend/main.py`
- **渲染顺序**：
  - 注入 `_CUSTOM_CSS`
  - `init_session_state()` 初始化 UI 状态
  - 启动 `preloader` 后台预加载（`frontend/utils/preloader.py`）
  - 获取 `rag_service/chat_manager` 后：
    - `render_chat_interface(rag_service, chat_manager)` 负责 UI
    - `handle_user_queries(rag_service, chat_manager)` 负责输入/触发查询

### 布局结构（参考目标 demo）

- **单列居中**：通过 `frontend/main.py` 中 `.block-container { max-width: 800px; }` 实现
- **标题行 + Restart + 设置**：由 `frontend/components/chat_display.py:_render_title_row()` 渲染
- **无侧边栏**：当前入口未挂载 `frontend/components/sidebar.py:render_sidebar()`

### 首屏（无消息）逻辑

- 文件：`frontend/components/quick_start.py`
- 逻辑：
  - 输入框：`st.chat_input(..., key="initial_question")`
  - 建议问题：`st.pills(..., key="selected_suggestion")`
  - 一旦输入/点击：
    - 追加用户消息到 `st.session_state.messages`
    - 设置 `st.session_state.pending_query`，交给 query_handler 统一处理

### 有消息时的对话显示

- 文件：`frontend/components/chat_display.py`
- `render_chat_history()` 渲染 `st.session_state.messages`（`streamlit_chat.message` 气泡）
- assistant 消息支持：
  - 引用来源（sources）
  - 推理链（reasoning_content）
  - 可观测性扩展块（continuation）

### 用户输入与查询触发（统一路由）

- 文件：`frontend/components/query_handler/__init__.py:handle_user_queries()`
- 优先级：
  - `pending_query`（首屏输入/建议问题）-> 执行查询 -> `st.rerun()`
  - `selected_question`（其他点击填充场景）-> 执行查询 -> `st.rerun()`
  - `main_chat_input`（有历史时的主输入组件）-> 执行查询（避免不必要 rerun）

### 查询执行（非流式）

- 文件：`frontend/components/query_handler/non_streaming.py:handle_non_streaming_query()`
- 行为：
  - `rag_service.query(...)`
  - 保存到 `st.session_state.messages`（UI 事实源）
  - 同步写入 `chat_manager`（会话持久化/历史）
  - 渲染 assistant 气泡 + continuation

### 设置入口与配置重建

- **设置弹窗**：`frontend/components/settings_dialog.py:show_settings_dialog()`
- **配置变更触发重建**：`frontend/utils/state.py:rebuild_services()`
  - 读取 session_state 中的配置（模型、检索策略、top_k/threshold、rerank、agentic 等）
  - 重建 `RAGService` 与 `ChatManager` 并写回 `init_result.instances`

### 历史会话加载（注意：功能仍存在）

- 文件：`frontend/components/session_loader.py:load_history_session()`
- 触发方式：当 `st.session_state.load_session_id` 或 `session_loading_pending` 存在时
- 行为：
  - 从 `SESSIONS_PATH/default/{session_id}.json` 加载
  - 将历史转换为 `st.session_state.messages`
  - 同步构建 `current_sources_map/current_reasoning_map`

---

## 实施步骤

### CP1：移除侧边栏，建立单列居中布局

**目标**：将 `layout="wide"` 改为居中布局，移除侧边栏渲染调用。

**验收标准**：
- [ ] 页面无侧边栏
- [ ] 主内容区居中显示
- [ ] 应用可正常启动

**预计文件改动**：

| 文件 | 职责 | 行数预算 |
|------|------|----------|
| `frontend/config.py` | 修改 `set_page_config` 参数 | ≤120 |
| `frontend/main.py` | 移除 `render_sidebar` 调用，调整 CSS | ≤300 |

---

### CP2：重构标题区域与 Restart 按钮

**目标**：标题居中，右侧放置 Restart 和设置按钮。

**验收标准**：
- [ ] 标题居中显示
- [ ] Restart 按钮可用，点击后清空对话
- [ ] 设置按钮可用，点击后弹出设置弹窗

**预计文件改动**：

| 文件 | 职责 | 行数预算 |
|------|------|----------|
| `frontend/main.py` | 新增标题行渲染逻辑 | ≤300 |
| `frontend/components/chat_display.py` | 移除原标题显示 | ≤160 |

---

### CP3：重构初始界面（建议问题 pills + 输入框）

**目标**：无对话时显示建议问题（使用 `st.pills`）和输入框。

**验收标准**：
- [ ] 初始界面显示建议问题 pills
- [ ] 点击 pills 可触发对应问题
- [ ] 输入框正常工作

**预计文件改动**：

| 文件 | 职责 | 行数预算 |
|------|------|----------|
| `frontend/components/quick_start.py` | 重构为 pills 风格 | ≤80 |
| `frontend/config.py` | 调整建议问题配置 | ≤120 |

---

### CP4：重构对话界面（气泡 + 底部输入）

**目标**：有对话时显示对话气泡，输入框在底部。

**验收标准**：
- [ ] 对话气泡正常显示
- [ ] 输入框固定在底部
- [ ] 发送消息后正常追加到对话

**预计文件改动**：

| 文件 | 职责 | 行数预算 |
|------|------|----------|
| `frontend/components/chat_display.py` | 调整对话渲染逻辑 | ≤160 |
| `frontend/components/chat_input_with_mode.py` | 简化输入组件 | ≤150 |

---

### CP5：设置入口迁移与收尾测试

**目标**：确保设置弹窗可正常打开，整体功能可用。

**验收标准**：
- [ ] 设置弹窗可正常打开和关闭
- [ ] 完整对话流程可正常运行
- [ ] 无控制台错误

**预计文件改动**：

| 文件 | 职责 | 行数预算 |
|------|------|----------|
| `frontend/main.py` | 集成设置弹窗触发逻辑 | ≤300 |
| `frontend/components/settings_dialog.py` | 无需改动（复用） | - |

---

## 风险与注意事项
 
 1. **历史会话入口不明确**：历史会话加载逻辑仍存在，但当前入口未挂载侧边栏时，需要提供独立入口来写入 `load_session_id` 触发加载
 2. **CSS 调整可能影响其他样式**：需仔细测试暗色主题下的显示效果
 3. **热重载兼容性**：确保 `_services_cached` 逻辑在新布局下仍正常工作
 
---

## 参考资料

- 目标页面：https://demo-ai-assistant.streamlit.app/
- 源码：https://github.com/streamlit/demo-ai-assistant/blob/main/streamlit_app.py
