"""
前端样式模块 - Claude风格设计系统
统一的CSS样式定义，供所有前端页面使用

主要功能：
- CLAUDE_STYLE_CSS: 完整的CSS样式定义，包含全局样式、组件样式等

特性：
- Claude风格设计系统
- 极简优雅的视觉风格
- 统一的颜色系统和字体规范
"""

CLAUDE_STYLE_CSS = """
<style>
/* ============================================================
   Claude风格设计系统 - 极简优雅
   
   目录索引：
   1. 全局基础样式（变量、重置、字体、标题）
   2. 布局样式（侧边栏、主内容区、弹窗）
   3. 组件样式（按钮、输入框、消息、选项卡等）
   4. 工具样式（滚动条、代码块、引用链接等）
   5. 特殊样式（底部工具栏）
   ============================================================ */

/* ============================================================
   1. 全局基础样式
   ============================================================ */

/* 1.1 CSS变量定义 */
:root {
    --color-bg-primary: #FFFFFF;
    --color-bg-sidebar: #FFFFFF;
    --color-bg-card: #FFFFFF;
    --color-bg-hover: #F5F5F5;
    --color-text-primary: #2C2C2C;
    --color-text-secondary: #6B6B6B;
    --color-accent: #2563EB;
    --color-accent-hover: #1D4ED8;
    --color-border: #E5E5E0;
    --color-border-light: #F0F0EB;
    
    /* Manus 风格配色 */
    --manus-bg-sidebar: #F8F9FA;
    --manus-bg-hover: #F0F1F2;
    --manus-bg-active: #E8E9EA;
    --manus-text-secondary: #6B7280;
    --manus-text-tertiary: #9CA3AF;
}

/* 1.2 全局重置 - 去除所有红色边框 */
*,
*::before,
*::after {
    --baseweb-error-color: var(--color-border) !important;
    --baseweb-focus-color: var(--color-accent) !important;
}

/* 1.3 全局focus状态处理 */
*:focus,
*:focus-visible,
*:focus-within,
*:active {
    outline: none !important;
    outline-color: transparent !important;
    box-shadow: none !important;
    border-color: var(--color-border) !important;
}

/* 特别覆盖Streamlit BaseWeb组件的红色边框 */
[data-baseweb] *:focus,
[data-baseweb] *:focus-visible,
[data-baseweb] *:focus-within {
    border-color: var(--color-border) !important;
}

/* 覆盖所有可能的红色边框（包括伪元素） */
*::before,
*::after {
    border-color: transparent !important;
}

/* 特别覆盖红色边框值 */
*[style*="border-color: red"],
*[style*="border-color: #ff0000"],
*[style*="border-color: #f00"],
*[style*="border-color: rgb(255, 0, 0)"],
*[style*="border-color: rgba(255, 0, 0"] {
    border-color: var(--color-border) !important;
}

/* 1.4 全局字体设置 */
.stApp {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial, sans-serif;
    background-color: var(--color-bg-primary);
    color: var(--color-text-primary);
    /* 优化rerun时的过渡效果，减少白屏感 */
    transition: opacity 0.2s ease-in-out;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* 1.5 基础元素样式 */
p, div, span {
    font-size: 16px;
    line-height: 1.7;
}

/* 标题层级 - 优雅的字重和间距 */
h1 {
    font-size: 2rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    color: var(--color-text-primary);
    margin-bottom: 0.75rem;
}

h2 {
    font-size: 1.5rem;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: var(--color-text-primary);
    margin-bottom: 0.5rem;
}

h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: 0.5rem;
}

/* 分隔线 */
hr {
    margin: 1.5rem 0;
    border: none;
    border-top: 1px solid var(--color-border);
}

/* ============================================================
   2. 布局样式
   ============================================================ */

/* 2.1 应用布局区域 */
.stApp > header {
    background-color: var(--color-bg-primary) !important;
}

.stApp > footer {
    background-color: var(--color-bg-primary) !important;
}

/* 2.2 主内容区域 */
.main .block-container {
    background-color: var(--color-bg-primary);
    padding-top: 2.5rem;
    max-width: 1200px !important;
    padding-bottom: 3rem;
    max-width: 100%;
}

/* 2.3 弹窗布局 */
div[data-testid="stDialog"] {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    z-index: 999 !important;
}

div[data-testid="stDialog"] div[role="dialog"] {
    width: 50vw !important;
    min-width: 600px !important;
    max-width: 90vw !important;
    margin: auto !important;
    position: relative !important;
    transform: none !important;
}

/* 2.4 侧边栏布局 */
[data-testid="stSidebar"] {
    background-color: var(--manus-bg-sidebar) !important;
    border-right: 1px solid var(--color-border);
    min-width: 280px !important;
    max-width: 600px !important;
    width: 373px !important;
    position: relative !important;
    display: flex !important;
    flex-direction: column !important;
    height: 100vh !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial, sans-serif !important;
}

/* 侧边栏内容区域（可滚动） */
[data-testid="stSidebar"] > div:first-child {
    flex: 1 !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    padding-bottom: 60px !important;
}

/* 侧边栏字体和间距 */
[data-testid="stSidebar"] .stMarkdown {
    font-size: 0.85rem !important;
    margin-top: 0.0625rem;
    margin-bottom: 0.0625rem;
    text-align: left !important;
}

[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    color: var(--color-text-primary);
    margin-top: 0.125rem;
    margin-bottom: 0.0625rem;
}

/* Manus 风格历史会话分组标题 */
.manus-group-title {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    color: var(--manus-text-tertiary) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    margin-top: 1rem !important;
    margin-bottom: 0.5rem !important;
    padding: 0 0.75rem !important;
    text-align: left !important;
}

.manus-group-title:first-child {
    margin-top: 0.5rem !important;
}

/* 历史会话按钮：统一简洁样式 */
[data-testid="stSidebar"] .stButton button[kind="secondary"] {
    /* 基础样式 */
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    padding: 0.5rem 0.75rem !important;
    margin: 0 !important;
    min-height: auto !important;
    height: auto !important;
    line-height: 1.4 !important;
    font-size: 0.8rem !important;
    text-align: left !important;
    justify-content: flex-start !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
    border-radius: 8px !important;
    transition: all 0.15s ease !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    color: var(--color-text-primary) !important;
    font-weight: 400 !important;
}

/* 历史会话按钮内部的 markdown 容器：完全去除间距 */
[data-testid="stSidebar"] .stButton button[kind="secondary"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] .stButton button[kind="secondary"] [data-testid="stMarkdownContainer"] *,
[data-testid="stSidebar"] .stButton button[kind="secondary"] p,
[data-testid="stSidebar"] .stButton button[kind="secondary"] div,
[data-testid="stSidebar"] .stButton button[kind="secondary"] .st-emotion-cache-17k2yau,
[data-testid="stSidebar"] .stButton button[kind="secondary"] .st-emotion-cache-17k2yau * {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.4 !important;
}

/* 未选中状态：悬停效果 */
[data-testid="stSidebar"] .stButton button[kind="secondary"]:not(:disabled):hover {
    background-color: var(--manus-bg-hover) !important;
}

/* 选中状态：使用disabled按钮显示选中样式 */
[data-testid="stSidebar"] .stButton button[kind="secondary"]:disabled {
    background-color: var(--manus-bg-active) !important;
    color: var(--manus-text-secondary) !important;
    font-weight: 500 !important;
    cursor: default !important;
    opacity: 1 !important;
}

/* 侧边栏历史会话区域间距控制 */
[data-testid="stSidebar"] .element-container div {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}

[data-testid="stSidebar"] .element-container {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

[data-testid="stSidebar"] .element-container > div,
[data-testid="stSidebar"] .element-container > div > div,
[data-testid="stSidebar"] .element-container .stButton,
[data-testid="stSidebar"] .element-container .stButton > * {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

[data-testid="stSidebar"] .element-container + .element-container {
    margin-top: 0 !important;
}

[data-testid="stSidebar"] .element-container .stButton + .stButton,
[data-testid="stSidebar"] .element-container .stButton ~ .stButton {
    margin-top: 0 !important;
}

[data-testid="stSidebar"] .element-container * {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}

/* ============================================================
   3. 组件样式
   ============================================================ */

/* 3.1 聊天消息组件 */
.stChatMessage {
    padding: 1.0rem 1.25rem;
    border-radius: 12px;
    margin-bottom: 0.9rem;
    margin-left: auto !important;
    margin-right: auto !important;
    max-width: 100% !important;
    width: 100% !important;
    border: none;
    box-shadow: none;
    background-color: var(--color-bg-card);
    flex-direction: row !important;
    align-items: flex-start !important;
}

/* 用户消息 */
.stChatMessage[data-testid="user-message"] {
    background-color: var(--color-bg-hover);
}

/* AI消息 */
.stChatMessage[data-testid="assistant-message"] {
    background-color: var(--color-bg-primary);
}

/* 消息头像和内容区域布局 */
.stChatMessage > div:first-child {
    width: auto !important;
    max-width: 3rem !important;
    min-width: 3rem !important;
    flex-shrink: 0 !important;
    flex-grow: 0 !important;
}

.stChatMessage img,
.stChatMessage svg,
.stChatMessage [data-testid="stAvatar"],
.stChatMessage > div:first-child img,
.stChatMessage > div:first-child svg {
    width: 2.5rem !important;
    height: 2.5rem !important;
    max-width: 2.5rem !important;
    max-height: 2.5rem !important;
    min-width: 2.5rem !important;
    min-height: 2.5rem !important;
    flex-shrink: 0 !important;
}

.stChatMessage > div:not(:first-child) {
    flex: 1 !important;
    width: auto !important;
    max-width: 100% !important;
}

.stChatMessage > div[data-testid="stChatMessageContent"],
.stChatMessage > div > div[data-testid="stChatMessageContent"] {
    flex: 1 !important;
    width: 100% !important;
    max-width: 100% !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
}

/* 消息内容文字样式 */
[data-testid="stChatMessageContent"] {
    font-size: 16px;
    line-height: 1.7;
    color: var(--color-text-primary);
    width: 100% !important;
    max-width: 100% !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}

/* 列布局中的消息对齐 */
[data-testid="column"] .stChatMessage,
[data-testid="column"] .stChatMessage[data-testid="user-message"],
[data-testid="column"] .stChatMessage[data-testid="assistant-message"] {
    margin-left: 0 !important;
    margin-right: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
}

/* 3.2 按钮组件 */
.stButton button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s ease;
    border: none;
    box-shadow: none;
    font-family: inherit;
}

/* 主要按钮 */
.stButton button[kind="primary"] {
    background-color: var(--color-accent);
    color: white;
    border: none;
}

.stButton button[kind="primary"]:hover {
    background-color: var(--color-accent-hover);
    transform: none;
    box-shadow: none;
}

/* 次要按钮 */
.stButton button[kind="secondary"] {
    background-color: transparent;
    border: 1px solid var(--color-border);
    color: var(--color-text-primary);
}

.stButton button[kind="secondary"]:hover {
    background-color: var(--color-bg-hover);
    border-color: var(--color-border);
}

/* 侧边栏中的按钮样式 */
[data-testid="stSidebar"] .stButton {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

[data-testid="stSidebar"] .element-container .stButton button {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}

/* 侧边栏主要按钮 */
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] .stButton button[kind="primary"]:hover,
[data-testid="stSidebar"] .stButton button[kind="primary"]:active,
[data-testid="stSidebar"] .stButton button[kind="primary"]:focus {
    padding: 0.65rem 1rem !important;
    margin: 0.25rem 0 !important;
    min-height: 2.5rem !important;
    font-size: 0.875rem !important;
    font-weight: 600 !important;
    line-height: 1.4 !important;
    white-space: nowrap !important;
    overflow: visible !important;
    text-overflow: clip !important;
}

/* 历史会话按钮 */
[data-testid="stSidebar"] .stButton button[kind="secondary"] {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    padding: 0.5rem 0.75rem !important;
    margin: 0 !important;
    min-height: auto !important;
    height: auto !important;
    line-height: 1.4 !important;
    font-size: 0.8rem !important;
    text-align: left !important;
    justify-content: flex-start !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
    border-radius: 8px !important;
    transition: all 0.15s ease !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    color: var(--color-text-primary) !important;
    font-weight: 400 !important;
}

[data-testid="stSidebar"] .stButton button[kind="secondary"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] .stButton button[kind="secondary"] [data-testid="stMarkdownContainer"] *,
[data-testid="stSidebar"] .stButton button[kind="secondary"] p,
[data-testid="stSidebar"] .stButton button[kind="secondary"] div,
[data-testid="stSidebar"] .stButton button[kind="secondary"] .st-emotion-cache-17k2yau,
[data-testid="stSidebar"] .stButton button[kind="secondary"] .st-emotion-cache-17k2yau * {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.4 !important;
}

[data-testid="stSidebar"] .stButton button[kind="secondary"]:not(:disabled):hover {
    background-color: var(--manus-bg-hover) !important;
}

[data-testid="stSidebar"] .stButton button[kind="secondary"]:disabled {
    background-color: var(--manus-bg-active) !important;
    color: var(--manus-text-secondary) !important;
    font-weight: 500 !important;
    cursor: default !important;
    opacity: 1 !important;
}

/* Manus 风格历史会话分组标题 */
.manus-group-title {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    color: var(--manus-text-tertiary) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    margin-top: 1rem !important;
    margin-bottom: 0.5rem !important;
    padding: 0 0.75rem !important;
    text-align: left !important;
}

.manus-group-title:first-child {
    margin-top: 0.5rem !important;
}

/* 3.3 输入框组件 */
.stTextInput input, 
.stTextArea textarea {
    border-radius: 8px;
    border: 1px solid var(--color-border) !important;
    padding: 0.75rem 1rem;
    background-color: var(--color-bg-primary);
    font-size: 16px;
    font-family: inherit;
    color: var(--color-text-primary);
    min-height: 48px;
    resize: none;
}

.stTextInput input:focus, 
.stTextArea textarea:focus,
.stTextInput input:focus-visible,
.stTextArea textarea:focus-visible,
.stTextInput input:active,
.stTextArea textarea:active,
.stTextInput input:focus-within,
.stTextArea textarea:focus-within {
    border-color: var(--color-border) !important;
}

.stTextInput input:invalid,
.stTextArea textarea:invalid,
.stTextInput input:valid,
.stTextArea textarea:valid {
    border-color: var(--color-border) !important;
}

/* 3.4 展开器组件 */
.streamlit-expanderHeader {
    background-color: var(--color-bg-primary);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    border: 1px solid var(--color-border-light);
    transition: all 0.2s ease;
}

.streamlit-expanderHeader:hover {
    background-color: var(--color-bg-hover);
    border-color: var(--color-border);
}

.streamlit-expanderContent {
    background-color: var(--color-bg-primary);
    border: none;
    padding: 1rem;
}

/* 3.5 选项卡组件 */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 1px solid var(--color-border) !important;
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
}

/* 标签页基础样式 - 移除所有边框 */
.stTabs [data-baseweb="tab"],
.stTabs [data-baseweb="tab"] *,
.stTabs [data-baseweb="tab"]::before,
.stTabs [data-baseweb="tab"]::after {
    border: none !important;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 0.75rem 1.5rem;
    color: var(--color-text-secondary);
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: var(--color-bg-hover);
    color: var(--color-text-primary);
    border: none !important;
    border-bottom: none !important;
}

/* 选中状态的标签页 - 只保留一条蓝色下划线 */
.stTabs [aria-selected="true"] {
    background-color: var(--color-bg-card);
    color: var(--color-text-primary);
    border: none !important;
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
    border-bottom: 2px solid var(--color-accent) !important;
}

/* 选中标签页的内部元素和伪元素也移除边框 */
.stTabs [aria-selected="true"] *,
.stTabs [aria-selected="true"]::before,
.stTabs [aria-selected="true"]::after {
    border: none !important;
}

/* 选项卡focus状态 - 继承全局focus规则 */
.stTabs [data-baseweb="tab"]:focus::before,
.stTabs [data-baseweb="tab"]:focus::after,
.stTabs [data-baseweb="tab"]:focus-visible::before,
.stTabs [data-baseweb="tab"]:focus-visible::after {
    border: none !important;
}

/* 确保选中状态的标签页只有蓝色下划线 */
.stTabs [aria-selected="true"]:focus,
.stTabs [aria-selected="true"]:focus-visible,
.stTabs [aria-selected="true"]:focus-within,
.stTabs [aria-selected="true"]:active,
.stTabs [data-baseweb="tab"][aria-selected="true"]:focus,
.stTabs [data-baseweb="tab"][aria-selected="true"]:focus-visible,
.stTabs [data-baseweb="tab"][aria-selected="true"]:focus-within,
.stTabs [data-baseweb="tab"][aria-selected="true"]:active {
    border: none !important;
    border-bottom: 2px solid var(--color-accent) !important;
}

/* 文件上传器 */
[data-testid="stFileUploader"] {
    border: 1px dashed var(--color-border);
    border-radius: 8px;
    padding: 1.5rem;
    background-color: var(--color-bg-card);
}

/* 下拉选择框 */
.stSelectbox [data-baseweb="select"] {
    border-radius: 8px;
    border: 1px solid var(--color-border);
}

.stSelectbox [data-baseweb="select"]:focus {
    border-color: var(--color-border) !important;
    box-shadow: none !important;
    outline: none !important;
}

/* Checkbox */
.stCheckbox {
    color: var(--color-text-primary);
}

/* Spinner加载动画 */
.stSpinner > div {
    border-top-color: var(--color-accent) !important;
}

/* 引用链接样式 */
a[href^="#citation_"] {
    color: var(--color-accent) !important;
    text-decoration: none !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    padding: 0.1em 0.2em !important;
    border-radius: 3px !important;
    background-color: rgba(37, 99, 235, 0.1) !important;
}

a[href^="#citation_"]:hover {
    background-color: rgba(37, 99, 235, 0.2) !important;
    color: var(--color-accent-hover) !important;
    text-decoration: underline !important;
}

/* 引用锚点高亮效果 */
[id^="citation_"] {
    transition: background-color 0.3s ease !important;
    border-radius: 4px !important;
    padding: 0.25rem 0.5rem !important;
    margin: -0.25rem -0.5rem !important;
}

/* ============================================================
   Manus 风格底部固定工具栏
   ============================================================ */

/* 底部固定工具栏 - 宽度跟随侧边栏 */
.manus-sidebar-footer {
    position: fixed !important;
    bottom: 0 !important;
    left: 0 !important;
    width: 373px !important;
    height: 48px !important;
    background-color: var(--manus-bg-sidebar) !important;
    border-top: 1px solid var(--color-border) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    padding: 0 8px !important;
    gap: 4px !important;
    z-index: 100 !important;
    box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05) !important;
}

/* 底部工具栏中的按钮 */
.manus-sidebar-footer .stButton {
    margin: 0 !important;
    padding: 0 !important;
}

.manus-sidebar-footer .stButton button {
    width: 32px !important;
    height: 32px !important;
    min-height: 32px !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    background-color: transparent !important;
    border-radius: 6px !important;
    color: var(--manus-text-secondary) !important;
    font-size: 18px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s ease !important;
}

.manus-sidebar-footer .stButton button:hover {
    background-color: var(--manus-bg-hover) !important;
    color: var(--color-text-primary) !important;
}

.manus-sidebar-footer .stButton button:active {
    transform: scale(0.95) !important;
}

.manus-sidebar-footer .stButton button:disabled {
    opacity: 0.4 !important;
    cursor: not-allowed !important;
}

</style>
"""


