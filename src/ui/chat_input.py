"""
Material Design 风格聊天输入组件
支持多行输入、自动高度调整、键盘快捷键和字符计数
"""
import streamlit as st
from typing import Optional
import streamlit.components.v1 as components


def deepseek_style_chat_input(placeholder: str = "给系统发送消息", key: str = "chat_input", disabled: bool = False, fixed: bool = False) -> Optional[str]:
    """
    Material Design 风格的聊天输入框
    
    Args:
        placeholder: 占位符文本（作为浮动标签）
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
    
    # 注入 Material Design 样式和 JavaScript
    container_id = f"material_input_{key}"
    _inject_material_design_assets(key, container_id, placeholder, fixed)
    
    # 根据是否固定定位选择不同的布局
    if fixed:
        # 固定定位时，使用全宽容器，通过CSS固定到底部
        # 添加一个标记类用于CSS选择
        st.markdown(f'<div class="fixed-input-container-{key}">', unsafe_allow_html=True)
        # 使用 columns 实现居中布局（缩小宽度）
        left_spacer, center_col, right_spacer = st.columns([2, 6, 2])
        
        with center_col:
            # 输入框和按钮的横向布局
            col_input, col_button = st.columns([10, 1])
            
            with col_input:
                # 输入框包装器
                input_wrapper = st.container()
                with input_wrapper:
                    # 多行文本输入
                    user_input = st.text_area(
                        "输入消息",
                        value=st.session_state[f'{key}_input'],
                        placeholder="",  # 占位符通过 CSS 实现
                        height=56,  # Material Design 标准高度
                        key=f'{key}_textarea',
                        label_visibility="collapsed"
                    )
                    
                    # 底部栏：字符计数
                    bottom_bar = st.container()
                    with bottom_bar:
                        # 字符计数显示（使用当前输入值）
                        char_count = len(user_input)
                        max_chars = 2000
                        count_color = "#6B6B6B" if char_count <= max_chars else "#EF4444"
                        st.markdown(
                            f'<div class="material-char-count" style="color: {count_color}; font-size: 12px; text-align: right; padding-right: 8px;">'
                            f'{char_count}/{max_chars}</div>',
                            unsafe_allow_html=True
                        )
            
            with col_button:
                # 发送按钮（Material Design FAB 风格）- 在右侧
                send_button = st.button(
                    "↑",
                    key=f'{key}_send',
                    use_container_width=True,
                    type="primary"
                )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # 非固定定位时，使用原来的居中布局
        left_spacer, center_col, right_spacer = st.columns([2, 6, 2])
        
        with center_col:
            # 创建输入框容器（输入框和按钮并排）
            with st.container():
                # 输入框和按钮的横向布局
                col_input, col_button = st.columns([10, 1])
                
                with col_input:
                    # 输入框包装器
                    input_wrapper = st.container()
                    with input_wrapper:
                        # 多行文本输入
                        user_input = st.text_area(
                            "输入消息",
                            value=st.session_state[f'{key}_input'],
                            placeholder="",  # 占位符通过 CSS 实现
                            height=56,  # Material Design 标准高度
                            key=f'{key}_textarea',
                            label_visibility="collapsed"
                        )
                        
                        # 底部栏：字符计数
                        bottom_bar = st.container()
                        with bottom_bar:
                            # 字符计数显示（使用当前输入值）
                            char_count = len(user_input)
                            max_chars = 2000
                            count_color = "#6B6B6B" if char_count <= max_chars else "#EF4444"
                            st.markdown(
                                f'<div class="material-char-count" style="color: {count_color}; font-size: 12px; text-align: right; padding-right: 8px;">'
                                f'{char_count}/{max_chars}</div>',
                                unsafe_allow_html=True
                            )
                
                with col_button:
                    # 发送按钮（Material Design FAB 风格）- 在右侧
                    send_button = st.button(
                        "↑",
                        key=f'{key}_send',
                        use_container_width=True,
                        type="primary"
                    )
    
    # 更新输入状态
    st.session_state[f'{key}_input'] = user_input
    st.session_state[f'{key}_char_count'] = len(user_input)
    
    # 处理发送逻辑
    if send_button and user_input.strip():
        # 清空输入框
        st.session_state[f'{key}_input'] = ""
        st.session_state[f'{key}_char_count'] = 0
        return user_input.strip()
    
    # 处理键盘快捷键（通过 JavaScript 触发）
    if f'{key}_keyboard_send' in st.session_state and st.session_state[f'{key}_keyboard_send']:
        user_input_value = st.session_state[f'{key}_input']
        if user_input_value.strip():
            st.session_state[f'{key}_input'] = ""
            st.session_state[f'{key}_char_count'] = 0
            st.session_state[f'{key}_keyboard_send'] = False
            return user_input_value.strip()
        st.session_state[f'{key}_keyboard_send'] = False
    
    return None


def _inject_material_design_assets(key: str, container_id: str, placeholder: str, fixed: bool = False) -> None:
    """注入 Material Design 样式和 JavaScript"""
    
    # 初始化键盘发送状态
    if f'{key}_keyboard_send' not in st.session_state:
        st.session_state[f'{key}_keyboard_send'] = False
    
    # Material Design 输入框的 HTML/CSS/JavaScript
    fixed_style = ""
    if fixed:
        fixed_style = f"""
    /* 固定定位在底部 - 使用标记类选择器 */
    .fixed-input-container-{key} {{
        position: fixed !important;
        bottom: 0 !important;
        left: 280px !important;  /* 侧边栏宽度 */
        right: 0 !important;
        z-index: 999 !important;
        background-color: #FFFFFF !important;
        padding: 1rem 0 !important;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1) !important;
        border-top: 1px solid #E5E5E0 !important;
    }}
    
    /* 固定输入框内部内容居中 - 限制最大宽度并居中 */
    .fixed-input-container-{key} [data-testid*="column"] {{
        max-width: 60% !important;
        margin: 0 auto !important;
    }}
    
    /* 确保固定输入框内的所有列都居中 */
    .fixed-input-container-{key} > div {{
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }}
    
    /* 为固定输入框留出底部空间 */
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
    }}
    """
    
    material_html = f"""
    <style>
    {fixed_style}
    
    /* Material Design 输入框容器 */
    div[data-testid*="{key}_textarea"] {{
        position: relative;
        margin-bottom: 0;
    }}
    
    /* Material Design 输入框样式 */
    textarea[data-testid*="{key}_textarea"] {{
        background-color: transparent !important;
        border: none !important;
        border-bottom: 2px solid #E5E5E0 !important;
        border-radius: 4px 4px 0 0 !important;
        padding: 16px 12px 8px 12px !important;
        padding-right: 60px !important;  /* 为右侧按钮留出空间 */
        font-size: 16px !important;
        line-height: 1.5 !important;
        color: #2C2C2C !important;
        min-height: 56px !important;
        max-height: 200px !important;
        resize: none !important;
        overflow-y: auto !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        box-shadow: 0 1px 0 0 rgba(0, 0, 0, 0.05) !important;
    }}
    
    /* 焦点状态 */
    textarea[data-testid*="{key}_textarea"]:focus {{
        outline: none !important;
        border-bottom-color: #2563EB !important;
        box-shadow: 0 2px 0 0 #2563EB !important;
    }}
    
    /* 浮动标签容器 */
    div[data-testid*="{key}_textarea"] {{
        position: relative;
    }}
    
    /* 浮动标签 */
    div[data-testid*="{key}_textarea"]::before {{
        content: "{placeholder}";
        position: absolute;
        left: 12px;
        top: 16px;
        font-size: 16px;
        color: #6B6B6B;
        pointer-events: none;
        transition: all 0.2s ease;
        z-index: 1;
        background-color: #FFFFFF;
        padding: 0 4px;
    }}
    
    /* 当有内容或焦点时，标签上浮 */
    textarea[data-testid*="{key}_textarea"].has-value ~ *::before,
    textarea[data-testid*="{key}_textarea"]:focus ~ *::before {{
        top: -8px;
        font-size: 12px;
        color: #2563EB;
    }}
    
    /* 发送按钮 Material Design FAB 风格 - 在输入框右侧 */
    button[data-testid*="{key}_send"] {{
        width: 48px !important;
        height: 48px !important;
        min-width: 48px !important;
        min-height: 48px !important;
        border-radius: 50% !important;
        background-color: #2563EB !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 20px !important;
        font-weight: 500 !important;
        padding: 0 !important;
        margin: 0 !important;
        margin-top: 4px !important;  /* 与输入框对齐 */
    }}
    
    button[data-testid*="{key}_send"]:hover {{
        background-color: #1D4ED8 !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
        transform: translateY(-2px) !important;
    }}
    
    button[data-testid*="{key}_send"]:active {{
        transform: translateY(0) !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
    }}
    
    button[data-testid*="{key}_send"]:disabled {{
        background-color: #D1D5DB !important;
        cursor: not-allowed !important;
        transform: none !important;
    }}
    
    /* 字符计数样式 */
    .material-char-count {{
        font-family: "Roboto", "Noto Sans SC", sans-serif;
        font-weight: 400;
    }}
    </style>
    
    <script>
    (function() {{
        // 等待 DOM 加载完成
        function initMaterialInput() {{
            const textarea = document.querySelector('textarea[data-testid*="{key}_textarea"]');
            if (!textarea) {{
                setTimeout(initMaterialInput, 100);
                return;
            }}
            
            // 自动调整高度
            function autoResize() {{
                textarea.style.height = 'auto';
                const scrollHeight = textarea.scrollHeight;
                const minHeight = 56;
                const maxHeight = 200;
                const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
                textarea.style.height = newHeight + 'px';
            }}
            
            // 监听输入事件
            textarea.addEventListener('input', autoResize);
            
            // 初始化高度
            autoResize();
            
            // 键盘快捷键处理
            textarea.addEventListener('keydown', function(e) {{
                // Enter 发送（如果没有 Shift）
                if (e.key === 'Enter' && !e.shiftKey) {{
                    e.preventDefault();
                    // 触发发送按钮点击
                    const sendButton = document.querySelector('button[data-testid*="{key}_send"]');
                    if (sendButton && textarea.value.trim()) {{
                        sendButton.click();
                    }}
                }}
                // Shift+Enter 换行（默认行为，不需要处理）
            }});
            
            // 浮动标签效果（通过 CSS 类控制）
            function updateFloatingLabel() {{
                const hasValue = textarea.value.trim().length > 0;
                const isFocused = document.activeElement === textarea;
                
                // 添加/移除类来控制标签位置
                if (hasValue || isFocused) {{
                    textarea.classList.add('has-value');
                    textarea.style.paddingTop = '24px';
                }} else {{
                    textarea.classList.remove('has-value');
                    textarea.style.paddingTop = '16px';
                }}
            }}
            
            textarea.addEventListener('input', updateFloatingLabel);
            textarea.addEventListener('focus', updateFloatingLabel);
            textarea.addEventListener('blur', updateFloatingLabel);
            updateFloatingLabel();
        }}
        
        // 启动初始化
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', initMaterialInput);
        }} else {{
            initMaterialInput();
        }}
        
        // Streamlit rerun 后重新初始化
        const observer = new MutationObserver(function(mutations) {{
            initMaterialInput();
        }});
        observer.observe(document.body, {{
            childList: true,
            subtree: true
        }});
    }})();
    </script>
    """
    
    st.markdown(material_html, unsafe_allow_html=True)
