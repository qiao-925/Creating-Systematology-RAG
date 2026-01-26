"""
可观测性摘要组件：智能提炼 RAG 链路关键信息

主要功能：
- render_l0_summary(): 渲染一句话摘要（始终可见）
- render_l1_key_nodes(): 渲染关键节点（有异常时展开）
- analyze_anomalies(): 分析异常情况
- compute_status(): 计算整体状态

设计原则：
- L0: 一行指标，用户一眼了解发生了什么
- L1: 关键节点，只在有异常/改写时显示
- L2: 完整链路，保留在 chat_display.py 中
"""

import streamlit as st
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class StatusLevel(Enum):
    """状态级别"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Anomaly:
    """异常信息"""
    level: StatusLevel
    icon: str
    message: str
    detail: Optional[str] = None


def compute_status(debug_log: Dict[str, Any]) -> Tuple[StatusLevel, str, str]:
    """计算整体状态
    
    Args:
        debug_log: LlamaDebug 日志数据
        
    Returns:
        (状态级别, 状态图标, 状态原因)
    """
    errors = debug_log.get('errors') or []
    warnings = debug_log.get('warnings') or []
    sources_count = debug_log.get('sources_count') or 0
    
    if errors:
        return StatusLevel.ERROR, "🔴", "执行错误"
    elif sources_count == 0:
        return StatusLevel.WARNING, "⚠️", "检索为空"
    elif warnings:
        return StatusLevel.WARNING, "⚠️", "有警告"
    else:
        return StatusLevel.SUCCESS, "✅", ""


def analyze_anomalies(debug_log: Dict[str, Any]) -> List[Anomaly]:
    """分析异常情况
    
    Args:
        debug_log: LlamaDebug 日志数据
        
    Returns:
        异常列表
    """
    anomalies = []
    
    # 检索结果为空
    sources_count = debug_log.get('sources_count') or 0
    if sources_count == 0:
        anomalies.append(Anomaly(
            level=StatusLevel.ERROR,
            icon="🔴",
            message="检索结果为空",
            detail="未检索到相关文档，答案可能不准确"
        ))
    
    # 答案长度异常
    answer_length = debug_log.get('answer_length') or 0
    if answer_length > 5000:
        anomalies.append(Anomaly(
            level=StatusLevel.WARNING,
            icon="⚠️",
            message="答案过长",
            detail=f"答案长度 {answer_length} 字符，可能包含冗余信息"
        ))
    elif 0 < answer_length < 50:
        anomalies.append(Anomaly(
            level=StatusLevel.WARNING,
            icon="⚠️",
            message="答案过短",
            detail=f"答案长度仅 {answer_length} 字符，可能信息不完整"
        ))
    
    # 性能瓶颈检测
    stage_times = debug_log.get('stage_times') or {}
    total_time = debug_log.get('total_time') or 0
    if total_time > 0 and stage_times:
        for stage, time_spent in stage_times.items():
            if time_spent and time_spent > total_time * 0.5:
                anomalies.append(Anomaly(
                    level=StatusLevel.WARNING,
                    icon="⏱️",
                    message=f"性能瓶颈: {stage}",
                    detail=f"该阶段耗时 {time_spent:.2f}s，占总耗时 {time_spent/total_time*100:.0f}%"
                ))
    
    # 错误信息
    errors = debug_log.get('errors', [])
    for error in errors:
        anomalies.append(Anomaly(
            level=StatusLevel.ERROR,
            icon="🔴",
            message="执行错误",
            detail=str(error)
        ))
    
    # 警告信息
    warnings = debug_log.get('warnings', [])
    for warning in warnings:
        anomalies.append(Anomaly(
            level=StatusLevel.WARNING,
            icon="⚠️",
            message="执行警告",
            detail=str(warning)
        ))
    
    return anomalies


def _format_tokens(tokens: int) -> str:
    """格式化 Token 数量（1000+ 显示为 1.2k）"""
    if tokens >= 1000:
        return f"{tokens/1000:.1f}k"
    return str(tokens)


def render_l0_summary(debug_log: Dict[str, Any], ragas_log: Optional[Dict[str, Any]] = None) -> None:
    """渲染 L0 指标摘要（一行无边框轻量样式）
    
    格式：📊 检索 0.8s · 📄 5篇 · 🎯 相关度 0.85
    
    Args:
        debug_log: LlamaDebug 日志数据
        ragas_log: RAGAS 评估日志数据（可选）
    """
    if not debug_log:
        return
    
    # 提取关键指标
    sources_count = debug_log.get('sources_count') or 0
    llm_calls = debug_log.get('llm_calls') or 0
    total_time = debug_log.get('total_time') or 0
    total_tokens = debug_log.get('total_tokens') or 0
    
    # 计算状态
    status_level, status_icon, status_reason = compute_status(debug_log)
    
    # RAGAS 分数
    ragas_score = None
    ragas_pending = False
    if ragas_log:
        if ragas_log.get('pending_evaluation'):
            ragas_pending = True
        else:
            ragas_score = _compute_ragas_score(ragas_log)
    
    # 构建一行摘要文本
    parts = []
    parts.append(f"📄 {sources_count} 文档")
    parts.append(f"🤖 {llm_calls} 次调用")
    parts.append(f"📝 {_format_tokens(total_tokens)} tokens")
    if total_time:
        parts.append(f"⏱️ {total_time:.1f}s")
    
    if ragas_pending:
        parts.append("📈 评估中...")
    elif ragas_score is not None:
        parts.append(f"📈 质量 {ragas_score:.2f}")
    elif status_reason:
        parts.append(f"{status_icon} {status_reason}")
    
    # 渲染一行摘要（无边框）
    summary_text = " · ".join(parts)
    st.markdown(
        f'<p class="obs-summary">{summary_text}</p>',
        unsafe_allow_html=True
    )


def _render_card(
    title: str, 
    content: str, 
    status: StatusLevel, 
    detail: Optional[str] = None
) -> None:
    """渲染单个卡片组件
    
    Args:
        title: 卡片标题
        content: 主要内容
        status: 状态级别（决定颜色）
        detail: 详细信息（可选）
    """
    # 状态对应的颜色配置
    color_map = {
        StatusLevel.SUCCESS: {"border": "#22c55e", "bg": "#f0fdf4", "text": "#166534"},
        StatusLevel.WARNING: {"border": "#f59e0b", "bg": "#fffbeb", "text": "#92400e"},
        StatusLevel.ERROR: {"border": "#ef4444", "bg": "#fef2f2", "text": "#991b1b"},
    }
    colors = color_map.get(status, color_map[StatusLevel.SUCCESS])
    
    # 构建卡片 HTML
    detail_html = f'<div style="font-size:12px;color:#6b7280;margin-top:4px;">{detail}</div>' if detail else ''
    
    card_html = f'''<div style="border-left:4px solid {colors["border"]};background:{colors["bg"]};padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:8px;">
<div style="font-weight:600;color:{colors["text"]};font-size:13px;margin-bottom:4px;">{title}</div>
<div style="color:#374151;font-size:14px;">{content}</div>{detail_html}</div>'''
    
    st.markdown(card_html, unsafe_allow_html=True)


def render_l1_key_nodes(debug_log: Dict[str, Any], ragas_log: Optional[Dict[str, Any]] = None) -> None:
    """渲染 L1 关键节点（卡片式设计）
    
    每个关键节点用独立卡片展示，左侧颜色条指示状态。
    
    Args:
        debug_log: LlamaDebug 日志数据
        ragas_log: RAGAS 评估日志数据（可选）
    """
    if not debug_log:
        return
    
    # 分析异常
    anomalies = analyze_anomalies(debug_log)
    ragas_anomalies = _analyze_ragas_anomalies(ragas_log) if ragas_log else []
    all_anomalies = anomalies + ragas_anomalies
    
    # 检查查询改写（只有真正改写了才显示）
    query_processing = debug_log.get('query_processing')
    has_rewrite = False
    rewritten_queries = []
    original_query = debug_log.get('query') or ''
    if query_processing:
        rewritten_queries = query_processing.get('rewritten_queries') or []
        # 只有当改写结果与原始查询不同时才认为"有改写"
        if rewritten_queries and len(rewritten_queries) > 0:
            first_rewritten = (rewritten_queries[0] or '').strip()
            original_stripped = original_query.strip()
            has_rewrite = first_rewritten != original_stripped
    
    # 无关键信息则返回
    if not all_anomalies and not has_rewrite:
        return
    
    # 构建标题摘要
    title_parts = []
    error_count = sum(1 for a in all_anomalies if a.level == StatusLevel.ERROR)
    warning_count = sum(1 for a in all_anomalies if a.level == StatusLevel.WARNING)
    if error_count > 0:
        title_parts.append(f"{error_count} 错误")
    if warning_count > 0:
        title_parts.append(f"{warning_count} 警告")
    if has_rewrite:
        title_parts.append("查询改写")
    
    title = f"🔍 关键节点（{', '.join(title_parts)}）" if title_parts else "🔍 关键节点"
    has_error = error_count > 0
    
    with st.expander(title, expanded=has_error):
        # 查询改写卡片（使用绿色，改写是正常优化）
        if has_rewrite:
            original = debug_log.get('query', '') or ''
            rewritten = rewritten_queries[0] if rewritten_queries else ''
            # 截断显示
            orig_display = f"{original[:80]}..." if len(original) > 80 else original
            rewr_display = f"{rewritten[:80]}..." if len(rewritten) > 80 else rewritten
            
            _render_card(
                title="📝 查询改写",
                content=f"<b>原始</b>: {orig_display}<br><b>改写</b>: {rewr_display}",
                status=StatusLevel.SUCCESS,
                detail="查询已被优化以提升检索效果"
            )
        
        # 异常卡片
        for anomaly in all_anomalies:
            _render_card(
                title=f"{anomaly.icon} {anomaly.message}",
                content=anomaly.detail or "",
                status=anomaly.level
            )


def _compute_ragas_score(ragas_log: Dict[str, Any]) -> Optional[float]:
    """计算 RAGAS 综合评分"""
    if not ragas_log:
        return None
    
    eval_result = ragas_log.get('evaluation_result')
    if not eval_result or not isinstance(eval_result, dict):
        return None
    
    scores = [v for v in eval_result.values() if isinstance(v, (int, float))]
    if not scores:
        return None
    
    return sum(scores) / len(scores)


def _analyze_ragas_anomalies(ragas_log: Dict[str, Any]) -> List[Anomaly]:
    """分析 RAGAS 评估结果中的异常"""
    anomalies = []
    
    if not ragas_log:
        return anomalies
    
    eval_result = ragas_log.get('evaluation_result')
    if not eval_result or not isinstance(eval_result, dict):
        return anomalies
    
    # 指标阈值和中文名称
    metric_info = {
        "faithfulness": ("忠实度", "答案可能与上下文不一致"),
        "context_precision": ("上下文精确度", "检索的上下文可能不够相关"),
        "context_recall": ("上下文召回率", "可能遗漏了相关信息"),
        "answer_relevancy": ("答案相关性", "答案可能未完全回答问题"),
    }
    
    threshold = 0.6  # 低于此阈值视为警告
    
    for metric, value in eval_result.items():
        if isinstance(value, (int, float)) and value < threshold:
            name, detail = metric_info.get(metric, (metric, "评分较低"))
            anomalies.append(Anomaly(
                level=StatusLevel.WARNING,
                icon="📉",
                message=f"{name}低 ({value:.2f})",
                detail=detail
            ))
    
    return anomalies


def render_observability_summary(
    debug_log: Dict[str, Any], 
    ragas_log: Optional[Dict[str, Any]] = None,
    show_l2: bool = True
) -> None:
    """渲染完整的可观测性摘要
    
    Args:
        debug_log: LlamaDebug 日志数据
        ragas_log: RAGAS 评估日志数据（可选）
        show_l2: 是否显示 L2 完整链路（默认 True，由 chat_display.py 控制）
    """
    if not debug_log:
        return
    
    # L0: 一句话摘要（始终显示）
    render_l0_summary(debug_log, ragas_log)
    
    # L1: 关键节点（有异常时显示）
    render_l1_key_nodes(debug_log, ragas_log)
