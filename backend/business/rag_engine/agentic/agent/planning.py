"""
规划 Agent 模块：创建 ReActAgent 用于自主选择检索策略

主要功能：
- create_planning_agent()：创建规划 Agent
- 集成检索工具
- 设置 System Prompt（从模板加载）
- 配置 max_iterations=5, verbose=True
"""

from typing import List, Optional
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import QueryEngineTool

from backend.infrastructure.indexer import IndexManager
from backend.infrastructure.logger import get_logger
from backend.business.rag_engine.agentic.agent.tools.retrieval_tools import create_retrieval_tools
from backend.business.rag_engine.agentic.prompts.loader import load_planning_prompt

logger = get_logger('rag_engine.agentic.agent')

# 尝试导入 DeepSeekLogger，用于类型检查
try:
    from backend.infrastructure.llms.deepseek_logger import DeepSeekLogger
except ImportError:
    DeepSeekLogger = None


def create_planning_agent(
    index_manager: IndexManager,
    llm,
    similarity_top_k: Optional[int] = None,
    similarity_cutoff: Optional[float] = None,
    enable_rerank: Optional[bool] = None,
    rerank_top_n: Optional[int] = None,
    reranker_type: Optional[str] = None,
    max_iterations: int = 5,
    verbose: bool = True,
    system_prompt: Optional[str] = None,
) -> ReActAgent:
    """创建规划 Agent（ReActAgent）
    
    Args:
        index_manager: 索引管理器
        llm: LLM 实例
        similarity_top_k: Top-K值（可选，默认使用配置）
        similarity_cutoff: 相似度阈值（可选，默认使用配置）
        enable_rerank: 是否启用重排序（可选，默认使用配置）
        rerank_top_n: 重排序Top-N（可选，默认使用配置）
        reranker_type: 重排序器类型（可选，默认使用配置）
        max_iterations: 最大迭代次数（默认5）
        verbose: 是否显示详细日志（默认True）
        system_prompt: System Prompt（可选，默认从模板加载）
        
    Returns:
        ReActAgent实例
    """
    # 提取底层的 LlamaIndex LLM（如果被包装了）
    # ReActAgent 需要原生的 LlamaIndex LLM 类型，不接受包装器
    actual_llm = llm
    if DeepSeekLogger and isinstance(llm, DeepSeekLogger):
        # 如果是 DeepSeekLogger 包装器，提取底层的 DeepSeek 实例
        actual_llm = llm._llm
        logger.debug("检测到 DeepSeekLogger 包装器，提取底层 LLM")
    elif hasattr(llm, '_llm'):
        # 通用处理：如果有 _llm 属性，尝试使用它
        actual_llm = llm._llm
        logger.debug("从包装器中提取底层 LLM")
    
    # 创建检索工具（使用原始 LLM，因为工具内部也会处理包装器）
    tools = create_retrieval_tools(
        index_manager=index_manager,
        llm=llm,  # 工具可以使用包装器
        similarity_top_k=similarity_top_k,
        similarity_cutoff=similarity_cutoff,
        enable_rerank=enable_rerank,
        rerank_top_n=rerank_top_n,
        reranker_type=reranker_type,
    )
    
    # 加载 System Prompt
    if system_prompt is None:
        system_prompt = load_planning_prompt()
    
    # 创建 ReActAgent
    # 注意：不同版本的 LlamaIndex 可能使用不同的 API
    # 尝试多种创建方式以确保兼容性
    agent = None
    error_messages = []
    
    # 方式1：尝试使用 from_tools 方法（新版本 API）
    if hasattr(ReActAgent, 'from_tools'):
        try:
            logger.debug("尝试使用 ReActAgent.from_tools 创建 Agent")
            agent = ReActAgent.from_tools(
                tools=tools,
                llm=actual_llm,  # 使用提取的底层 LLM
                verbose=verbose,
                max_iterations=max_iterations,
                system_prompt=system_prompt,
            )
            logger.info("使用 ReActAgent.from_tools 创建成功")
        except Exception as e:
            error_messages.append(f"from_tools 方式失败: {e}")
            logger.warning(f"ReActAgent.from_tools 创建失败: {e}")
    
    # 方式2：尝试使用构造函数方式
    if agent is None:
        try:
            logger.debug("尝试使用 ReActAgent 构造函数创建 Agent")
            # 尝试不同的参数组合
            try:
                agent = ReActAgent(
                    tools=tools,
                    llm=actual_llm,  # 使用提取的底层 LLM
                    verbose=verbose,
                    max_iterations=max_iterations,
                    system_prompt=system_prompt,
                )
            except TypeError:
                # 如果上面的参数组合失败，尝试更简单的参数
                agent = ReActAgent(
                    tools=tools,
                    llm=actual_llm,  # 使用提取的底层 LLM
                    verbose=verbose,
                    max_iterations=max_iterations,
                )
            logger.info("使用 ReActAgent 构造函数创建成功")
        except Exception as e:
            error_messages.append(f"构造函数方式失败: {e}")
            logger.error(f"ReActAgent 构造函数创建失败: {e}")
    
    # 如果所有方式都失败，抛出详细的错误信息
    if agent is None:
        error_detail = "\n".join(error_messages) if error_messages else "未知错误"
        available_methods = [m for m in dir(ReActAgent) if not m.startswith('_')]
        raise RuntimeError(
            f"无法创建 ReActAgent，已尝试的方法都失败了。\n"
            f"错误详情:\n{error_detail}\n"
            f"ReActAgent 可用方法: {', '.join(available_methods[:10])}...\n"
            f"请检查 LlamaIndex 版本和 API 文档。"
        )
    
    # 验证 Agent 的关键方法是否存在
    available_methods = [
        m for m in dir(agent) 
        if not m.startswith('_') and callable(getattr(agent, m))
    ]
    
    # 检查关键方法
    key_methods = ['query', 'chat', 'run']
    found_methods = [m for m in key_methods if hasattr(agent, m) and callable(getattr(agent, m))]
    
    if found_methods:
        logger.info(
            "创建规划 Agent 完成",
            tool_count=len(tools),
            max_iterations=max_iterations,
            verbose=verbose,
            available_key_methods=found_methods,
            recommended_method=found_methods[0]  # 第一个找到的方法通常是推荐的
        )
    else:
        logger.warning(
            "创建规划 Agent 完成，但未找到关键方法（query/chat/run）",
            tool_count=len(tools),
            max_iterations=max_iterations,
            verbose=verbose,
            available_methods_sample=available_methods[:10],  # 只显示前10个
            total_methods=len(available_methods),
            note="可能需要检查 LlamaIndex 版本和 API 文档"
        )
    
    # 记录所有可用方法（调试级别）
    logger.debug(
        "Agent 可用方法列表",
        methods=available_methods[:20],  # 只记录前20个，避免日志过长
        total_count=len(available_methods)
    )
    
    return agent

