#!/usr/bin/env python3
"""
RAG链路耗时分析脚本：测量查询各阶段耗时，定位性能瓶颈

使用方法：
    python tests/tools/analyze_rag_timing.py
    python tests/tools/analyze_rag_timing.py --query "你的测试问题"
    python tests/tools/analyze_rag_timing.py --detailed  # 详细模式
    python tests/tools/analyze_rag_timing.py --agentic   # 测试Agentic模式

输出示例：
    📊 RAG链路耗时诊断报告
    ══════════════════════════════════════════════════════════
    阶段                          耗时(s)    占比      状态
    ──────────────────────────────────────────────────────────
    1. 查询处理（意图理解+改写）     1.23    15%       ✅
    2. 检索策略选择                  0.05     1%       ✅
    3. 向量检索                      0.45     5%       ✅
    4. 重排序                        0.89    11%       🟡
    5. LLM生成                       5.67    68%       ⚠️ 瓶颈
    ──────────────────────────────────────────────────────────
    总计                             8.29   100%
"""

import sys
import time
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class TimingResult:
    """计时结果"""
    name: str
    duration: float
    success: bool
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class RAGTimingAnalyzer:
    """RAG链路耗时分析器"""
    
    def __init__(self, detailed: bool = False):
        self.detailed = detailed
        self.results: List[TimingResult] = []
        self.total_start = time.perf_counter()
    
    @contextmanager
    def measure(self, name: str):
        """计时上下文管理器"""
        start = time.perf_counter()
        details = {}
        error = None
        success = True
        
        try:
            yield details
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            duration = time.perf_counter() - start
            self.results.append(TimingResult(
                name=name,
                duration=duration,
                success=success,
                error=error,
                details=details
            ))
    
    def add_result(self, name: str, duration: float, success: bool = True, 
                   error: Optional[str] = None, details: Optional[Dict] = None) -> None:
        """手动添加计时结果"""
        self.results.append(TimingResult(
            name=name,
            duration=duration,
            success=success,
            error=error,
            details=details or {}
        ))
    
    def print_report(self) -> None:
        """打印诊断报告"""
        total_time = sum(r.duration for r in self.results)
        
        print("\n" + "═" * 65)
        print("📊 RAG链路耗时诊断报告")
        print("═" * 65)
        print(f"{'阶段':<32} {'耗时(s)':<10} {'占比':<8} {'状态':<10}")
        print("─" * 65)
        
        for i, result in enumerate(self.results, 1):
            pct = (result.duration / total_time * 100) if total_time > 0 else 0
            status = self._get_status(result, pct)
            name_display = f"{i}. {result.name}"
            print(f"{name_display:<32} {result.duration:>6.2f}    {pct:>5.1f}%    {status}")
            
            if self.detailed and result.details:
                for key, value in result.details.items():
                    print(f"   └─ {key}: {value}")
            
            if result.error and self.detailed:
                print(f"   └─ 错误: {result.error[:60]}...")
        
        print("─" * 65)
        print(f"{'总计':<32} {total_time:>6.2f}    100.0%")
        print("═" * 65)
        
        # 打印建议
        self._print_suggestions(total_time)
    
    def _get_status(self, result: TimingResult, pct: float) -> str:
        """获取状态标记"""
        if not result.success:
            return "❌ 失败"
        if pct > 50:
            return "⚠️ 主要瓶颈"
        if pct > 30:
            return "🟠 瓶颈"
        if pct > 15:
            return "🟡 关注"
        return "✅"
    
    def _print_suggestions(self, total_time: float) -> None:
        """打印优化建议"""
        print("\n💡 优化建议:")
        
        # 按耗时排序，找出瓶颈
        sorted_results = sorted(self.results, key=lambda r: r.duration, reverse=True)
        
        for i, result in enumerate(sorted_results[:3]):
            pct = (result.duration / total_time * 100) if total_time > 0 else 0
            if pct > 15:
                suggestion = self._get_suggestion(result.name, result.duration, pct)
                print(f"   {i+1}. {suggestion}")
        
        # 总体评估
        print()
        if total_time < 3:
            print("   ✅ 总耗时 < 3秒，性能良好")
        elif total_time < 8:
            print("   🟡 总耗时 3-8秒，有优化空间")
        elif total_time < 15:
            print("   🟠 总耗时 8-15秒，建议优化")
        else:
            print("   ⚠️ 总耗时 > 15秒，急需优化")
        
        # 失败的阶段
        failed = [r for r in self.results if not r.success]
        if failed:
            print(f"   ❌ 有 {len(failed)} 个阶段失败，需要排查")
    
    def _get_suggestion(self, stage_name: str, duration: float, pct: float) -> str:
        """根据阶段名称生成优化建议"""
        suggestions = {
            "查询处理": f"「{stage_name}」占 {pct:.1f}%（{duration:.2f}s）- 考虑：简化查询直接跳过LLM / 使用更快的模型 / 增加缓存命中率",
            "LLM生成": f"「{stage_name}」占 {pct:.1f}%（{duration:.2f}s）- 考虑：使用更快的模型 / 减少max_tokens / 优化prompt长度",
            "向量检索": f"「{stage_name}」占 {pct:.1f}%（{duration:.2f}s）- 考虑：减少top_k / 优化索引结构 / 使用更快的向量库",
            "重排序": f"「{stage_name}」占 {pct:.1f}%（{duration:.2f}s）- 考虑：禁用重排序 / 使用更轻量的模型 / 减少重排序数量",
            "Embedding": f"「{stage_name}」占 {pct:.1f}%（{duration:.2f}s）- 考虑：使用本地模型 / 批量处理 / 缓存Embedding",
            "Agent": f"「{stage_name}」占 {pct:.1f}%（{duration:.2f}s）- 考虑：减少迭代次数 / 简化工具 / 使用传统模式",
        }
        
        # 模糊匹配
        for key, suggestion in suggestions.items():
            if key in stage_name:
                return suggestion
        
        return f"「{stage_name}」占 {pct:.1f}%（{duration:.2f}s）- 建议优先优化"


