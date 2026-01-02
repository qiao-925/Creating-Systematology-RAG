"""
聊天输入组件 - 现代简洁风格
支持多行输入、自动高度调整、键盘快捷键和字符计数

主要功能：
- deepseek_style_chat_input()：现代简洁风格的聊天输入框
"""

import streamlit as st
from typing import Optional, Tuple


def deepseek_style_chat_input(placeholder: str = "给系统发送消息", key: str = "chat_input", disabled: bool = False, fixed: bool = False) -> Optional[str]:
    """现代简洁风格的聊天输入框
    
    Args:
        placeholder: 占位符文本
        key: Streamlit组件key
        disabled: 是否禁用输入框（思考中时隐藏）
        fixed: 是否固定在底部（有对话历史时使用）
        
    Returns:
        用户输入的文本，如果未输入或未点击发送则返回None
    """
    # 如果禁用，不渲染输入框
    if disabled:
        return None
    
    # 初始化输入状态
    if f'{key}_input' not in st.session_state:
        st.session_state[f'{key}_input'] = ""
    
    if f'{key}_char_count' not in st.session_state:
        st.session_state[f'{key}_char_count'] = 0
    
    # 注入样式和 JavaScript
    _inject_chat_input_assets(key, placeholder, fixed)
    
    # 根据是否固定定位选择不同的布局
    from frontend.utils.helpers import create_centered_columns
    if fixed:
        # 固定定位时，使用全宽容器，通过CSS固定到底部
        st.markdown(f'<div class="fixed-input-container-{key}">', unsafe_allow_html=True)
        left_spacer, center_col, right_spacer = create_centered_columns()
        with center_col:
            user_input, send_button = _render_input_area(key, placeholder)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        left_spacer, center_col, right_spacer = create_centered_columns()
        with center_col:
            with st.container():
                user_input, send_button = _render_input_area(key, placeholder)
    
    # 更新输入状态
    st.session_state[f'{key}_input'] = user_input
    st.session_state[f'{key}_char_count'] = len(user_input)
    
    # 处理发送逻辑
    if send_button and user_input.strip():
        st.session_state[f'{key}_input'] = ""
        st.session_state[f'{key}_char_count'] = 0
        return user_input.strip()
    
    # 处理键盘快捷键
    if f'{key}_keyboard_send' in st.session_state and st.session_state[f'{key}_keyboard_send']:
        user_input_value = st.session_state[f'{key}_input']
        if user_input_value.strip():
            st.session_state[f'{key}_input'] = ""
            st.session_state[f'{key}_char_count'] = 0
            st.session_state[f'{key}_keyboard_send'] = False
            return user_input_value.strip()
        st.session_state[f'{key}_keyboard_send'] = False
    
    return None


def _render_input_area(key: str, placeholder: str) -> Tuple[str, bool]:
    """渲染输入区域
    
    Returns:
        (user_input, send_button_clicked) 元组
    """
    # 使用更协调的布局比例，按钮宽度适中
    col_input, col_button = st.columns([10, 1.2], gap="small")
    
    with col_input:
        # 使用容器包裹输入框，便于精确对齐
        input_container = st.container()
        with input_container:
            user_input = st.text_area(
                "输入消息",
                value=st.session_state.get(f'{key}_input', ""),
                placeholder=placeholder,
                height=60,
                key=f'{key}_textarea',
                label_visibility="collapsed"
            )
            # 字符计数
            char_count = len(user_input)
            max_chars = 2000
            count_color = "#6B6B6B" if char_count <= max_chars else "#EF4444"
            st.markdown(
                f'<div class="chat-char-count" style="color: {count_color}; font-size: 12px; text-align: right; padding-right: 8px; margin-top: -8px;">'
                f'{char_count}/{max_chars}</div>',
                unsafe_allow_html=True
            )
    
    with col_button:
        # 使用flexbox精确对齐，确保按钮与输入框顶部对齐
        st.markdown(
            '<div class="send-button-wrapper" style="display: flex; align-items: flex-start; height: 100%; padding-top: 0;">',
            unsafe_allow_html=True
        )
        send_button = st.button("发送", key=f'{key}_send_btn', use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)
    
    return user_input, send_button


