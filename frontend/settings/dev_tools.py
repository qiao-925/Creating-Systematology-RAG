"""
设置页面开发者工具模块
Phoenix可视化、调试工具、追踪信息
"""

import streamlit as st
from backend.infrastructure.phoenix_utils import (
    start_phoenix_ui, 
    stop_phoenix_ui, 
    is_phoenix_running, 
    get_phoenix_url
)


def render_dev_tools_tab():
    """渲染开发者工具标签页"""
    st.header("🐛 开发者工具")
    st.caption("RAG流程可观测性和调试工具")
    
    # Phoenix可视化平台
    _render_phoenix_section()
    
    st.divider()
    
    # LlamaDebugHandler调试
    _render_debug_section()
    
    st.divider()
    
    # 追踪信息收集
    _render_trace_section()


def _render_phoenix_section():
    """渲染Phoenix可视化平台部分"""
    st.subheader("📊 Phoenix可视化平台")
    st.markdown("""
    **Phoenix** 是开源的LLM可观测性平台，提供：
    - 📊 实时追踪RAG查询流程
    - 🔍 向量检索可视化
    - 📈 性能分析和统计
    - 🐛 调试和问题诊断
    """)
    
    if is_phoenix_running():
        st.success(f"✅ Phoenix已启动")
        st.markdown(f"**访问地址：** [{get_phoenix_url()}]({get_phoenix_url()})")
        
        if st.button("🛑 停止Phoenix", use_container_width=True):
            stop_phoenix_ui()
            st.session_state.phoenix_enabled = False
            st.success("Phoenix已停止")
            st.rerun()
    else:
        if st.button("🚀 启动Phoenix UI", type="primary", use_container_width=True):
            with st.spinner("正在启动Phoenix..."):
                session = start_phoenix_ui(port=6006)
                if session:
                    st.session_state.phoenix_enabled = True
                    st.success("✅ Phoenix已启动！")
                    st.rerun()
                else:
                    st.error("❌ Phoenix启动失败，请检查依赖是否安装")


def _render_debug_section():
    """渲染调试部分"""
    st.subheader("🐛 LlamaDebugHandler调试")
    st.markdown("""
    **LlamaDebugHandler** 是LlamaIndex内置的调试工具：
    - 📝 输出详细的执行日志
    - 🔎 显示LLM调用和检索过程
    - ⚡ 轻量级，无需额外服务
    """)
    
    debug_enabled = st.checkbox(
        "启用调试日志",
        value=st.session_state.debug_mode_enabled,
        help="在控制台输出详细的调试信息"
    )
    st.session_state.debug_mode_enabled = debug_enabled
    
    if debug_enabled:
        st.info("ℹ️ 调试日志将输出到控制台和日志文件")
        st.warning("⚠️ 配置更改后需要重新初始化对话管理器才能生效")
        
        if st.button("重新初始化对话管理器"):
            st.session_state.chat_manager = None
            st.success("✅ 对话管理器已重置，下次对话时将应用新配置")


def _render_trace_section():
    """渲染追踪信息部分"""
    st.subheader("📈 查询追踪信息")
    st.markdown("""
    收集每次查询的详细指标：
    - ⏱️ 检索时间和LLM生成时间
    - 📊 相似度分数统计
    - 📝 完整的chunk内容
    """)
    
    trace_enabled = st.checkbox(
        "启用追踪信息收集",
        value=st.session_state.collect_trace,
        help="在界面上显示详细的查询追踪信息"
    )
    st.session_state.collect_trace = trace_enabled
    
    if trace_enabled:
        st.info("ℹ️ 追踪信息将在每次查询后显示")

