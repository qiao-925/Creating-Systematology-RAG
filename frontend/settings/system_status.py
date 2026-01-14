"""
设置页面系统状态模块
索引管理、模型状态、系统信息
"""

import streamlit as st
from backend.infrastructure.config import config


def render_system_status_tab():
    """渲染系统状态标签页"""
    st.header("⚙️ 系统状态")
    st.caption("系统级配置和管理操作")
    
    # 索引管理
    _render_index_management()
    
    st.divider()
    
    # Embedding模型状态
    _render_model_status()
    
    st.divider()
    
    # 系统信息
    _render_system_info()


def _render_index_management():
    """渲染索引管理部分"""
    st.subheader("🗂️ 索引管理")
    
    if st.session_state.index_manager:
        stats = st.session_state.index_manager.get_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("文档数量", stats.get('document_count', 0))
        with col2:
            st.metric("分块大小", stats.get('chunk_size', 'N/A'))
        with col3:
            st.metric("分块重叠", stats.get('chunk_overlap', 'N/A'))
        
        st.divider()
        
        # 清空索引
        st.markdown("**危险操作**")
        st.warning("⚠️ 以下操作不可撤销")
        
        if st.button("🗑️ 清空索引", help="删除所有已索引的文档"):
            confirm = st.checkbox("确认清空索引")
            if confirm:
                st.session_state.index_manager.clear_index()
                st.session_state.index_built = False
                st.success("✅ 索引已清空")
                st.rerun()
    else:
        st.info("索引尚未初始化")


def _render_model_status():
    """渲染模型状态部分"""
    st.subheader("🔧 Embedding 模型状态")
    
    # 获取 Embedding 实例状态
    try:
        from backend.infrastructure.embeddings.factory import get_embedding_instance
        
        instance = get_embedding_instance()
        if instance:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("模型名称", instance.get_model_name())
            with col2:
                st.metric("已加载", "✅ 是")
            with col3:
                st.metric("向量维度", instance.get_embedding_dimension())
        else:
            st.warning("⚠️ 模型未加载")
    except Exception as e:
        st.error(f"❌ 获取模型状态失败: {e}")


def _render_system_info():
    """渲染系统信息部分"""
    st.subheader("ℹ️ 系统信息")
    
    sys_info = {
        "应用标题": config.APP_TITLE,
        "LLM模型": config.LLM_MODEL,
        "Embedding模型": config.EMBEDDING_MODEL,
        "向量数据库": "ChromaDB",
        "HuggingFace镜像": config.HF_ENDPOINT,
        "离线模式": "是" if config.HF_OFFLINE_MODE else "否",
    }
    
    for key, value in sys_info.items():
        col1, col2 = st.columns([1, 2])
        with col1:
            st.text(key)
        with col2:
            st.code(value)

