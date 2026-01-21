"""
对话显示组件
"""

import streamlit as st
from typing import Optional
from frontend.utils.helpers import get_chat_title
from frontend.utils.sources import convert_sources_to_dict
from frontend.utils.state import initialize_sources_map
from frontend.utils.sources import format_answer_with_citation_links
from frontend.components.sources_panel import display_sources_below_message
from frontend.components.observability_summary import render_observability_summary
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger('app')


def render_chat_interface(rag_service, chat_manager) -> None:
    """渲染对话界面
    
    优化：统一处理会话加载和rerun，减少重复渲染。
    
    Args:
        rag_service: RAG服务实例
        chat_manager: 对话管理器实例
    """
    # 统一处理会话加载（优化：减少 rerun 次数）
    if st.session_state.get('session_loading_pending') or st.session_state.get('load_session_id'):
        from frontend.components.session_loader import load_history_session
        if load_history_session(chat_manager):
            st.rerun()
    
    # 注入全局JavaScript脚本（仅一次，必须在渲染任何消息前）
    if not st.session_state.get('citation_script_injected', False):
        from frontend.utils.sources import inject_citation_script
        st.markdown(inject_citation_script(), unsafe_allow_html=True)
        st.session_state.citation_script_injected = True
    
    # 显示标题
    chat_title = get_chat_title(st.session_state.messages)
    if chat_title:
        st.subheader(chat_title)
        st.markdown("---")
    
    # 初始化来源映射
    initialize_sources_map()
    
    # 无对话历史：显示快速开始
    if not st.session_state.messages:
        from frontend.components.quick_start import render_quick_start
        render_quick_start()
        return
    
    # 有对话历史：显示对话
    render_chat_history()


def render_chat_history() -> None:
    """渲染对话历史"""
    # 显示对话历史
    from frontend.utils.helpers import generate_message_id
    for idx, message in enumerate(st.session_state.messages):
        message_id = generate_message_id(idx, message)
        with st.chat_message(message["role"]):
            # 如果是AI回答，先显示观察器信息
            if message["role"] == "assistant":
                _render_observer_info(idx)
            
            # 如果是AI回答且包含引用，使用带链接的格式
            if message["role"] == "assistant" and "sources" in message and message["sources"]:
                formatted_content = format_answer_with_citation_links(
                    message["content"],
                    message["sources"],
                    message_id=message_id
                )
                st.markdown(formatted_content, unsafe_allow_html=True)
            else:
                st.markdown(message["content"])
            
            # 显示推理链（始终显示，如果存在）
            if message["role"] == "assistant":
                reasoning_content = message.get("reasoning_content")
                # 调试：检查推理链是否存在
                if reasoning_content:
                    with st.expander("🧠 推理过程", expanded=False):
                        st.markdown(f"```\n{reasoning_content}\n```")
                else:
                    # 调试：显示为什么没有推理链
                    if config.DEEPSEEK_ENABLE_REASONING_DISPLAY:
                        # 只在启用显示时才显示调试信息
                        logger.debug(f"消息 {message_id} 没有推理链内容")
        
        # 在消息下方显示引用来源（如果有）
        if message["role"] == "assistant":
            sources = st.session_state.current_sources_map.get(message_id, [])
            if sources:
                # 显示引用来源标题
                st.markdown("#### 📚 引用来源")
                # 显示引用来源详情
                display_sources_below_message(sources, message_id=message_id)
        
        # 更新session_state中的映射（确保同步）
        st.session_state.current_sources_map = st.session_state.current_sources_map
        st.session_state.current_reasoning_map = st.session_state.current_reasoning_map


