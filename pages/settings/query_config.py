"""
设置页面查询配置模块
查询引擎参数配置
"""

import streamlit as st
from src.config import config


def render_query_config_tab():
    """渲染查询配置标签页"""
    st.header("🔧 查询配置")
    st.caption("调整查询引擎的行为参数")
    
    # 维基百科增强
    st.subheader("🌐 维基百科增强")
    st.markdown("启用维基百科可以在本地结果不足时自动补充背景知识")
    
    enable_wiki = st.checkbox(
        "启用维基百科查询", 
        value=st.session_state.enable_wikipedia,
        help="查询时如果本地结果相关度不足，会自动查询维基百科补充"
    )
    st.session_state.enable_wikipedia = enable_wiki
    
    if enable_wiki:
        threshold = st.slider(
            "触发阈值",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.wikipedia_threshold,
            step=0.1,
            help="本地结果相关度低于此值时触发维基百科查询"
        )
        st.session_state.wikipedia_threshold = threshold
        
        # 重置混合查询引擎
        if st.button("应用配置", type="primary"):
            st.session_state.hybrid_query_engine = None
            st.success("✅ 配置已应用，下次查询时生效")
    
    st.divider()
    
    # 未来扩展：检索参数调整
    st.subheader("🔍 检索参数（未来扩展）")
    st.info("ℹ️ 此部分功能将在未来版本中提供")
    
    # 预留位置
    st.text_input("相似度阈值", value=str(config.SIMILARITY_THRESHOLD), disabled=True)
    st.text_input("检索数量 (Top K)", value=str(config.SIMILARITY_TOP_K), disabled=True)

