"""
设置页面开发者工具模块
调试工具、追踪信息
"""

import streamlit as st
from datetime import datetime


def render_dev_tools_tab():
    """渲染开发者工具标签页"""
    st.header("🐛 开发者工具")
    st.caption("RAG流程可观测性和调试工具（默认全部启用）")
    
    # 初始化日志存储
    if 'llama_debug_logs' not in st.session_state:
        st.session_state.llama_debug_logs = []
    if 'ragas_logs' not in st.session_state:
        st.session_state.ragas_logs = []
    
    # 创建标签页
    tab1, tab2 = st.tabs([
        "🐛 LlamaDebug 调试日志",
        "📊 RAGAS 评估日志"
    ])
    
    with tab1:
        _render_llama_debug_section()
    
    with tab2:
        _render_ragas_section()


def _render_llama_debug_section():
    """渲染 LlamaDebug 调试部分"""
    st.markdown("""
    **LlamaDebugHandler** 是LlamaIndex内置的调试工具：
    - 📝 输出详细的执行日志
    - 🔎 显示LLM调用和检索过程
    - ⚡ 轻量级，无需额外服务
    - ✅ **默认启用**，日志自动输出到控制台和页面
    """)
    
    # 清空日志按钮
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🗑️ 清空日志", use_container_width=True):
            st.session_state.llama_debug_logs = []
            st.rerun()
    
    # 显示日志
    logs = st.session_state.llama_debug_logs
    if not logs:
        st.info("📭 暂无调试日志，执行查询后将显示调试信息")
        return
    
    st.subheader(f"📋 调试日志（最近 {len(logs)} 条）")
    
    # 倒序显示（最新的在前）
    for idx, log_entry in enumerate(reversed(logs[-20:])):  # 只显示最近20条
        with st.expander(f"🔍 查询 #{len(logs) - idx}: {log_entry.get('query', 'N/A')[:50]}...", expanded=(idx == 0)):
            st.markdown(f"**查询内容：** `{log_entry.get('query', 'N/A')}`")
            st.markdown(f"**答案预览：** {log_entry.get('answer', 'N/A')[:200]}...")
            st.markdown(f"**引用来源数：** {log_entry.get('sources_count', 0)}")
            st.markdown(f"**事件数：** {log_entry.get('events_count', 0)}")
            
            if log_entry.get('event_pairs'):
                st.markdown("**事件对：**")
                for i, pair in enumerate(log_entry['event_pairs'][:5]):  # 只显示前5个事件对
                    with st.container():
                        st.text(f"事件 {i+1}:")
                        if pair.get('start_event'):
                            st.code(pair['start_event'], language=None)
                        if pair.get('end_event'):
                            st.code(pair['end_event'], language=None)


def _render_ragas_section():
    """渲染 RAGAS 评估部分"""
    st.markdown("""
    **RAGAS** 是RAG系统评估框架：
    - 📊 多维度质量评估（忠实度、精确度、召回率等）
    - 🔍 自动收集查询数据
    - 📈 批量评估和结果分析
    - ✅ **默认启用**，评估数据自动输出到控制台和页面
    """)
    
    # 清空日志按钮
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🗑️ 清空日志", key="clear_ragas", use_container_width=True):
            st.session_state.ragas_logs = []
            st.rerun()
    
    # 显示日志
    logs = st.session_state.ragas_logs
    if not logs:
        st.info("📭 暂无评估日志，执行查询后将显示评估数据")
        return
    
    st.subheader(f"📋 评估日志（最近 {len(logs)} 条）")
    
    # 统计信息
    pending_count = sum(1 for log in logs if log.get('pending_evaluation', False))
    evaluated_count = len(logs) - pending_count
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总记录数", len(logs))
    with col2:
        st.metric("待评估", pending_count)
    with col3:
        st.metric("已评估", evaluated_count)
    
    # 倒序显示（最新的在前）
    for idx, log_entry in enumerate(reversed(logs[-20:])):  # 只显示最近20条
        is_pending = log_entry.get('pending_evaluation', False)
        status_icon = "⏳" if is_pending else "✅"
        
        with st.expander(f"{status_icon} 查询 #{len(logs) - idx}: {log_entry.get('query', 'N/A')[:50]}...", expanded=(idx == 0)):
            st.markdown(f"**查询内容：** `{log_entry.get('query', 'N/A')}`")
            st.markdown(f"**答案预览：** {log_entry.get('answer', 'N/A')[:200]}...")
            st.markdown(f"**上下文数量：** {log_entry.get('contexts_count', 0)}")
            st.markdown(f"**时间戳：** {log_entry.get('timestamp', 'N/A')}")
            
            if is_pending:
                st.info("⏳ 等待批量评估中...")
            elif log_entry.get('evaluation_result'):
                st.markdown("**评估结果：**")
                eval_result = log_entry['evaluation_result']
                if isinstance(eval_result, dict):
                    for metric, value in eval_result.items():
                        st.metric(metric, f"{value:.4f}" if isinstance(value, (int, float)) else str(value))
                else:
                    st.text(str(eval_result))