def _render_observer_info(message_index: int) -> None:
    """渲染观察器信息（在答案前显示）
    
    Args:
        message_index: 消息索引（assistant消息的索引）
    """
    # 初始化日志存储
    if 'llama_debug_logs' not in st.session_state:
        st.session_state.llama_debug_logs = []
    if 'ragas_logs' not in st.session_state:
        st.session_state.ragas_logs = []
    
    # 获取观察器日志
    debug_logs = st.session_state.llama_debug_logs
    ragas_logs = st.session_state.ragas_logs
    
    # 计算assistant消息的数量（用于匹配日志）
    assistant_count = sum(1 for msg in st.session_state.messages[:message_index+1] if msg.get("role") == "assistant")
    
    # 找到对应的日志（通过assistant消息数量匹配）
    debug_log = None
    ragas_log = None
    
    # 如果日志数量足够，使用对应的日志
    if len(debug_logs) >= assistant_count:
        debug_log = debug_logs[assistant_count - 1]
    elif len(debug_logs) > 0:
        # 否则使用最新的日志
        debug_log = debug_logs[-1]
    
    if len(ragas_logs) >= assistant_count:
        ragas_log = ragas_logs[assistant_count - 1]
    elif len(ragas_logs) > 0:
        ragas_log = ragas_logs[-1]
    
    # 显示观察器信息（如果有）- 分层展示
    if debug_log or ragas_log:
        # L0 + L1: 智能摘要（始终显示，集成 RAGAS）
        if debug_log:
            render_observability_summary(debug_log, ragas_log=ragas_log, show_l2=False)
        
        # L2: 完整链路（折叠，供开发者调试）
        with st.expander("🔬 完整链路详情（开发者）", expanded=False):
            if debug_log:
                _render_llamadebug_full_info(debug_log)
            
            if ragas_log:
                st.divider()
                _render_ragas_full_info(ragas_log)