def analyze_modular_engine(query: str, detailed: bool = False) -> RAGTimingAnalyzer:
    """分析 ModularQueryEngine（传统模式）耗时"""
    from dotenv import load_dotenv
    load_dotenv()
    
    analyzer = RAGTimingAnalyzer(detailed=detailed)
    
    print("🔍 开始分析 ModularQueryEngine 链路耗时...\n")
    print(f"📝 测试查询: {query}\n")
    
    # 1. 初始化阶段
    index_manager = None
    engine = None
    
    with analyzer.measure("索引加载") as details:
        from backend.infrastructure.indexer import IndexManager
        index_manager = IndexManager()
        details["index_type"] = type(index_manager).__name__
    
    with analyzer.measure("引擎初始化") as details:
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        engine = ModularQueryEngine(index_manager=index_manager)
        details["strategy"] = engine.retrieval_strategy
        details["rerank"] = engine.enable_rerank
    
    # 2. 查询处理阶段（手动分解）
    query_processor = engine.query_processor
    
    with analyzer.measure("查询处理（意图理解+改写）") as details:
        processed = query_processor.process(query)
        details["method"] = processed.get("processing_method")
        details["final_query"] = processed["final_query"][:50] + "..." if len(processed["final_query"]) > 50 else processed["final_query"]
    
    final_query = processed["final_query"]
    understanding = processed.get("understanding")
    
    # 3. 检索阶段（手动分解）
    with analyzer.measure("检索策略选择/路由") as details:
        query_engine, strategy_info = engine._get_or_create_query_engine(
            final_query, 
            understanding
        )
        details["strategy_info"] = strategy_info[:60] if len(strategy_info) > 60 else strategy_info
    
    # 4. 检索执行（包含向量检索+重排序）
    # 这里需要更细粒度的分解，但 LlamaIndex 的 query_engine.query() 是原子操作
    # 我们记录总时间，然后估算各部分
    with analyzer.measure("检索+重排序+LLM生成（总计）") as details:
        start_time = time.perf_counter()
        answer, sources, reasoning_content, trace_info = engine.query(query, collect_trace=True)
        details["sources_count"] = len(sources)
        details["answer_len"] = len(answer)
        if trace_info:
            details["retrieval_time"] = trace_info.get("retrieval_time", "N/A")
    
    return analyzer


