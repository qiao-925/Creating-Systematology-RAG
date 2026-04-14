# 终端化 UI 迭代（阶段存档）

**任务状态**：🔄 进行中（阶段归档）  
**归档日期**：2026-02-07  
**任务类型**：前端实现 / 视觉重构 / 交互优化

---

## 本阶段目标

- 将首页与对话区统一为终端风格（深色 + 绿色发光主题）。
- 优化标题区与设置/重置按钮的视觉一致性。
- 将“关键词探索”改为弹窗式“组词”流程，并增强可读性。
- 首屏布局改为“无对话时视觉居中，有对话时回归顶部”。

---

## 已完成内容

### 1) 标题与顶部控制区

- 移除标题左侧 `title-icon`，保留标题顶部留白。
- 标题文本采用 SVG 终端化风格。
- 设置按钮改为纯图标风格（无边框，融入背景）。
- 重置按钮替换为提供的 SVG 图标。

### 2) 首屏布局策略

- 新增首屏专属容器：
  - 无对话时：标题 + 输入区垂直居中。
  - 进入对话后：恢复顶部布局。
- 在“绝对居中”的基础上增加轻微上移，改善视觉重心。

### 3) 组词弹窗与文案中文化

- 入口按钮与弹窗命名：`关键词探索` → `组词`。
- 弹窗内部提示文案统一改为中文（含选择、生成、重新生成、状态提示）。
- 修复 `st.dialog` 非法 icon 问题（使用合法 emoji）。

### 4) 组词词云可视区增强

- 词云可视高度参数提升到大面板级别。
- 组件容器和 iframe 高度同步放大（含兼容性兜底）。
- 词云展示数量从 `30` 提升到 `90`，减少大面板留白。
- 增加组件 key 版本号，降低旧尺寸缓存影响。

### 5) 对话左右布局（进行中）

- 已加入 user/assistant 角色锚点。
- 已注入“用户右侧、助手左侧”的布局样式。
- 当前需要在真实页面继续观察选择器匹配稳定性并微调。

---

## 关键改动文件

- `frontend/main.py`
- `frontend/components/chat_display.py`
- `frontend/components/query_handler/__init__.py`
- `frontend/components/query_handler/streaming.py`
- `frontend/components/quick_start.py`
- `frontend/components/keyword_cloud.py`
- `frontend/config.py`
- `frontend/assets/icons/`（新增与替换 SVG 资源）

---

## 待办 / 下一步

1. 确认对话区最终左右布局（用户右、助手左）在当前 Streamlit 版本稳定生效。  
2. 验证组词词云在实际运行中“高度放大且内容铺满”是否达到预期（必要时再增密排布逻辑）。  
3. 统一顶部按钮间距、尺寸与 hover 反馈，完成最终视觉收口。

---

## 回滚与定位提示

- 若需回退居中策略：查看 `chat_display.py` 中 `landing_center_shell` 与 `_inject_landing_center_css()`。
- 若需回退组词面板高度：查看 `keyword_cloud.py` 中
  - `BUBBLE_CLOUD_HEIGHT_PX`
  - `BUBBLE_COMPONENT_HEIGHT_PX`
  - `KEYWORD_IFRAME_VERSION`
- 若需回退对话左右布局：查看 `main.py` 中 `stChatMessage` 相关 CSS 规则。

---

**归档说明**：本存档用于恢复上下文与继续迭代，不代表全部收尾完成。
