"""
观察器信息渲染组件

主要功能：
- 渲染 LlamaDebug 完整信息
- 渲染 RAGAS 完整信息
"""

import streamlit as st


def render_llamadebug_full_info(debug_log: dict) -> None:
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
    
    # 检索统计
    retrieval_info = debug_log.get('retrieval', {})
    if retrieval_info:
        col1, col2, col3 = st.columns(3)
        with col1:
            if retrieval_info.get('nodes_retrieved'):
                st.metric("检索节点数", retrieval_info['nodes_retrieved'])
        with col2:
            if retrieval_info.get('retrieval_time'):
                st.metric("检索耗时", f"{retrieval_info['retrieval_time']:.3f}s")
        with col3:
            if retrieval_info.get('similarity_cutoff'):
                st.metric("相似度阈值", f"{retrieval_info['similarity_cutoff']:.3f}")
        
        # 检索节点详情
        if retrieval_info.get('nodes'):
            with st.expander(f"查看检索节点 ({len(retrieval_info['nodes'])} 个)", expanded=False):
                for i, node in enumerate(retrieval_info['nodes'], 1):
                    st.markdown(f"**节点 {i}**:")
                    if isinstance(node, dict):
                        if node.get('text'):
                            st.text(node['text'][:500] + "..." if len(node['text']) > 500 else node['text'])
                        if node.get('score') is not None:
                            st.caption(f"相似度: {node['score']:.4f}")
                        if node.get('metadata'):
                            with st.expander("元数据", expanded=False):
                                st.json(node['metadata'])
                    else:
                        st.text(str(node)[:500])
                    st.divider()
    
    st.divider()
    
    # ========== 阶段3: LLM生成阶段 ==========
    st.markdown("##### 🤖 3. LLM生成阶段")
    
    llm_info = debug_log.get('llm_generation', {})
    if llm_info:
        col1, col2, col3 = st.columns(3)
        with col1:
            if llm_info.get('generation_time'):
                st.metric("生成耗时", f"{llm_info['generation_time']:.3f}s")
        with col2:
            if llm_info.get('tokens_generated'):
                st.metric("生成Token数", llm_info['tokens_generated'])
        with col3:
            if llm_info.get('tokens_per_second'):
                st.metric("生成速度", f"{llm_info['tokens_per_second']:.1f} tokens/s")
        
        # LLM调用详情
        if llm_info.get('calls'):
            with st.expander(f"查看LLM调用详情 ({len(llm_info['calls'])} 次)", expanded=False):
                for i, call in enumerate(llm_info['calls'], 1):
                    st.markdown(f"**调用 {i}**:")
                    if isinstance(call, dict):
                        if call.get('prompt'):
                            with st.expander("Prompt", expanded=False):
                                st.text(call['prompt'][:1000] + "..." if len(call['prompt']) > 1000 else call['prompt'])
                        if call.get('response'):
                            with st.expander("Response", expanded=False):
                                st.text(call['response'][:1000] + "..." if len(call['response']) > 1000 else call['response'])
                        if call.get('tokens'):
                            st.caption(f"Tokens: {call['tokens']}")
                    else:
                        st.text(str(call)[:500])
                    st.divider()
    
    st.divider()
    
    # ========== 阶段4: 后处理阶段 ==========
    st.markdown("##### 🔧 4. 后处理阶段")
    
    postprocess_info = debug_log.get('postprocessing', {})
    if postprocess_info:
        if postprocess_info.get('reranking_applied'):
            st.markdown("**重排序**: ✅ 已应用")
            if postprocess_info.get('reranked_count'):
                st.metric("重排序后节点数", postprocess_info['reranked_count'])
        else:
            st.markdown("**重排序**: ❌ 未应用")
    
    st.divider()
    
    # ========== 阶段5: 完整事件列表 ==========
    st.markdown("##### 📋 5. 完整事件列表")
    
    if debug_log.get('events'):
        with st.expander("查看所有事件", expanded=False):
            for i, event in enumerate(debug_log['events'], 1):
                st.markdown(f"**事件 {i}**:")
                if isinstance(event, dict):
                    st.json(event)
                else:
                    st.text(str(event))
                st.divider()


def render_ragas_full_info(ragas_log: dict) -> None:
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
        batch_size = ragas_log.get('evaluation_batch_size', 10)
        if is_pending:
            progress = min(pending_count / batch_size, 1.0)
            st.progress(progress)
            st.info(f"⏳ 当前记录待评估，批量评估将在达到 {batch_size} 条数据时自动触发（当前: {pending_count}/{batch_size}）")
            
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
            st.markdown("**评估指标概览**:")
            
            metrics_list = list(eval_result.items())
            num_cols = min(len(metrics_list), 5)
            cols = st.columns(num_cols)
            
            for idx, (metric, value) in enumerate(metrics_list):
                with cols[idx % num_cols]:
                    value_str = f"{value:.4f}" if isinstance(value, (int, float)) else str(value)
                    if isinstance(value, (int, float)):
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
    
    # 数据质量评分
    required_checks = [c for c in quality_checks if c[0] != "ℹ️"]
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