def _inject_chat_input_assets(key: str, placeholder: str, fixed: bool = False) -> None:
    """注入样式和 JavaScript"""
    if f'{key}_keyboard_send' not in st.session_state:
        st.session_state[f'{key}_keyboard_send'] = False
    
    # 固定定位样式
    fixed_style = ""
    if fixed:
        fixed_style = f"""
.fixed-input-container-{key} {{
    position: fixed !important;
    bottom: 0 !important;
    left: 280px !important;
    right: 0 !important;
    z-index: 999 !important;
    background-color: #FFFFFF !important;
    padding: 1rem 0 !important;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.08) !important;
    border-top: 1px solid #E5E5E0 !important;
}}
.fixed-input-container-{key} [data-testid*="column"] {{
    max-width: 60% !important;
    margin: 0 auto !important;
}}
.fixed-input-container-{key} > div {{
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
}}
.main .block-container {{
    padding-bottom: 120px !important;
}}
@media (max-width: 768px) {{
    .fixed-input-container-{key} {{
        left: 0 !important;
    }}
    .fixed-input-container-{key} > div {{
        max-width: 90% !important;
    }}
}}"""
    
    # 输入框和按钮样式
    input_html = f"""<style>{fixed_style}
/* 输入框和按钮容器协调样式 */
div[data-testid*="column"]:has(textarea[data-testid*="{key}_textarea"]) {{
    display: flex !important;
    flex-direction: column !important;
}}
div[data-testid*="column"]:has(button[data-testid*="{key}_send_btn"]) {{
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
}}
.send-button-wrapper {{
    display: flex !important;
    align-items: flex-start !important;
    width: 100% !important;
    height: 100% !important;
}}
.send-button-wrapper button {{
    margin-top: 0 !important;
    align-self: flex-start !important;
}}

/* 输入框样式 - 现代简洁风格 */
div[data-testid*="{key}_textarea"] {{
    margin-bottom: 0 !important;
}}
textarea[data-testid*="{key}_textarea"] {{
    background-color: #FFFFFF !important;
    border: 1px solid #E5E5E0 !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    font-size: 16px !important;
    line-height: 1.6 !important;
    color: #2C2C2C !important;
    min-height: 60px !important;
    max-height: 200px !important;
    resize: none !important;
    overflow-y: auto !important;
    transition: all 0.2s ease !important;
    font-family: "Noto Serif SC", "Source Han Serif SC", "Georgia", "Times New Roman", serif !important;
    box-sizing: border-box !important;
}}
textarea[data-testid*="{key}_textarea"]:focus,
textarea[data-testid*="{key}_textarea"]:focus-visible,
textarea[data-testid*="{key}_textarea"]:focus-within,
textarea[data-testid*="{key}_textarea"]:active {{
    outline: none !important;
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
}}
textarea[data-testid*="{key}_textarea"]::placeholder {{
    color: #6B6B6B !important;
    opacity: 1 !important;
}}

/* 发送按钮样式 - 与输入框协调统一 */
button[data-testid*="{key}_send_btn"] {{
    height: 60px !important;
    min-height: 60px !important;
    max-height: 60px !important;
    border-radius: 12px !important;
    background-color: #2563EB !important;
    color: white !important;
    border: none !important;
    font-size: 16px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    font-family: "Noto Serif SC", "Source Han Serif SC", sans-serif !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    flex-shrink: 0 !important;
}}
button[data-testid*="{key}_send_btn"]:hover {{
    background-color: #1D4ED8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3) !important;
}}
button[data-testid*="{key}_send_btn"]:active {{
    transform: translateY(0) !important;
    box-shadow: none !important;
}}
button[data-testid*="{key}_send_btn"]:disabled {{
    background-color: #D1D5DB !important;
    cursor: not-allowed !important;
    transform: none !important;
    box-shadow: none !important;
}}

/* 字符计数样式 */
.chat-char-count {{
    font-family: "Noto Serif SC", "Source Han Serif SC", sans-serif;
    font-weight: 400;
}}
</style>
<script>
(function() {{
    function initChatInput() {{
        const textarea = document.querySelector('textarea[data-testid*="{key}_textarea"]');
        if (!textarea) {{
            setTimeout(initChatInput, 100);
            return;
        }}
        
        // 自动调整高度
        function autoResize() {{
            textarea.style.height = 'auto';
            const scrollHeight = textarea.scrollHeight;
            const minHeight = 60;
            const maxHeight = 200;
            const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
            textarea.style.height = newHeight + 'px';
        }}
        
        textarea.addEventListener('input', autoResize);
        autoResize();
        
        // 键盘快捷键：Enter发送，Shift+Enter换行
        textarea.addEventListener('keydown', function(e) {{
            if (e.key === 'Enter' && !e.shiftKey) {{
                e.preventDefault();
                const sendButton = document.querySelector('button[data-testid*="{key}_send_btn"]');
                if (sendButton && textarea.value.trim()) {{
                    sendButton.click();
                }}
            }}
        }});
    }}
    
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', initChatInput);
    }} else {{
        initChatInput();
    }}
    
    // 监听DOM变化，重新初始化
    const observer = new MutationObserver(function(mutations) {{
        initChatInput();
    }});
    observer.observe(document.body, {{childList: true, subtree: true}});
}})();
</script>"""
    
    st.markdown(input_html, unsafe_allow_html=True)
