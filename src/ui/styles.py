"""
UI样式模块 - Claude风格设计系统
统一的CSS样式定义，供所有页面使用
"""

CLAUDE_STYLE_CSS = """
<style>
/* ============================================================
   Claude风格设计系统 - 极简优雅
   ============================================================ */

/* 弹窗大小优化 - 至少占页面的一半，并居中显示 */
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

/* 全局字体和配色 */
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
}

/* 全局字体 - 衬线字体增强可读性 */
.stApp {
    font-family: "Noto Serif SC", "Source Han Serif SC", "Georgia", "Times New Roman", serif;
    background-color: var(--color-bg-primary);
    color: var(--color-text-primary);
    /* 优化rerun时的过渡效果，减少白屏感 */
    transition: opacity 0.2s ease-in-out;
}

/* 顶部区域 */
.stApp > header {
    background-color: var(--color-bg-primary) !important;
}

/* 底部区域 */
.stApp > footer {
    background-color: var(--color-bg-primary) !important;
}

/* 主内容区域背景 */
.main .block-container {
    background-color: var(--color-bg-primary);
}

/* 主内容区域 */
.main .block-container {
    padding-top: 2.5rem;
    max-width: 1200px !important;
    padding-bottom: 3rem;
    max-width: 100%;
}

/* 正文字体大小和行高 */
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

/* 侧边栏中的标题间距更紧凑 */
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    margin-top: 0.125rem;
    margin-bottom: 0.0625rem;
}

/* 侧边栏中的markdown间距更紧凑 */
[data-testid="stSidebar"] .stMarkdown {
    margin-top: 0.0625rem;
    margin-bottom: 0.0625rem;
}

/* 侧边栏中的div间距更紧凑 */
[data-testid="stSidebar"] div {
    margin-top: 0.0625rem;
    margin-bottom: 0.0625rem;
}

/* 侧边栏 - 温暖的米色背景 */
[data-testid="stSidebar"] {
    background-color: var(--color-bg-sidebar);
    border-right: 1px solid var(--color-border);
    width: 280px !important;
}

[data-testid="stSidebar"] .stMarkdown {
    font-size: 0.9rem;
}

[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    color: var(--color-text-primary);
}

/* 消息容器 - 紧凑间距 */
.stChatMessage {
    padding: 1.0rem 1.25rem;
    border-radius: 12px;
    margin-bottom: 0.9rem;
    border: none;
    box-shadow: none;
    background-color: var(--color-bg-card);
}

/* 用户消息 - 浅米色背景 */
.stChatMessage[data-testid="user-message"] {
    background-color: var(--color-bg-hover);
}

/* AI消息 - 温暖米色背景 */
.stChatMessage[data-testid="assistant-message"] {
    background-color: var(--color-bg-primary);
}

/* 消息内容文字 */
[data-testid="stChatMessageContent"] {
    font-size: 16px;
    line-height: 1.7;
    color: var(--color-text-primary);
}

/* 按钮 - 温暖的强调色 */
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

/* 侧边栏历史记录按钮容器：彻底去除所有间距 */
[data-testid="stSidebar"] .stButton,
[data-testid="stSidebar"] .stButton *,
[data-testid="stSidebar"] > div > div > .stButton,
[data-testid="stSidebar"] > div > div > div > .stButton {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    line-height: 1.2 !important;
}

/* 侧边栏历史记录按钮：单行显示 + 超出省略 + 紧凑样式（仅针对secondary按钮） */
[data-testid="stSidebar"] .stButton button[kind="secondary"] {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin: 0 !important;
    padding: 0.15rem 0.4rem !important;
    min-height: auto !important;
    height: auto !important;
    line-height: 1.3 !important;
}

/* 侧边栏历史记录按钮（secondary）：去边框框线，紧凑间距，所有状态一致 */
[data-testid="stSidebar"] .stButton button[kind="secondary"],
[data-testid="stSidebar"] .stButton button[kind="secondary"]:hover,
[data-testid="stSidebar"] .stButton button[kind="secondary"]:active,
[data-testid="stSidebar"] .stButton button[kind="secondary"]:focus,
[data-testid="stSidebar"] .stButton button[kind="secondary"]:focus-visible {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    padding: 0.15rem 0.4rem !important;
    margin: 0.0625rem 0 !important;
    min-height: auto !important;
    height: auto !important;
    line-height: 1.3 !important;
}

[data-testid="stSidebar"] .stButton button[kind="secondary"]:hover {
    background-color: var(--color-bg-hover) !important;
}

/* 保持顶部主要按钮的可点击性和视觉权重 - 确保足够大 */
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] .stButton button[kind="primary"]:hover,
[data-testid="stSidebar"] .stButton button[kind="primary"]:active,
[data-testid="stSidebar"] .stButton button[kind="primary"]:focus {
    padding: 0.65rem 1rem !important;
    margin: 0.25rem 0 !important;
    min-height: 2.5rem !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    line-height: 1.4 !important;
    white-space: nowrap !important;
    overflow: visible !important;
    text-overflow: clip !important;
}

/* 输入框 - 简洁边框 */
.stTextInput input, 
.stTextArea textarea,
.stChatInput textarea {
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

/* 去除所有focus状态的红色和蓝色边框 */
.stTextInput input:focus, 
.stTextArea textarea:focus,
.stChatInput textarea:focus,
.stTextInput input:focus-visible,
.stTextArea textarea:focus-visible,
.stChatInput textarea:focus-visible,
.stTextInput input:active,
.stTextArea textarea:active,
.stChatInput textarea:active {
    border-color: var(--color-border) !important;
    box-shadow: none !important;
    outline: none !important;
}

/* 去除所有invalid/valid状态的红色边框 */
.stTextInput input:invalid,
.stTextArea textarea:invalid,
.stChatInput textarea:invalid,
.stTextInput input:valid,
.stTextArea textarea:valid,
.stChatInput textarea:valid {
    border-color: var(--color-border) !important;
    box-shadow: none !important;
    outline: none !important;
}

/* 聊天输入框 - 简化样式，去除多余装饰 */
.stChatInput {
    max-width: 900px !important;
    margin: 0 auto !important;
}

[data-testid="stChatInput"] {
    max-width: 900px !important;
    margin: 0 auto !important;
    background: var(--color-bg-primary) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: 8px !important;
    padding: 0.5rem !important;
}

/* DeepSeek风格文本输入框样式 - 在居中列中 */
.stTextArea {
    width: 100% !important;
}

.stTextArea {
    position: relative !important;
}

.stTextArea > div {
    background: #FFFFFF !important;
    border: 1px solid var(--color-border) !important;
    border-radius: 12px !important;
    padding: 0.5rem 3rem 0.5rem 1rem !important;  /* 右侧留出空间给发送按钮 */
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    transition: all 0.2s ease !important;
    position: relative !important;
}

.stTextArea > div:focus-within {
    border-color: var(--color-accent) !important;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1) !important;
}

.stTextArea textarea {
    min-height: 40px !important;
    max-height: 150px !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 0.5rem 0 !important;
    font-size: 16px !important;
    line-height: 1.5 !important;
    resize: vertical !important;
    background: transparent !important;
    color: var(--color-text-primary) !important;
}

.stTextArea textarea::placeholder {
    color: #9CA3AF !important;
}

.stTextArea textarea:focus {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}

/* 发送按钮嵌入到输入框内部 - 使用绝对定位 */
.stTextArea ~ .stColumn:has(button[data-testid*="send"]),
.stTextArea ~ .stColumn:has(button[data-testid*="main_chat_input_send"]) {
    position: absolute !important;
    right: 0.75rem !important;
    bottom: 0.5rem !important;
    z-index: 10 !important;
    width: auto !important;
    margin: 0 !important;
    padding: 0 !important;
}

.stTextArea ~ .stColumn:has(button[data-testid*="send"]) .stButton,
.stTextArea ~ .stColumn:has(button[data-testid*="main_chat_input_send"]) .stButton {
    margin: 0 !important;
    padding: 0 !important;
}

/* 发送按钮样式（圆形，浅蓝色，白色向上箭头）- 嵌入到输入框内 */
button[data-testid*="send"],
button[data-testid*="main_chat_input_send"] {
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    min-height: 32px !important;
    max-width: 32px !important;
    max-height: 32px !important;
    border-radius: 50% !important;
    background: #3B82F6 !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
    transition: all 0.2s ease !important;
    font-size: 16px !important;
    color: white !important;
    font-weight: 600 !important;
    flex-shrink: 0 !important;
}

button[data-testid*="send"]:hover,
button[data-testid*="main_chat_input_send"]:hover {
    background: #2563EB !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15) !important;
    transform: translateY(-1px) !important;
}

button[data-testid*="send"]:active,
button[data-testid*="main_chat_input_send"]:active {
    transform: translateY(0) !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
}

button[data-testid*="send"]:focus,
button[data-testid*="main_chat_input_send"]:focus {
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
}

button[data-testid*="send"]:disabled,
button[data-testid*="main_chat_input_send"]:disabled {
    background: #D1D5DB !important;
    cursor: not-allowed !important;
    transform: none !important;
}

/* 去除聊天输入框的所有状态颜色（包括focus、active、invalid等） */
[data-testid="stChatInput"]:focus,
[data-testid="stChatInput"]:focus-within,
[data-testid="stChatInput"]:active,
[data-testid="stChatInput"]:hover {
    border-color: var(--color-border) !important;
    box-shadow: none !important;
    outline: none !important;
}

/* 去除聊天输入框内部textarea的所有状态 */
[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInput"] textarea:focus-visible,
[data-testid="stChatInput"] textarea:active,
[data-testid="stChatInput"] textarea:invalid,
[data-testid="stChatInput"] textarea:valid {
    border-color: var(--color-border) !important;
    box-shadow: none !important;
    outline: none !important;
}

/* 发送按钮样式 */
[data-testid="stChatInput"] button {
    background-color: var(--color-accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.5rem 0.9rem !important;
}

[data-testid="stChatInput"] button:hover {
    background-color: var(--color-accent-hover) !important;
}

/* 展开器 - 极简设计，使用温暖米色 */
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

/* 分隔线 */
hr {
    margin: 1.5rem 0;
    border: none;
    border-top: 1px solid var(--color-border);
}

/* 提示文字 */
.stCaption {
    color: var(--color-text-secondary);
    font-size: 0.875rem;
    line-height: 1.5;
}

/* 指标卡片 */
[data-testid="stMetric"] {
    background-color: var(--color-bg-card);
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid var(--color-border-light);
    box-shadow: none;
}

[data-testid="stMetric"] label {
    color: var(--color-text-secondary);
    font-size: 0.875rem;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--color-text-primary);
    font-weight: 600;
}

/* 提示消息 - 统一灰色系配色，去除红蓝黄绿 */
.stSuccess, .stError, .stInfo, .stWarning {
    border-radius: 8px;
    padding: 1rem;
    border: 1px solid var(--color-border) !important;
    background-color: var(--color-bg-primary) !important;
    color: var(--color-text-primary) !important;
}

/* 去除Streamlit默认的彩色图标和背景 */
.stSuccess [data-testid="stMarkdownContainer"] p,
.stError [data-testid="stMarkdownContainer"] p,
.stInfo [data-testid="stMarkdownContainer"] p,
.stWarning [data-testid="stMarkdownContainer"] p {
    color: var(--color-text-primary) !important;
}

/* 去除彩色图标 */
.stSuccess [data-testid="stIcon"],
.stError [data-testid="stIcon"],
.stInfo [data-testid="stIcon"],
.stWarning [data-testid="stIcon"] {
    color: var(--color-text-secondary) !important;
}

/* 去除所有彩色背景和边框 */
.stSuccess > div,
.stError > div,
.stInfo > div,
.stWarning > div {
    background-color: transparent !important;
}

/* 代码块 */
code {
    font-family: "JetBrains Mono", "Fira Code", "Courier New", monospace;
    background-color: var(--color-bg-hover);
    padding: 0.2em 0.4em;
    border-radius: 4px;
    font-size: 0.9em;
}

pre code {
    padding: 1rem;
    border-radius: 8px;
}

/* 滚动条 - 柔和样式 */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--color-bg-primary);
}

::-webkit-scrollbar-thumb {
    background: var(--color-border);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--color-text-secondary);
}

/* 选项卡 */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 1px solid var(--color-border);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 0.75rem 1.5rem;
    color: var(--color-text-secondary);
    border: none;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: var(--color-bg-hover);
    color: var(--color-text-primary);
}

.stTabs [aria-selected="true"] {
    background-color: var(--color-bg-card);
    color: var(--color-text-primary);
    border-bottom: 2px solid var(--color-text-primary);
}

/* 去除选项卡的focus状态颜色 */
.stTabs [data-baseweb="tab"]:focus {
    outline: none !important;
    box-shadow: none !important;
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
</style>
"""
