#!/usr/bin/env python3
"""
测试 Markdown 格式化功能
验证 Prompt 模板注入和格式化效果
"""

import sys
from src.indexer import IndexManager
from src.query_engine import QueryEngine
from src.logger import setup_logger

logger = setup_logger('test_markdown')


def test_markdown_formatting():
    """测试 Markdown 格式化功能"""
    
    print("\n" + "="*60)
    print("🧪 测试 Markdown 格式化功能")
    print("="*60 + "\n")
    
    # 初始化索引管理器
    print("📦 初始化索引管理器...")
    try:
        index_manager = IndexManager()
        print("✅ 索引管理器初始化成功\n")
    except Exception as e:
        print(f"❌ 索引管理器初始化失败: {e}")
        return
    
    # 测试问题
    test_questions = [
        "什么是系统？",
        "系统科学的基本概念有哪些？",
        "解释一下涌现性的含义",
    ]
    
    # 测试1: 启用 Markdown 格式化
    print("\n" + "-"*60)
    print("📝 测试1: 启用 Markdown 格式化")
    print("-"*60 + "\n")
    
    try:
        query_engine_md = QueryEngine(
            index_manager,
            enable_markdown_formatting=True
        )
        print("✅ QueryEngine 初始化成功（Markdown 已启用）\n")
        
        for i, question in enumerate(test_questions[:1], 1):  # 只测试第一个问题
            print(f"\n🔍 问题 {i}: {question}\n")
            
            try:
                answer, sources, _ = query_engine_md.query(question)
                
                print("📄 生成的答案：")
                print("-" * 60)
                print(answer[:500] + "..." if len(answer) > 500 else answer)
                print("-" * 60)
                
                # 检查格式
                has_heading = "##" in answer or "# " in answer
                has_list = "\n- " in answer or "\n* " in answer
                has_bold = "**" in answer
                
                print(f"\n✅ 格式检测：")
                print(f"   - 包含标题: {'✅' if has_heading else '❌'}")
                print(f"   - 包含列表: {'✅' if has_list else '❌'}")
                print(f"   - 包含粗体: {'✅' if has_bold else '❌'}")
                
                if sources:
                    print(f"\n📚 引用来源数: {len(sources)}")
                
            except Exception as e:
                print(f"❌ 查询失败: {e}")
                logger.error(f"查询失败: {e}", exc_info=True)
    
    except Exception as e:
        print(f"❌ QueryEngine 初始化失败: {e}")
        logger.error(f"QueryEngine 初始化失败: {e}", exc_info=True)
    
    # 测试2: 禁用 Markdown 格式化（对比）
    print("\n\n" + "-"*60)
    print("📝 测试2: 禁用 Markdown 格式化（对比）")
    print("-"*60 + "\n")
    
    try:
        query_engine_plain = QueryEngine(
            index_manager,
            enable_markdown_formatting=False
        )
        print("✅ QueryEngine 初始化成功（Markdown 已禁用）\n")
        
        question = test_questions[0]
        print(f"🔍 问题: {question}\n")
        
        try:
            answer, sources, _ = query_engine_plain.query(question)
            
            print("📄 生成的答案：")
            print("-" * 60)
            print(answer[:500] + "..." if len(answer) > 500 else answer)
            print("-" * 60)
            
            # 检查格式
            has_heading = "##" in answer or "# " in answer
            has_list = "\n- " in answer or "\n* " in answer
            has_bold = "**" in answer
            
            print(f"\n格式检测：")
            print(f"   - 包含标题: {'✅' if has_heading else '❌'}")
            print(f"   - 包含列表: {'✅' if has_list else '❌'}")
            print(f"   - 包含粗体: {'✅' if has_bold else '❌'}")
        
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            logger.error(f"查询失败: {e}", exc_info=True)
    
    except Exception as e:
        print(f"❌ QueryEngine 初始化失败: {e}")
        logger.error(f"QueryEngine 初始化失败: {e}", exc_info=True)
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_markdown_formatting()

