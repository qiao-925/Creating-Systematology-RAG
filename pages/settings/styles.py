"""
设置页面CSS样式模块
Claude风格设计系统
"""

CLAUDE_STYLE_CSS = """
<style>
/* ============================================================
   Claude风格设计系统 - 极简优雅
   ============================================================ */

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
    padding-top: 2.5rem;
    padding-bottom: 3rem;
    max-width: 100%;
}

/* 正文字体大小和行高 */
p, div, span {
    font-size: 16px;
    line-height: 1.7;
}

/* 标题层级 */
h1 {
    font-size: 2rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
    color: var(--color-text-primary);
}

h2 {
    font-size: 1.5rem;
    font-weight: 600;
    margin-top: 2rem;
    margin-bottom: 1rem;
    color: var(--color-text-primary);
}

h3 {
    font-size: 1.25rem;
    font-weight: 500;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    color: var(--color-text-primary);
}

/* 按钮样式 */
.stButton > button {
    border-radius: 8px;
    border: 1px solid var(--color-border);
    background-color: var(--color-bg-card);
    color: var(--color-text-primary);
    font-weight: 500;
    transition: all 0.2s;
}

.stButton > button:hover {
    background-color: var(--color-bg-hover);
    border-color: var(--color-accent);
}

/* 输入框 */
.stTextInput > div > div > input {
    border-radius: 8px;
    border: 1px solid var(--color-border);
}

/* 标签页 */
.stTabs [data-baseweb="tab"] {
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
    color: var(--color-accent);
    border-bottom: 2px solid var(--color-accent);
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

/* Checkbox */
.stCheckbox {
    color: var(--color-text-primary);
}

/* Spinner加载动画 */
.stSpinner > div {
    border-top-color: var(--color-accent) !important;
}
</style>
"""

