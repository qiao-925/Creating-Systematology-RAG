# 聊天历史间距调整 - 快速摘要

- 日期：2025-10-31
- 任务：减小聊天历史每条消息上下间距
- 文档类型：快速摘要

## 做了什么
- 调小聊天消息气泡的内边距与相邻间距，使历史列表更紧凑：
  - `.stChatMessage` padding：1.5rem→1.0rem（左右 1.25rem）
  - `.stChatMessage` margin-bottom：1.5rem→0.9rem

## 关键改动
- 文件：`app.py`
  - CSS 中 `.stChatMessage` 样式的 padding 与 margin-bottom。

## 预期效果
- 每条消息之间的上下空白更小，滚动密度更高，视觉更紧凑。
