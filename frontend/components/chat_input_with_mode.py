"""
聊天输入组件（带模式切换）
参考 DeepSeek 设计：整合输入框和按钮在一个容器中

主要功能：
- render_chat_input_with_mode()：渲染整合的输入区域（输入框 + 按钮）
- 处理 Agentic RAG 状态切换逻辑
"""

import streamlit as st
from typing import Optional


def render_chat_input_with_mode(
    placeholder: str = "给系统发送消息",
    key: str = "chat_input",
    disabled: bool = False
) -> Optional[str]:
    """渲染整合的聊天输入区域（参考 DeepSeek 设计）
    
    布局：
    - 上方：输入框
    - 下方：选项按钮（Agentic RAG）和发送按钮
    
    Args:
        placeholder: 输入框占位符文本
        key: Streamlit组件key
        disabled: 是否禁用输入框（思考中时隐藏）
        
    Returns:
        用户输入的文本，如果未输入或未点击发送则返回None
        
    注意：
        - 输入框和按钮整合在一个容器中
        - 按钮在输入框下方，左对齐
        - 切换模式时会重新创建服务实例
    """
    # 初始化 Agentic RAG 状态
    if 'use_agentic_rag' not in st.session_state:
        st.session_state.use_agentic_rag = False
    
    # 初始化输入状态
    if f'{key}_input_value' not in st.session_state:
        st.session_state[f'{key}_input_value'] = ''
    
    # 检查是否发送（在渲染之前检查，避免重复处理）
    user_input = None
    if st.session_state.get(f'{key}_send_clicked', False):
        user_input = st.session_state.get(f'{key}_input_value', '').strip()
        if user_input:
            st.session_state[f'{key}_input_value'] = ''  # 清空输入
        st.session_state[f'{key}_send_clicked'] = False  # 重置标志
    
    # 使用容器整合输入区域（参考 DeepSeek 设计：大输入框容器）
    with st.container():
        # 添加一些间距，让输入区域更明显
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 上方：大输入框
        if not disabled:
            # 使用 text_area 作为输入框（支持多行，不固定在底部）
            # 参考 DeepSeek：大输入框，支持多行输入
            input_value = st.text_area(
                placeholder,
                value=st.session_state[f'{key}_input_value'],
                key=f'{key}_textarea',
                height=120,  # 增加高度，更像 DeepSeek 的大输入框
                disabled=disabled,
                label_visibility="collapsed",
                help="输入消息，按 Shift+Enter 换行，点击发送按钮发送"
            )
            
            # 更新 session_state
            st.session_state[f'{key}_input_value'] = input_value
            
            # 下方：按钮区域（选项按钮 + 发送按钮）
            _render_input_actions(key, input_value.strip())
        else:
            # 禁用状态：只显示按钮区域
            _render_input_actions(key, '')
    
    return user_input


def _render_input_actions(input_key: str, input_value: str) -> None:
    """渲染输入区域下方的操作按钮
    
    参考 DeepSeek 设计：
    - 左侧：选项按钮（Agentic RAG 等）
    - 右侧：发送按钮
    """
    # 使用列布局：左侧选项按钮 + 右侧发送按钮
    col_left, col_right = st.columns([3, 1])
    
    with col_left:
        # 渲染 Agentic RAG 切换按钮
        _render_agentic_rag_toggle()
    
    with col_right:
        # 发送按钮
        if st.button(
            "发送",
            key=f"{input_key}_send_button",
            type="primary",
            use_container_width=True,
            disabled=not input_value
        ):
            # 标记发送按钮已点击
            st.session_state[f'{input_key}_send_clicked'] = True
            st.rerun()


def _render_agentic_rag_toggle() -> None:
    """渲染 Agentic RAG 模式切换按钮
    
    参考 DeepSeek 设计：按钮大小适中，左对齐
    """
    current_state = st.session_state.use_agentic_rag
    
    # 根据状态设置按钮文本和类型
    if current_state:
        button_label = "🤖 Agentic RAG"
        button_type = "primary"
        button_help = "点击禁用 Agentic RAG 模式"
    else:
        button_label = "🤖 Agentic RAG"
        button_type = "secondary"
        button_help = "点击启用 Agentic RAG 模式：AI 将自主选择检索策略（vector/hybrid/multi）。适合复杂查询，但响应时间可能稍长。"
    
    # 渲染按钮（大小适中，不占满全宽）
    if st.button(
        button_label,
        key="agentic_rag_toggle",
        type=button_type,
        use_container_width=False,
        help=button_help
    ):
            # 切换状态
            new_state = not current_state
            st.session_state.use_agentic_rag = new_state
            
            # 只重新创建 RAGService 和 ChatManager，不需要重新初始化整个应用
            # 这样可以避免重新加载索引等耗时操作
            if 'init_result' in st.session_state:
                init_result = st.session_state.init_result
                
                # 获取 IndexManager（不需要重新创建）
                index_manager = init_result.instances.get('index_manager')
                if index_manager is None:
                    # 如果没有 IndexManager，则需要完整重新初始化
                    st.session_state.boot_ready = False
                    del st.session_state.init_result
                    st.rerun()
                    return
                
                # 重新创建 RAGService（使用新的 use_agentic_rag 配置）
                from backend.business.rag_api import RAGService
                from backend.infrastructure.config import config
                
                collection_name = st.session_state.get('collection_name', config.CHROMA_COLLECTION_NAME)
                enable_debug = st.session_state.get('debug_mode_enabled', False)
                
                new_rag_service = RAGService(
                    collection_name=collection_name,
                    enable_debug=enable_debug,
                    enable_markdown_formatting=True,
                    use_agentic_rag=new_state,
                )
                init_result.instances['rag_service'] = new_rag_service
                
                # 重新创建 ChatManager（使用新的 use_agentic_rag 配置）
                from backend.business.chat import ChatManager
                
                new_chat_manager = ChatManager(
                    index_manager=index_manager,
                    user_email=None,
                    enable_debug=enable_debug,
                    enable_markdown_formatting=True,
                    use_agentic_rag=new_state,
                )
                init_result.instances['chat_manager'] = new_chat_manager
            
            # 触发 rerun，应用新的服务实例
            st.rerun()


