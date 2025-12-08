"""
自定义聊天输入组件 - DeepSeek风格
支持多行输入和圆形发送按钮
"""
import streamlit as st
from typing import Optional


def deepseek_style_chat_input(placeholder: str = "给系统发送消息", key: str = "chat_input") -> Optional[str]:
    """
    DeepSeek风格的聊天输入框
    
    Args:
        placeholder: 占位符文本
        key: Streamlit组件key
        
    Returns:
        用户输入的文本，如果未输入或未点击发送则返回None
    """
    # 初始化输入状态
    if f'{key}_input' not in st.session_state:
        st.session_state[f'{key}_input'] = ""
    
    # 使用 columns 实现居中布局（类似历史消息的居中方式）
    left_spacer, center_col, right_spacer = st.columns([1, 8, 1])
    
    with center_col:
        # 创建容器，使用相对定位将发送按钮嵌入输入框
        container = st.container()
        with container:
            # 多行文本输入（高度较小，更美观）
            user_input = st.text_area(
                "",
                value=st.session_state[f'{key}_input'],
                placeholder=placeholder,
                height=50,  # 进一步缩小高度
                key=f'{key}_textarea',
                label_visibility="collapsed"
            )
            
            # 发送按钮（使用绝对定位嵌入到输入框内部）
            col_btn, _ = st.columns([1, 20])
            with col_btn:
                send_button = st.button("↑", key=f'{key}_send', use_container_width=False, type="primary")
    
    # 更新输入状态
    st.session_state[f'{key}_input'] = user_input
    
    # 处理发送逻辑
    if send_button and user_input.strip():
        # 清空输入框
        st.session_state[f'{key}_input'] = ""
        return user_input.strip()
    
    return None

