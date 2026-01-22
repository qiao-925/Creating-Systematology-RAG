"""
ReActAgent 修复验证测试脚本

用于验证 ReActAgent 实现修复后的功能：
1. 检查 Agent 的可用方法
2. 验证方法调用是否正确
3. 检查响应对象结构
4. 验证 sources 和 reasoning 提取
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.infrastructure.indexer import IndexManager
from backend.infrastructure.config import config
from backend.business.rag_engine.agentic.agent.planning import create_planning_agent
from backend.infrastructure.llms import create_deepseek_llm_for_query
from backend.infrastructure.logger import get_logger

logger = get_logger('test.reactagent_validation')


def test_agent_methods():
    """测试 Agent 的可用方法"""
    print("\n" + "="*60)
    print("测试 1: 检查 Agent 的可用方法")
    print("="*60)
    
    try:
        # 初始化必要的组件
        index_manager = IndexManager()
        llm = create_deepseek_llm_for_query(
            api_key=config.DEEPSEEK_API_KEY,
            model=config.LLM_MODEL,
            max_tokens=4096,
        )
        
        # 创建 Agent
        agent = create_planning_agent(
            index_manager=index_manager,
            llm=llm,
            max_iterations=3,
            verbose=True,
        )
        
        # 检查可用方法
        available_methods = [
            m for m in dir(agent) 
            if not m.startswith('_') and callable(getattr(agent, m))
        ]
        
        print(f"\nAgent 类型: {type(agent).__name__}")
        print(f"可用方法总数: {len(available_methods)}")
        print(f"\n关键方法检查:")
        
        key_methods = ['query', 'chat', 'run', 'stream_chat']
        for method_name in key_methods:
            has_method = hasattr(agent, method_name) and callable(getattr(agent, method_name))
            status = "✓" if has_method else "✗"
            print(f"  {status} {method_name}: {'存在' if has_method else '不存在'}")
        
        print(f"\n所有可用方法（前20个）:")
        for i, method in enumerate(available_methods[:20], 1):
            print(f"  {i}. {method}")
        
        return agent, available_methods
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None, []


def test_agent_response_structure(agent):
    """测试 Agent 响应对象结构"""
    print("\n" + "="*60)
    print("测试 2: 检查 Agent 响应对象结构")
    print("="*60)
    
    if agent is None:
        print("❌ Agent 未创建，跳过测试")
        return None
    
    try:
        # 检查可用方法
        if hasattr(agent, 'query') and callable(getattr(agent, 'query')):
            method = agent.query
            method_name = 'query'
        elif hasattr(agent, 'chat') and callable(getattr(agent, 'chat')):
            method = agent.chat
            method_name = 'chat'
        elif hasattr(agent, 'run') and callable(getattr(agent, 'run')):
            method = agent.run
            method_name = 'run'
        else:
            print("❌ 未找到可用的调用方法")
            return None
        
        print(f"\n使用方法: {method_name}")
        print(f"测试查询: '系统工程的基本概念是什么？'")
        
        # 调用 Agent（使用简单查询，避免长时间等待）
        response = method("系统工程的基本概念是什么？")
        
        print(f"\n响应对象类型: {type(response).__name__}")
        print(f"响应对象属性:")
        
        response_attrs = [attr for attr in dir(response) if not attr.startswith('_')]
        for i, attr in enumerate(response_attrs[:15], 1):  # 只显示前15个
            try:
                value = getattr(response, attr)
                if not callable(value):
                    value_str = str(value)[:50] if value else "None"
                    print(f"  {i}. {attr}: {value_str}")
            except Exception as e:
                print(f"  {i}. {attr}: <无法访问: {e}>")
        
        # 检查关键属性
        print(f"\n关键属性检查:")
        key_attrs = ['source_nodes', 'sources', 'metadata', 'message', 'reasoning_content']
        for attr in key_attrs:
            has_attr = hasattr(response, attr)
            status = "✓" if has_attr else "✗"
            if has_attr:
                try:
                    value = getattr(response, attr)
                    value_preview = str(value)[:50] if value else "None"
                    print(f"  {status} {attr}: {value_preview}")
                except Exception as e:
                    print(f"  {status} {attr}: <访问错误: {e}>")
            else:
                print(f"  {status} {attr}: 不存在")
        
        return response
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_extraction_functions(response, agent):
    """测试提取函数"""
    print("\n" + "="*60)
    print("测试 3: 测试 sources 和 reasoning 提取")
    print("="*60)
    
    if response is None:
        print("❌ 响应对象为空，跳过测试")
        return
    
    try:
        from backend.business.rag_engine.agentic.extraction import (
            extract_sources_from_agent,
            extract_reasoning_from_agent,
        )
        
        # 测试 sources 提取
        print("\n测试 sources 提取:")
        sources = extract_sources_from_agent(response, agent=agent)
        print(f"  提取到的 sources 数量: {len(sources)}")
        if sources:
            print(f"  第一个 source 示例:")
            for key, value in list(sources[0].items())[:3]:
                value_str = str(value)[:50] if value else "None"
                print(f"    {key}: {value_str}")
        else:
            print("  ⚠️  未提取到 sources")
        
        # 测试 reasoning 提取
        print("\n测试 reasoning 提取:")
        reasoning = extract_reasoning_from_agent(response, agent=agent)
        if reasoning:
            print(f"  提取到的 reasoning 长度: {len(str(reasoning))}")
            print(f"  Reasoning 预览: {str(reasoning)[:200]}...")
        else:
            print("  ⚠️  未提取到 reasoning")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("ReActAgent 修复验证测试")
    print("="*60)
    
    # 测试 1: 检查 Agent 方法
    agent, available_methods = test_agent_methods()
    
    if agent is None:
        print("\n❌ Agent 创建失败，无法继续测试")
        return
    
    # 测试 2: 检查响应对象结构
    response = test_agent_response_structure(agent)
    
    # 测试 3: 测试提取函数
    test_extraction_functions(response, agent)
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    main()

