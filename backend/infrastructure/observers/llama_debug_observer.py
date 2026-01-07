"""
LlamaDebug 观察器
提供 LlamaIndex 内置的调试日志功能
"""

from typing import Any, Dict, List, Optional
from llama_index.core.callbacks import LlamaDebugHandler

from backend.infrastructure.observers.base import BaseObserver, ObserverType
from backend.infrastructure.logger import get_logger

logger = get_logger('llama_debug_observer')

# 尝试导入 streamlit（可选）
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None


class LlamaDebugObserver(BaseObserver):
    """LlamaDebug 观察器
    
    提供 LlamaIndex 内置的调试日志功能
    """
    
    def __init__(
        self,
        name: str = "llama_debug",
        enabled: bool = True,
        print_trace_on_end: bool = True,
    ):
        """初始化 LlamaDebug 观察器
        
        Args:
            name: 观察器名称
            enabled: 是否启用
            print_trace_on_end: 是否在结束时打印追踪信息
        """
        super().__init__(name, enabled)
        self.print_trace_on_end = print_trace_on_end
        self.handler = None
        
        if self.enabled:
            self.setup()
    
    def get_observer_type(self) -> ObserverType:
        return ObserverType.DEBUG
    
    def setup(self) -> None:
        """设置 LlamaDebug"""
        logger.info("🐛 初始化 LlamaDebug 观察器")
        
        try:
            self.handler = LlamaDebugHandler(
                print_trace_on_end=self.print_trace_on_end
            )
            
            logger.info("✅ LlamaDebug 观察器初始化完成")
            
        except Exception as e:
            logger.error(f"❌ LlamaDebug 初始化失败: {e}")
            self.enabled = False
    
    def on_query_start(self, query: str, **kwargs) -> Optional[str]:
        """查询开始时回调"""
        # LlamaDebugHandler 自动处理
        return None
    
    def on_query_end(
        self,
        query: str,
        answer: str,
        sources: List[Dict],
        trace_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """查询结束时回调"""
        # LlamaDebugHandler 自动处理
        # 同时将调试信息存储到 session_state 供前端显示
        if self.handler:
            try:
                event_pairs = self.get_event_pairs()
                # 提取更详细的事件信息
                event_details = []
                llm_calls = 0
                retrieval_calls = 0
                total_tokens = 0
                prompt_tokens = 0
                completion_tokens = 0
                llm_prompts = []
                llm_responses = []
                retrieval_queries = []
                retrieved_nodes = []
                event_type_counts = {}
                stage_times = {}
                
                for pair in event_pairs[:20]:  # 保存前20个事件对
                    start_event = pair[0] if pair[0] else None
                    end_event = pair[1] if pair[1] else None
                    
                    event_type = None
                    event_type_str = None
                    if start_event and hasattr(start_event, 'event_type'):
                        event_type = start_event.event_type
                        event_type_str = str(event_type)
                        event_type_counts[event_type_str] = event_type_counts.get(event_type_str, 0) + 1
                    
                    # 统计事件类型
                    if event_type_str:
                        if 'llm' in event_type_str.lower():
                            llm_calls += 1
                        if 'retrieval' in event_type_str.lower() or 'retrieve' in event_type_str.lower():
                            retrieval_calls += 1
                    
                    # 提取事件Payload信息
                    event_info = {
                        "event_type": event_type_str,
                        "start_event": str(start_event)[:500] if start_event else None,
                        "end_event": str(end_event)[:500] if end_event else None,
                        "payload": {},
                    }
                    
                    # 提取Payload详情
                    if start_event and hasattr(start_event, 'payload'):
                        payload = start_event.payload
                        if isinstance(payload, dict):
                            event_info["payload"] = {}
                            
                            # 提取所有Payload键值对
                            for key, value in payload.items():
                                key_str = str(key)
                                
                                # LLM相关
                                if 'prompt' in key_str.lower() or 'formatted_prompt' in key_str.lower():
                                    prompt_text = str(value)[:1000] if value else None
                                    if prompt_text:
                                        llm_prompts.append(prompt_text)
                                        event_info["payload"][key_str] = prompt_text
                                
                                if 'response' in key_str.lower() or 'message' in key_str.lower():
                                    response_text = str(value)[:1000] if value else None
                                    if response_text:
                                        llm_responses.append(response_text)
                                        event_info["payload"][key_str] = response_text
                                
                                # Token信息
                                if 'token' in key_str.lower():
                                    if isinstance(value, (int, float)):
                                        total_tokens += value
                                        if 'prompt' in key_str.lower() or 'input' in key_str.lower():
                                            prompt_tokens += value
                                        elif 'completion' in key_str.lower() or 'output' in key_str.lower():
                                            completion_tokens += value
                                        event_info["payload"][key_str] = value
                                
                                # 检索相关
                                if 'query' in key_str.lower() and 'retrieval' in event_type_str.lower() if event_type_str else False:
                                    query_text = str(value)[:500] if value else None
                                    if query_text:
                                        retrieval_queries.append(query_text)
                                        event_info["payload"][key_str] = query_text
                                
                                # 节点信息
                                if 'node' in key_str.lower() or 'chunk' in key_str.lower():
                                    if isinstance(value, (list, dict)):
                                        retrieved_nodes.append(str(value)[:500])
                                        event_info["payload"][key_str] = str(value)[:500]
                                
                                # 其他重要信息
                                if key_str not in event_info["payload"]:
                                    # 保存其他重要字段（限制长度）
                                    if isinstance(value, (str, int, float, bool)):
                                        event_info["payload"][key_str] = str(value)[:200]
                    
                    # 提取时间信息
                    if start_event and hasattr(start_event, 'time'):
                        event_info["start_time"] = str(start_event.time)
                    if end_event and hasattr(end_event, 'time'):
                        event_info["end_time"] = str(end_event.time)
                        if start_event and hasattr(start_event, 'time'):
                            try:
                                duration = float(end_event.time) - float(start_event.time)
                                event_info["duration"] = duration
                                if event_type_str:
                                    stage_times[event_type_str] = stage_times.get(event_type_str, 0) + duration
                            except:
                                pass
                    
                    event_details.append(event_info)
                
                debug_info = {
                    # 基础信息
                    "query": query,
                    "answer": answer[:500] + "..." if len(answer) > 500 else answer,
                    "answer_length": len(answer),
                    "sources_count": len(sources),
                    "sources": [
                        {
                            "text": src.get('text', '')[:200] if isinstance(src, dict) else str(src)[:200],
                            "score": src.get('score', 0) if isinstance(src, dict) else None,
                            "metadata": src.get('metadata', {}) if isinstance(src, dict) else {},
                            "id": src.get('id', None) if isinstance(src, dict) else None,
                        }
                        for src in sources[:10]  # 保存前10个来源
                    ],
                    
                    # 事件统计
                    "events_count": len(event_pairs),
                    "llm_calls": llm_calls,
                    "retrieval_calls": retrieval_calls,
                    "event_types": list(set([
                        str(pair[0].event_type) if pair[0] and hasattr(pair[0], 'event_type') else 'unknown'
                        for pair in event_pairs[:20]
                    ])),
                    "event_type_counts": event_type_counts,
                    
                    # Token信息
                    "total_tokens": total_tokens,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    
                    # LLM详细信息
                    "llm_prompts": llm_prompts[:5],  # 保存前5个prompt
                    "llm_responses": llm_responses[:5],  # 保存前5个response
                    
                    # 检索详细信息
                    "retrieval_queries": retrieval_queries[:5],  # 保存前5个检索查询
                    "retrieved_nodes": retrieved_nodes[:5],  # 保存前5个节点
                    
                    # 性能指标
                    "stage_times": stage_times,
                    "total_time": sum(stage_times.values()) if stage_times else None,
                    
                    # 事件对详情
                    "event_pairs": event_details,
                }
                
                # 存储到 session_state（如果 streamlit 可用）
                if STREAMLIT_AVAILABLE and hasattr(st, 'session_state'):
                    if 'llama_debug_logs' not in st.session_state:
                        st.session_state.llama_debug_logs = []
                    st.session_state.llama_debug_logs.append(debug_info)
                    
                    # 只保留最近50条记录
                    if len(st.session_state.llama_debug_logs) > 50:
                        st.session_state.llama_debug_logs = st.session_state.llama_debug_logs[-50:]
                
                # 打印到控制台
                logger.info(f"🐛 LlamaDebug: 查询完成，{len(event_pairs)} 个事件")
                print(f"\n🐛 LlamaDebug 追踪信息:")
                print(f"   查询: {query[:100]}...")
                print(f"   事件数: {len(event_pairs)}")
                if event_pairs:
                    print(f"   第一个事件: {str(event_pairs[0][0])[:200]}...")
                
            except Exception as e:
                logger.warning(f"⚠️  保存 LlamaDebug 信息失败: {e}")
    
    def get_callback_handler(self):
        """获取 LlamaIndex 兼容的回调处理器"""
        return self.handler
    
    def get_event_pairs(self):
        """获取事件对"""
        if self.handler:
            return self.handler.get_event_pairs()
        return []
    
    def get_report(self) -> Dict[str, Any]:
        """获取调试报告"""
        report = {
            "observer": self.name,
            "type": self.get_observer_type().value,
            "enabled": self.enabled,
            "print_trace_on_end": self.print_trace_on_end,
        }
        
        if self.handler:
            event_pairs = self.get_event_pairs()
            report["events_count"] = len(event_pairs)
        
        return report
    
    def teardown(self) -> None:
        """清理资源"""
        logger.info("🧹 清理 LlamaDebug 资源")

