---
name: frontend-development
description: 前端开发规范，包含 Streamlit 原生组件优先使用和 UI 自然语言编辑。适用于 frontend/** 目录内的前端开发。
---

# 前端开发规范

> 优先使用 Streamlit 原生组件，避免不必要的自定义组件。

---

## ⚠️ 核心强制要求

**优先使用 Streamlit 原生组件**

- 所有前端功能**必须**首先考虑使用原生组件
- 只有在原生组件**确实无法满足**需求时，才考虑自定义组件
- 使用自定义组件前**必须**向用户说明原因并获得确认

---

## AI Agent 行为要求

### 开发新功能时

1. **必须**首先查阅 Streamlit API 参考
2. **必须**优先尝试使用原生组件
3. 如果原生组件无法满足需求，**必须**：
   - 说明原生组件的局限性
   - 提出替代方案
   - **等待用户确认**

### 代码审查时

- 检查是否使用了不必要的自定义组件
- 发现时提供原生组件替换建议

---

## 常用原生组件速查

| 类别 | 组件 |
|------|------|
| 文本 | `st.write`, `st.markdown`, `st.title`, `st.header` |
| 输入 | `st.text_input`, `st.selectbox`, `st.slider`, `st.checkbox` |
| 布局 | `st.columns`, `st.tabs`, `st.expander`, `st.sidebar` |
| 聊天 | `st.chat_input`, `st.chat_message` |
| 反馈 | `st.spinner`, `st.progress`, `st.toast`, `st.error` |

---

## UI 自然语言编辑

**脚本**：`scripts/browser_edit.py`

**示例**：`/browser-edit 调整聊天输入框圆角为 20px`

---

## 参考资料

- `references/streamlit-components.md` - Streamlit 原生组件详细说明
- `references/ui-natural-language-editing.md` - UI 自然语言编辑详细说明
