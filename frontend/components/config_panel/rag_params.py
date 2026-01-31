"""
RAG 参数面板组件 - RAG 检索参数的 UI 控制

主要功能：
- render_rag_basic_params(): 基础参数（检索策略、Agentic 开关）
- render_rag_advanced_params(): 高级参数（top_k、threshold、rerank）
"""

import streamlit as st
from typing import Callable, Optional

from backend.infrastructure.config import config


# 检索策略选项
RETRIEVAL_STRATEGIES = {
    "vector": "向量检索",
    "bm25": "BM25 关键词检索",
    "hybrid": "混合检索",
    "multi": "多策略融合",
}


def render_rag_basic_params(
    on_strategy_change: Optional[Callable[[str], None]] = None,
    on_agentic_toggle: Optional[Callable[[bool], None]] = None,
) -> None:
    """渲染 RAG 基础参数面板
    
    Args:
        on_strategy_change: 检索策略变更回调
        on_agentic_toggle: Agentic RAG 切换回调
    """
    # 初始化状态
    if 'retrieval_strategy' not in st.session_state:
        st.session_state.retrieval_strategy = config.RETRIEVAL_STRATEGY
    if 'use_agentic_rag' not in st.session_state:
        st.session_state.use_agentic_rag = False
    
    # 检索策略选择
    strategy_names = list(RETRIEVAL_STRATEGIES.values())
    strategy_keys = list(RETRIEVAL_STRATEGIES.keys())
    
    current_strategy = st.session_state.retrieval_strategy
    current_index = strategy_keys.index(current_strategy) if current_strategy in strategy_keys else 0
    
    # Agentic RAG 启用时禁用策略选择
    is_agentic = st.session_state.use_agentic_rag
    
    selected_name = st.selectbox(
        "🔍 检索策略",
        options=strategy_names,
        index=current_index,
        key="retrieval_strategy_selector",
        disabled=is_agentic,
        help="选择文档检索方式。启用 Agentic RAG 时由 AI 自动选择。"
    )
    
    # 更新策略
    selected_key = strategy_keys[strategy_names.index(selected_name)]
    if selected_key != current_strategy and not is_agentic:
        st.session_state.retrieval_strategy = selected_key
        if on_strategy_change:
            on_strategy_change(selected_key)
    
    # Agentic RAG 开关
    st.markdown("---")
    
    agentic_enabled = st.toggle(
        "🤖 Agentic RAG",
        value=is_agentic,
        key="agentic_rag_toggle_sidebar",
        help="启用后，AI 将自主选择检索策略。适合复杂查询，但响应时间可能稍长。"
    )
    
    if agentic_enabled != is_agentic:
        st.session_state.use_agentic_rag = agentic_enabled
        if on_agentic_toggle:
            on_agentic_toggle(agentic_enabled)
    
    if agentic_enabled:
        st.caption("💡 AI 将根据查询内容自动选择最佳检索策略")


def render_rag_advanced_params(
    on_params_change: Optional[Callable[[], None]] = None,
) -> None:
    """渲染 RAG 高级参数面板（用于设置弹窗）
    
    Args:
        on_params_change: 参数变更回调
    """
    # 初始化状态
    if 'similarity_top_k' not in st.session_state:
        st.session_state.similarity_top_k = config.SIMILARITY_TOP_K
    if 'similarity_threshold' not in st.session_state:
        st.session_state.similarity_threshold = config.SIMILARITY_THRESHOLD
    if 'enable_rerank' not in st.session_state:
        st.session_state.enable_rerank = config.ENABLE_RERANK
    
    st.subheader("检索参数")
    
    # 检索数量
    col1, col2 = st.columns(2)
    
    with col1:
        new_top_k = st.slider(
            "检索数量 (Top-K)",
            min_value=1,
            max_value=10,
            value=st.session_state.similarity_top_k,
            key="similarity_top_k_slider",
            format="%d",
            help="每次检索返回的文档数量。数值越大召回越全，但可能引入噪声。"
        )
        
        if new_top_k != st.session_state.similarity_top_k:
            st.session_state.similarity_top_k = new_top_k
            if on_params_change:
                on_params_change()
    
    with col2:
        new_threshold = st.slider(
            "相似度阈值",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.similarity_threshold,
            step=0.05,
            key="similarity_threshold_slider",
            format="%.2f",
            help="低于此阈值的结果会被过滤。数值越低召回越多，但质量可能下降。"
        )
        
        if new_threshold != st.session_state.similarity_threshold:
            st.session_state.similarity_threshold = new_threshold
            if on_params_change:
                on_params_change()
    
    # 重排序开关
    st.markdown("---")
    
    new_rerank = st.toggle(
        "启用重排序 (Rerank)",
        value=st.session_state.enable_rerank,
        key="enable_rerank_toggle",
        help="对检索结果进行二次排序，提高相关性。会增加响应时间。"
    )
    
    if new_rerank != st.session_state.enable_rerank:
        st.session_state.enable_rerank = new_rerank
        if on_params_change:
            on_params_change()
    
    # 当前配置摘要
    st.markdown("---")
    st.caption(
        f"当前配置：Top-K={st.session_state.similarity_top_k}, "
        f"阈值={st.session_state.similarity_threshold:.2f}, "
        f"重排序={'开' if st.session_state.enable_rerank else '关'}"
    )
