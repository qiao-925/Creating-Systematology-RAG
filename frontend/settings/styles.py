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

/* 标签页基础样式 - 移除所有边框 */
.stTabs [data-baseweb="tab"] {
    color: var(--color-text-secondary);
    border: none !important;
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
    border-bottom: none !important;
    background-color: transparent;
}

/* 标签页内部所有元素也移除边框 */
.stTabs [data-baseweb="tab"] *,
.stTabs [data-baseweb="tab"]::before,
.stTabs [data-baseweb="tab"]::after {
    border: none !important;
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
    border-bottom: none !important;
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
    color: var(--color-accent);
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
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
    border-bottom: none !important;
}

/* 去除选项卡的所有focus状态颜色和边框 */
.stTabs [data-baseweb="tab"]:focus,
.stTabs [data-baseweb="tab"]:focus-visible,
.stTabs [data-baseweb="tab"]:focus-within,
.stTabs [data-baseweb="tab"]:active {
    outline: none !important;
    outline-color: transparent !important;
    box-shadow: none !important;
    border: none !important;
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
    border-bottom: none !important;
}

/* 确保选中状态的标签页只有蓝色下划线，没有其他边框 - 使用最高优先级 */
.stTabs [aria-selected="true"]:focus,
.stTabs [aria-selected="true"]:focus-visible,
.stTabs [aria-selected="true"]:focus-within,
.stTabs [aria-selected="true"]:active,
.stTabs [data-baseweb="tab"][aria-selected="true"]:focus,
.stTabs [data-baseweb="tab"][aria-selected="true"]:focus-visible,
.stTabs [data-baseweb="tab"][aria-selected="true"]:focus-within,
.stTabs [data-baseweb="tab"][aria-selected="true"]:active {
    outline: none !important;
    outline-color: transparent !important;
    box-shadow: none !important;
    border: none !important;
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
    border-bottom: 2px solid var(--color-accent) !important;
}

/* 确保标签页列表容器本身没有红色边框 */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 1px solid var(--color-border) !important;
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
}

/* 覆盖所有可能的红色边框和outline */
.stTabs *:focus,
.stTabs *:focus-visible,
.stTabs *:focus-within {
    outline: none !important;
    outline-color: transparent !important;
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

/* Checkbox */
.stCheckbox {
    color: var(--color-text-primary);
}

/* Spinner加载动画 */
.stSpinner > div {
    border-top-color: var(--color-accent) !important;
}

/* 去除所有focus状态的红色和蓝色边框 */
.stTextInput input:focus, 
.stTextArea textarea:focus,
.stTextInput input:focus-visible,
.stTextArea textarea:focus-visible,
.stTextInput input:focus-within,
.stTextArea textarea:focus-within,
.stTextInput input:active,
.stTextArea textarea:active {
    border-color: var(--color-border) !important;
    box-shadow: none !important;
    outline: none !important;
}

/* 去除所有invalid/valid状态的红色边框 */
.stTextInput input:invalid,
.stTextArea textarea:invalid,
.stTextInput input:valid,
.stTextArea textarea:valid {
    border-color: var(--color-border) !important;
    box-shadow: none !important;
    outline: none !important;
}

/* 全局去除所有可能的红色边框和outline */
*:focus,
*:focus-visible,
*:focus-within {
    outline-color: transparent !important;
}

/* 特别处理Streamlit可能添加的红色边框 */
[data-baseweb="tab"]:focus,
[data-baseweb="tab"]:focus-visible,
[data-baseweb="tab"]:focus-within,
[data-baseweb="select"]:focus,
[data-baseweb="select"]:focus-visible,
button:focus,
button:focus-visible,
input:focus,
input:focus-visible,
textarea:focus,
textarea:focus-visible {
    outline: none !important;
    outline-color: transparent !important;
    box-shadow: none !important;
    border-color: var(--color-border) !important;
}

/* 强制覆盖所有可能的红色边框颜色值 */
*:focus,
*:focus-visible,
*:focus-within,
*:active {
    border-color: var(--color-border) !important;
}

/* 特别覆盖红色边框值 */
*[style*="border-color: red"],
*[style*="border-color: #ff0000"],
*[style*="border-color: #f00"],
*[style*="border-color: rgb(255, 0, 0)"],
*[style*="border-color: rgba(255, 0, 0"] {
    border-color: var(--color-border) !important;
}

/* JavaScript: 动态移除设置对话框中的红色边框 */
</style>
<script>
(function() {
    function removeRedBordersInDialog() {
        // 只在对话框内查找
        const dialog = document.querySelector('[data-testid="stDialog"]');
        if (!dialog) return;
        
        // 获取对话框内的所有标签页
        const tabs = dialog.querySelectorAll('[data-baseweb="tab"]');
        tabs.forEach(function(tab) {
            // 移除所有可能的红色边框
            tab.style.outline = 'none';
            tab.style.outlineColor = 'transparent';
            tab.style.boxShadow = 'none';
            
            // 移除所有边框
            tab.style.border = 'none';
            tab.style.borderTop = 'none';
            tab.style.borderLeft = 'none';
            tab.style.borderRight = 'none';
            tab.style.borderBottom = 'none';
            
            // 移除内部所有子元素的边框
            const children = tab.querySelectorAll('*');
            children.forEach(function(child) {
                child.style.border = 'none';
                child.style.borderBottom = 'none';
            });
            
            // 如果是选中的标签页，只保留一条蓝色下划线
            if (tab.getAttribute('aria-selected') === 'true') {
                tab.style.borderBottom = '2px solid #2563EB';
                // 确保没有其他边框
                tab.style.borderTop = 'none';
                tab.style.borderLeft = 'none';
                tab.style.borderRight = 'none';
            }
        });
        
        // 检查标签页列表容器
        const tabList = dialog.querySelector('[data-baseweb="tab-list"]');
        if (tabList) {
            tabList.style.borderTop = 'none';
            tabList.style.borderLeft = 'none';
            tabList.style.borderRight = 'none';
            tabList.style.borderBottom = '1px solid var(--color-border, #E5E5E0)';
        }
    }
    
    // 页面加载后执行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            removeRedBordersInDialog();
            setInterval(removeRedBordersInDialog, 300);
        });
    } else {
        removeRedBordersInDialog();
        setInterval(removeRedBordersInDialog, 300);
    }
    
    // 监听DOM变化
    const observer = new MutationObserver(function(mutations) {
        removeRedBordersInDialog();
    });
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class', 'aria-selected']
    });
})();
</script>
"""