def _render_llamadebug_full_info(debug_log: dict) -> None:
    """按执行流程渲染 LlamaDebug 全量信息"""
    
    # ========== 阶段1: 查询开始 ==========
    st.markdown("##### 📝 1. 查询阶段")
    if debug_log.get('query'):
        st.markdown(f"**原始查询**: `{debug_log['query']}`")
    
    # 查询处理结果（新增）
    query_processing = debug_log.get('query_processing')
    if query_processing:
        col1, col2 = st.columns(2)
        with col1:
            if query_processing.get('rewritten_queries'):
                rewritten = query_processing['rewritten_queries']
                if len(rewritten) > 0:
                    st.markdown(f"**改写后的查询**: `{rewritten[0]}`")
                    if len(rewritten) > 1:
                        with st.expander(f"其他改写版本 ({len(rewritten)-1} 个)", expanded=False):
                            for i, q in enumerate(rewritten[1:], 2):
                                st.markdown(f"**版本 {i}**: `{q}`")
        
        with col2:
            if query_processing.get('processing_method'):
                method = query_processing['processing_method']
                method_label = "简单查询（跳过LLM）" if method == "simple" else "LLM处理"
                st.markdown(f"**处理方式**: {method_label}")
        
        # 意图理解结果（新增）
        understanding = query_processing.get('understanding')
        if understanding:
            with st.expander("🧠 查询意图理解", expanded=False):
                if isinstance(understanding, dict):
                    if understanding.get('query_type'):
                        st.markdown(f"**查询类型**: `{understanding['query_type']}`")
                    if understanding.get('complexity'):
                        complexity = understanding['complexity']
                        complexity_label = {
                            'simple': '简单',
                            'medium': '中等',
                            'complex': '复杂'
                        }.get(complexity, complexity)
                        st.markdown(f"**复杂度**: {complexity_label}")
                    if understanding.get('intent'):
                        st.markdown(f"**查询意图**: {understanding['intent']}")
                    if understanding.get('entities'):
                        entities = understanding['entities']
                        if entities:
                            st.markdown(f"**关键实体**: {', '.join(entities)}")
                    if understanding.get('confidence') is not None:
                        st.markdown(f"**置信度**: {understanding['confidence']:.2f}")
                else:
                    st.json(understanding)
    
    # 配置信息（新增）
    if debug_log.get('llm_model') or debug_log.get('retrieval_strategy') or debug_log.get('top_k'):
        with st.expander("⚙️ 配置信息", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                if debug_log.get('llm_model'):
                    st.markdown(f"**LLM模型**: `{debug_log['llm_model']}`")
                if debug_log.get('llm_params'):
                    params = debug_log['llm_params']
                    if params.get('temperature') is not None:
                        st.markdown(f"**Temperature**: {params['temperature']}")
                    if params.get('max_tokens') is not None:
                        st.markdown(f"**Max Tokens**: {params['max_tokens']}")
            with col2:
                if debug_log.get('retrieval_strategy'):
                    st.markdown(f"**检索策略**: `{debug_log['retrieval_strategy']}`")
            with col3:
                if debug_log.get('top_k'):
                    st.markdown(f"**Top K**: {debug_log['top_k']}")
    
    # 基础统计
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("事件总数", debug_log.get('events_count', 0))
    with col2:
        st.metric("LLM调用", debug_log.get('llm_calls', 0))
    with col3:
        st.metric("检索调用", debug_log.get('retrieval_calls', 0))
    with col4:
        total_time = debug_log.get('total_time', 0)
        if total_time:
            st.metric("总耗时", f"{total_time:.3f}s")
    
    # 事件类型统计
    if debug_log.get('event_type_counts'):
        st.markdown("**事件类型统计**:")
        event_counts = debug_log['event_type_counts']
        cols = st.columns(min(len(event_counts), 5))
        for idx, (event_type, count) in enumerate(list(event_counts.items())[:5]):
            with cols[idx % 5]:
                st.markdown(f"- `{event_type}`: {count}")
    
    st.divider()
    
    # ========== 阶段2: 检索阶段 ==========
    st.markdown("##### 🔍 2. 检索阶段")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**检索调用次数**: {debug_log.get('retrieval_calls', 0)}")
        if debug_log.get('stage_times'):
            retrieval_time = sum(
                time for event_type, time in debug_log['stage_times'].items()
                if 'retriev' in event_type.lower() or 'retrieve' in event_type.lower()
            )
            if retrieval_time > 0:
                st.markdown(f"**检索耗时**: {retrieval_time:.3f}s")
    
    with col2:
        st.markdown(f"**引用来源数**: {debug_log.get('sources_count', 0)}")
    
    # 检索查询
    if debug_log.get('retrieval_queries'):
        with st.expander(f"📋 检索查询 ({len(debug_log['retrieval_queries'])} 个)", expanded=False):
            for i, query in enumerate(debug_log['retrieval_queries'], 1):
                st.markdown(f"**检索查询 {i}**:")
                st.code(query, language=None)
    
    # 检索到的节点
    if debug_log.get('retrieved_nodes'):
        with st.expander(f"📄 检索到的节点 ({len(debug_log['retrieved_nodes'])} 个)", expanded=False):
            for i, node in enumerate(debug_log['retrieved_nodes'], 1):
                st.markdown(f"**节点 {i}**:")
                st.text(node[:500] + "..." if len(node) > 500 else node)
    
    # 引用来源详情
    if debug_log.get('sources'):
        with st.expander(f"📚 引用来源详情 ({len(debug_log['sources'])} 个)", expanded=False):
            for i, source in enumerate(debug_log['sources'], 1):
                st.markdown(f"**来源 {i}**:")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(source.get('text', '')[:300] + "..." if len(source.get('text', '')) > 300 else source.get('text', ''))
                with col2:
                    if source.get('score') is not None:
                        st.metric("相似度", f"{source['score']:.4f}")
                    if source.get('id'):
                        st.caption(f"ID: {source['id']}")
                    if source.get('metadata'):
                        with st.expander("元数据", expanded=False):
                            st.json(source['metadata'])
    
    st.divider()
    
    # ========== 阶段3: LLM调用阶段 ==========
    st.markdown("##### 🤖 3. LLM调用阶段")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("LLM调用次数", debug_log.get('llm_calls', 0))
    with col2:
        if debug_log.get('prompt_tokens', 0) > 0:
            st.metric("Prompt Tokens", debug_log['prompt_tokens'])
    with col3:
        if debug_log.get('completion_tokens', 0) > 0:
            st.metric("Completion Tokens", debug_log['completion_tokens'])
    with col4:
        if debug_log.get('total_tokens', 0) > 0:
            st.metric("Total Tokens", debug_log['total_tokens'])
    
    # LLM调用耗时
    if debug_log.get('stage_times'):
        llm_time = sum(
            time for event_type, time in debug_log['stage_times'].items()
            if 'llm' in event_type.lower()
        )
        if llm_time > 0:
            st.markdown(f"**LLM调用总耗时**: {llm_time:.3f}s")
    
    # LLM Prompts
    if debug_log.get('llm_prompts'):
        with st.expander(f"💬 LLM Prompts ({len(debug_log['llm_prompts'])} 个)", expanded=False):
            for i, prompt in enumerate(debug_log['llm_prompts'], 1):
                st.markdown(f"**Prompt {i}**:")
                st.code(prompt, language=None)
    
    # LLM Responses
    if debug_log.get('llm_responses'):
        with st.expander(f"📤 LLM Responses ({len(debug_log['llm_responses'])} 个)", expanded=False):
            for i, response in enumerate(debug_log['llm_responses'], 1):
                st.markdown(f"**Response {i}**:")
                st.code(response, language=None)
    
    st.divider()
    
    # ========== 阶段4: 生成阶段 ==========
    st.markdown("##### ✨ 4. 生成阶段")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**答案长度**: {debug_log.get('answer_length', 0)} 字符")
    with col2:
        if debug_log.get('stage_times'):
            gen_time = sum(
                time for event_type, time in debug_log['stage_times'].items()
                if 'synthesize' in event_type.lower() or 'generate' in event_type.lower()
            )
            if gen_time > 0:
                st.markdown(f"**生成耗时**: {gen_time:.3f}s")
    
    # 答案预览
    if debug_log.get('answer'):
        with st.expander("📄 答案预览", expanded=False):
            st.markdown(debug_log['answer'])
    
    st.divider()
    
    # ========== 阶段5: 性能指标 ==========
    st.markdown("##### ⏱️ 5. 性能指标")
    
    if debug_log.get('stage_times'):
        st.markdown("**各阶段耗时明细**:")
        stage_times = debug_log['stage_times']
        for event_type, duration in sorted(stage_times.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"- `{event_type}`: {duration:.3f}s")
    
    st.divider()
    
    # ========== 阶段6: 事件详情 ==========
    st.markdown("##### 🔍 6. 事件详情")
    
    if debug_log.get('event_pairs'):
        with st.expander(f"📋 事件对详情 ({len(debug_log['event_pairs'])} 个)", expanded=False):
            for i, pair in enumerate(debug_log['event_pairs'], 1):
                event_type = pair.get('event_type', 'Unknown')
                duration = pair.get('duration')
                
                with st.expander(f"事件对 {i}: {event_type}" + (f" ({duration:.3f}s)" if duration else ""), expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**开始事件**:")
                        if pair.get('start_event'):
                            st.code(pair['start_event'], language=None)
                        if pair.get('start_time'):
                            st.caption(f"时间: {pair['start_time']}")
                    
                    with col2:
                        st.markdown("**结束事件**:")
                        if pair.get('end_event'):
                            st.code(pair['end_event'], language=None)
                        if pair.get('end_time'):
                            st.caption(f"时间: {pair['end_time']}")
                    
                    # Payload详情
                    if pair.get('payload'):
                        with st.expander("Payload详情", expanded=False):
                            st.json(pair['payload'])
    
    # ========== 阶段7: 错误和警告 ==========
    errors = debug_log.get('errors', [])
    warnings = debug_log.get('warnings', [])
    
    if errors or warnings:
        st.markdown("##### ⚠️ 7. 错误和警告")
        
        if errors:
            st.error(f"❌ 错误 ({len(errors)} 个)")
            for i, error in enumerate(errors, 1):
                st.markdown(f"**错误 {i}**: {error}")
        
        if warnings:
            st.warning(f"⚠️ 警告 ({len(warnings)} 个)")
            for i, warning in enumerate(warnings, 1):
                st.markdown(f"**警告 {i}**: {warning}")


def _render_ragas_full_info(ragas_log: dict) -> None:
    """按执行流程渲染 RAGAS 全量信息"""
    
    is_pending = ragas_log.get('pending_evaluation', False)
    status_icon = "⏳" if is_pending else "✅"
    
    # ========== 阶段1: 数据收集阶段 ==========
    st.markdown("##### 📥 1. 数据收集阶段")
    
    st.markdown(f"**状态**: {status_icon} {'待评估' if is_pending else '已评估'}")
    
    # 数据统计
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("答案长度", f"{ragas_log.get('answer_length', 0)} 字符")
    with col2:
        st.metric("上下文数", ragas_log.get('contexts_count', 0))
    with col3:
        st.metric("来源数", ragas_log.get('sources_count', 0))
    with col4:
        if ragas_log.get('timestamp'):
            from datetime import datetime
            try:
                ts = datetime.fromisoformat(ragas_log['timestamp'].replace('Z', '+00:00'))
                st.caption(f"收集时间: {ts.strftime('%H:%M:%S')}")
            except:
                st.caption(f"时间: {ragas_log['timestamp']}")
    
    # 查询内容
    if ragas_log.get('query'):
        st.markdown("**📝 查询内容**:")
        st.code(ragas_log['query'], language=None)
    
    # 答案内容
    if ragas_log.get('answer'):
        with st.expander(f"📄 答案内容 ({ragas_log.get('answer_length', 0)} 字符)", expanded=False):
            st.markdown(ragas_log['answer'])
    
    # 上下文详情
    if ragas_log.get('contexts'):
        st.markdown(f"**📚 上下文数据 ({len(ragas_log['contexts'])} 个)**:")
        with st.expander(f"查看所有上下文", expanded=False):
            for i, ctx in enumerate(ragas_log['contexts'], 1):
                st.markdown(f"**上下文 {i}** ({len(ctx)} 字符):")
                st.text(ctx[:800] + "..." if len(ctx) > 800 else ctx)
                st.divider()
    
    # 来源详情
    if ragas_log.get('sources'):
        st.markdown(f"**🔗 来源详情 ({len(ragas_log['sources'])} 个)**:")
        with st.expander(f"查看所有来源", expanded=False):
            for i, source in enumerate(ragas_log['sources'], 1):
                st.markdown(f"**来源 {i}**:")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(source.get('text', '')[:400] + "..." if len(source.get('text', '')) > 400 else source.get('text', ''))
                with col2:
                    if source.get('score') is not None:
                        st.metric("相似度", f"{source['score']:.4f}")
                    if source.get('metadata'):
                        with st.expander("元数据", expanded=False):
                            st.json(source['metadata'])
                st.divider()
    elif ragas_log.get('sources_count', 0) > 0:
        st.markdown(f"**🔗 来源统计**: {ragas_log['sources_count']} 个来源")
    
    # Ground Truth（如果有）
    if ragas_log.get('ground_truth'):
        with st.expander("🎯 Ground Truth（真值）", expanded=False):
            st.markdown(ragas_log['ground_truth'])
    
    # Trace ID（如果有）
    if ragas_log.get('trace_id'):
        st.caption(f"Trace ID: {ragas_log['trace_id']}")
    
    st.divider()
    
    # ========== 阶段2: 批量评估状态 ==========
    st.markdown("##### 📊 2. 批量评估状态")
    
    # 计算待评估数据量
    if 'ragas_logs' in st.session_state:
        pending_count = sum(
            1 for log in st.session_state.ragas_logs 
            if log.get('pending_evaluation', True)
        )
        evaluated_count = len(st.session_state.ragas_logs) - pending_count
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总记录数", len(st.session_state.ragas_logs))
        with col2:
            st.metric("待评估", pending_count, delta=None)
        with col3:
            st.metric("已评估", evaluated_count, delta=None)
        
        # 批量评估进度
        batch_size = ragas_log.get('evaluation_batch_size', 10)  # 从评估结果获取，或使用默认值10
        if is_pending:
            progress = min(pending_count / batch_size, 1.0)
            st.progress(progress)
            st.info(f"⏳ 当前记录待评估，批量评估将在达到 {batch_size} 条数据时自动触发（当前: {pending_count}/{batch_size}）")
            
            # 显示评估队列信息
            if pending_count > 0:
                st.markdown(f"**评估队列**: 还有 {pending_count - 1} 条记录在队列中等待")
        else:
            st.success("✅ 此记录已完成评估")
            if ragas_log.get('evaluation_timestamp'):
                from datetime import datetime
                try:
                    eval_ts = datetime.fromisoformat(ragas_log['evaluation_timestamp'].replace('Z', '+00:00'))
                    st.caption(f"评估时间: {eval_ts.strftime('%Y-%m-%d %H:%M:%S')}")
                except:
                    st.caption(f"评估时间: {ragas_log['evaluation_timestamp']}")
    
    st.divider()
    
    # ========== 阶段3: 评估指标详情 ==========
    st.markdown("##### 📈 3. 评估指标详情")
    
    if not is_pending and ragas_log.get('evaluation_result'):
        eval_result = ragas_log['evaluation_result']
        
        if isinstance(eval_result, dict):
            # 显示所有评估指标
            st.markdown("**评估指标概览**:")
            
            # 按指标分组显示
            metrics_list = list(eval_result.items())
            num_cols = min(len(metrics_list), 5)
            cols = st.columns(num_cols)
            
            for idx, (metric, value) in enumerate(metrics_list):
                with cols[idx % num_cols]:
                    value_str = f"{value:.4f}" if isinstance(value, (int, float)) else str(value)
                    if isinstance(value, (int, float)):
                        # 根据值显示不同颜色和状态
                        if value >= 0.8:
                            color = "🟢"
                            status = "优秀"
                        elif value >= 0.6:
                            color = "🟡"
                            status = "良好"
                        else:
                            color = "🔴"
                            status = "需改进"
                        
                        st.metric(f"{color} {metric}", value_str, delta=status)
                    else:
                        st.markdown(f"**{metric}**: {value_str}")
            
            st.divider()
            
            # 详细指标说明
            st.markdown("**指标说明**:")
            metric_descriptions = {
                "faithfulness": "忠实度：答案是否基于提供的上下文",
                "context_precision": "上下文精确度：检索到的上下文是否相关",
                "context_recall": "上下文召回率：是否检索到所有相关信息",
                "answer_relevancy": "答案相关性：答案是否回答了查询",
                "context_relevancy": "上下文相关性：上下文是否与查询相关",
            }
            
            for metric, value in eval_result.items():
                description = metric_descriptions.get(metric, "评估指标")
                value_str = f"{value:.4f}" if isinstance(value, (int, float)) else str(value)
                
                with st.expander(f"📊 {metric}: {value_str}", expanded=False):
                    st.markdown(f"**说明**: {description}")
                    if isinstance(value, (int, float)):
                        # 显示进度条
                        st.progress(value)
                        if value >= 0.8:
                            st.success(f"✅ 优秀 ({value:.2%})")
                        elif value >= 0.6:
                            st.warning(f"⚠️ 良好 ({value:.2%})")
                        else:
                            st.error(f"❌ 需改进 ({value:.2%})")
        else:
            st.markdown("**评估结果**:")
            st.text(str(eval_result)[:1000])
    elif is_pending:
        st.info("⏳ 此记录尚未评估，等待批量评估触发")
    else:
        st.warning("⚠️ 暂无评估结果")
    
    st.divider()
    
    # ========== 阶段4: 评估数据质量 ==========
    st.markdown("##### 🔍 4. 评估数据质量")
    
    # 数据完整性检查
    quality_checks = []
    
    if ragas_log.get('query'):
        quality_checks.append(("✅", "查询数据", "已收集", f"{len(ragas_log['query'])} 字符"))
    else:
        quality_checks.append(("❌", "查询数据", "缺失", ""))
    
    if ragas_log.get('answer'):
        quality_checks.append(("✅", "答案数据", "已收集", f"{ragas_log.get('answer_length', 0)} 字符"))
    else:
        quality_checks.append(("❌", "答案数据", "缺失", ""))
    
    if ragas_log.get('contexts_count', 0) > 0:
        total_ctx_len = sum(len(ctx) for ctx in ragas_log.get('contexts', []))
        quality_checks.append(("✅", "上下文数据", f"已收集 ({ragas_log.get('contexts_count', 0)} 个)", f"总长度: {total_ctx_len} 字符"))
    else:
        quality_checks.append(("⚠️", "上下文数据", "为空", ""))
    
    if ragas_log.get('sources_count', 0) > 0:
        quality_checks.append(("✅", "来源数据", f"已收集 ({ragas_log.get('sources_count', 0)} 个)", ""))
    else:
        quality_checks.append(("⚠️", "来源数据", "为空", ""))
    
    if ragas_log.get('ground_truth'):
        quality_checks.append(("✅", "Ground Truth", "已提供", ""))
    else:
        quality_checks.append(("ℹ️", "Ground Truth", "未提供（可选）", ""))
    
    # 显示质量检查结果
    for icon, check_name, status, detail in quality_checks:
        if detail:
            st.markdown(f"{icon} **{check_name}**: {status} - {detail}")
        else:
            st.markdown(f"{icon} **{check_name}**: {status}")
    
    # 数据质量评分（只计算必需项）
    required_checks = [c for c in quality_checks if c[0] != "ℹ️"]  # 排除可选项
    quality_score = sum(1 for icon, _, _, _ in required_checks if icon == "✅") / len(required_checks) if required_checks else 0
    passed_checks = sum(1 for icon, _, _, _ in required_checks if icon == "✅")
    st.markdown(f"**数据完整性**: {quality_score:.0%} ({passed_checks}/{len(required_checks)} 必需项通过)")
    st.progress(quality_score)
    
    # 数据质量建议
    if quality_score < 1.0:
        st.warning("⚠️ 数据不完整，可能影响评估准确性")
    elif quality_score == 1.0 and ragas_log.get('ground_truth'):
        st.success("✅ 数据完整且包含 Ground Truth，评估结果最准确")
    elif quality_score == 1.0:
        st.info("ℹ️ 数据完整，但缺少 Ground Truth，部分指标可能无法计算")