def analyze_modular_engine_detailed(query: str, detailed: bool = False) -> RAGTimingAnalyzer:
    """分析 ModularQueryEngine（传统模式）耗时 - 细粒度分解版"""
    from dotenv import load_dotenv
    load_dotenv()
    
    analyzer = RAGTimingAnalyzer(detailed=detailed)
    
    print("🔍 开始分析 ModularQueryEngine 链路耗时（细粒度）...\n")
    print(f"📝 测试查询: {query}\n")
    
    # 1. 初始化阶段
    with analyzer.measure("索引加载") as details:
        from backend.infrastructure.indexer import IndexManager
        index_manager = IndexManager()
        details["index_type"] = type(index_manager).__name__
    
    with analyzer.measure("引擎初始化") as details:
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        from backend.business.rag_engine.formatting import ResponseFormatter
        from backend.infrastructure.llms import create_deepseek_llm_for_query
        from backend.infrastructure.config import config
        
        # 手动初始化组件以分解耗时
        engine = ModularQueryEngine(index_manager=index_manager)
        details["strategy"] = engine.retrieval_strategy
        details["rerank"] = engine.enable_rerank
    
    # 2. 查询处理阶段
    query_processor = engine.query_processor
    
    with analyzer.measure("查询处理（意图理解+改写）") as details:
        processed = query_processor.process(query)
        details["method"] = processed.get("processing_method")
        details["complexity"] = processed.get("complexity", "N/A")
    
    final_query = processed["final_query"]
    understanding = processed.get("understanding")
    
    # 3. 检索策略选择
    with analyzer.measure("检索策略选择/路由") as details:
        query_engine_instance, strategy_info = engine._get_or_create_query_engine(
            final_query, 
            understanding
        )
        details["strategy"] = strategy_info[:40]
    
    # 4. 向量检索（手动执行检索器）
    retriever = engine.retriever
    nodes_with_scores = []
    
    with analyzer.measure("向量检索") as details:
        if retriever:
            nodes_with_scores = retriever.retrieve(final_query)
            details["retrieved_count"] = len(nodes_with_scores)
    
    # 5. 后处理（重排序等）
    with analyzer.measure("后处理（重排序等）") as details:
        if engine.postprocessors and nodes_with_scores:
            for postprocessor in engine.postprocessors:
                nodes_with_scores = postprocessor.postprocess_nodes(
                    nodes_with_scores,
                    query_str=final_query
                )
            details["final_count"] = len(nodes_with_scores)
    
    # 6. LLM生成
    with analyzer.measure("LLM生成") as details:
        from llama_index.core import get_response_synthesizer
        
        # 构建上下文
        context_parts = []
        for i, node_with_score in enumerate(nodes_with_scores, 1):
            node = node_with_score.node if hasattr(node_with_score, 'node') else node_with_score
            text = node.text if hasattr(node, 'text') else str(node)
            context_parts.append(f"[{i}] {text}")
        context_str = "\n\n".join(context_parts) if context_parts else "（无相关信息）"
        
        # 构建 prompt
        from backend.business.rag_engine.formatting.templates import get_template
        prompt = get_template('chat').format(context_str=context_str)
        prompt += f"\n\n用户问题：{final_query}\n\n请用中文回答问题。"
        
        # 调用 LLM
        response = engine.llm.complete(prompt)
        answer = str(response)
        details["answer_len"] = len(answer)
    
    # 7. 格式化
    with analyzer.measure("答案格式化") as details:
        formatted_answer = engine.formatter.format(answer, None)
        details["formatted_len"] = len(formatted_answer)
    
    return analyzer


def analyze_agentic_engine(query: str, detailed: bool = False) -> RAGTimingAnalyzer:
    """分析 AgenticQueryEngine（Agent模式）耗时"""
    from dotenv import load_dotenv
    load_dotenv()
    
    analyzer = RAGTimingAnalyzer(detailed=detailed)
    
    print("🔍 开始分析 AgenticQueryEngine 链路耗时...\n")
    print(f"📝 测试查询: {query}\n")
    
    # 1. 初始化阶段
    with analyzer.measure("索引加载") as details:
        from backend.infrastructure.indexer import IndexManager
        index_manager = IndexManager()
        details["index_type"] = type(index_manager).__name__
    
    with analyzer.measure("Agentic引擎初始化") as details:
        from backend.business.rag_engine.agentic.engine import AgenticQueryEngine
        engine = AgenticQueryEngine(
            index_manager=index_manager,
            max_iterations=5,
            timeout_seconds=60,
        )
        details["max_iterations"] = engine.max_iterations
    
    # 2. 执行查询（Agent模式是原子操作，难以细分）
    with analyzer.measure("Agent执行（总计）") as details:
        answer, sources, reasoning_content, trace_info = engine.query(query, collect_trace=True)
        details["sources_count"] = len(sources)
        details["answer_len"] = len(answer)
        details["has_reasoning"] = reasoning_content is not None
        if trace_info:
            details["agent_call_time"] = trace_info.get("agent_call_time", "N/A")
            details["extraction_time"] = trace_info.get("extraction_time", "N/A")
    
    return analyzer


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="RAG链路耗时诊断脚本")
    parser.add_argument("--query", "-q", type=str, 
                        default="什么是系统科学？",
                        help="测试查询（默认：什么是系统科学？）")
    parser.add_argument("--detailed", "-d", action="store_true", 
                        help="显示详细信息")
    parser.add_argument("--agentic", "-a", action="store_true", 
                        help="测试Agentic模式")
    parser.add_argument("--granular", "-g", action="store_true", 
                        help="细粒度分解（仅传统模式）")
    args = parser.parse_args()
    
    try:
        if args.agentic:
            # 测试 Agentic 模式
            print("=" * 65)
            print("🤖 测试 AgenticQueryEngine")
            print("=" * 65)
            analyzer = analyze_agentic_engine(args.query, detailed=args.detailed)
            analyzer.print_report()
        else:
            # 测试传统模式
            print("=" * 65)
            print("🔧 测试 ModularQueryEngine")
            print("=" * 65)
            
            if args.granular:
                analyzer = analyze_modular_engine_detailed(args.query, detailed=args.detailed)
            else:
                analyzer = analyze_modular_engine(args.query, detailed=args.detailed)
            
            analyzer.print_report()
            
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
