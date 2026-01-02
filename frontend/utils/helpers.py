"""
辅助函数模块
"""

import streamlit as st
from typing import Optional, Dict, Any, List


def display_trace_info(trace_info: Dict[str, Any]) -> None:
    """显示查询追踪信息
    
    Args:
        trace_info: 追踪信息字典
    """
    if not trace_info:
        return
    
    with st.expander("📊 查询追踪信息", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("总耗时", f"{trace_info.get('total_time', 0)}s")
        
        with col2:
            retrieval_info = trace_info.get('retrieval', {})
            st.metric("检索耗时", f"{retrieval_info.get('time_cost', 0)}s")
        
        with col3:
            st.metric("召回数量", retrieval_info.get('chunks_retrieved', 0))
        
        st.divider()
        
        # 检索详情
        st.markdown("**🔍 检索详情**")
        col1, col2 = st.columns(2)
        with col1:
            st.text(f"Top K: {retrieval_info.get('top_k', 0)}")
            st.text(f"平均相似度: {retrieval_info.get('avg_score', 0)}")
        
        with col2:
            llm_info = trace_info.get('llm_generation', {})
            st.text(f"LLM模型: {llm_info.get('model', 'N/A')}")
            st.text(f"回答长度: {llm_info.get('response_length', 0)} 字符")


def get_chat_title(messages: List[Dict[str, Any]]) -> Optional[str]:
    """从第一个用户消息中提取标题
    
    Args:
        messages: 消息列表
        
    Returns:
        标题字符串，如果没有用户消息则返回None
    """
    if not messages:
        return None
    
    # 找到第一个用户消息
    for message in messages:
        if message.get("role") == "user":
            content = message.get("content", "")
            if content:
                # 截取前50个字符作为标题
                title = content[:50].strip()
                # 如果超过50个字符，添加省略号
                if len(content) > 50:
                    title += "..."
                return title
    
    return None

