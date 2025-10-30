#!/usr/bin/env python3
"""
CLI工具
提供命令行操作：批量导入文档、索引管理、测试查询等
"""

import sys
import argparse
from pathlib import Path
from typing import List
import os

# 优先设置 UTF-8 编码（确保 emoji 正确显示）
try:
    from src.encoding import setup_utf8_encoding
    setup_utf8_encoding()
except ImportError:
    # 如果 encoding 模块尚未加载，手动设置基础编码
    os.environ["PYTHONIOENCODING"] = "utf-8"

from src.config import config
from src.indexer import IndexManager, create_index_from_directory, create_index_from_urls
from src.query_engine import QueryEngine, format_sources
from src.chat_manager import ChatManager
from src.data_loader import (
    load_documents_from_directory, 
    load_documents_from_urls,
    load_documents_from_github
)


def cmd_import_docs(args):
    """导入文档命令"""
    print("=" * 60)
    print("📥 导入文档")
    print("=" * 60)
    
    directory = Path(args.directory)
    if not directory.exists():
        print(f"❌ 目录不存在: {directory}")
        return 1
    
    try:
        # 加载文档
        print(f"\n📂 从目录加载文档: {directory}")
        documents = load_documents_from_directory(directory, recursive=args.recursive)
        
        if not documents:
            print("⚠️  未找到任何文档")
            return 1
        
        # 创建或更新索引
        print(f"\n🔨 构建索引...")
        index_manager = IndexManager(collection_name=args.collection)
        _, _ = index_manager.build_index(documents)
        
        # 显示统计
        stats = index_manager.get_stats()
        print(f"\n📊 索引统计:")
        print(f"   集合名称: {stats['collection_name']}")
        print(f"   文档数量: {stats['document_count']}")
        print(f"   Embedding模型: {stats['embedding_model']}")
        
        print("\n✅ 导入完成")
        return 0
        
    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        return 1


def cmd_import_urls(args):
    """从URL导入命令"""
    print("=" * 60)
    print("🌐 从URL导入文档")
    print("=" * 60)
    
    # 读取URL列表
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
    else:
        urls = args.urls
    
    if not urls:
        print("❌ 未提供URL")
        return 1
    
    try:
        # 加载网页
        print(f"\n🌍 加载 {len(urls)} 个网页...")
        documents = load_documents_from_urls(urls)
        
        if not documents:
            print("⚠️  未成功加载任何网页")
            return 1
        
        # 创建或更新索引
        print(f"\n🔨 构建索引...")
        index_manager = IndexManager(collection_name=args.collection)
        _, _ = index_manager.build_index(documents)
        
        # 显示统计
        stats = index_manager.get_stats()
        print(f"\n📊 索引统计:")
        print(f"   文档数量: {stats['document_count']}")
        
        print("\n✅ 导入完成")
        return 0
        
    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        return 1


def cmd_import_github(args):
    """从GitHub仓库导入命令"""
    print("=" * 60)
    print("📦 从GitHub仓库导入文档")
    print("=" * 60)
    
    owner = args.owner
    repo = args.repo
    branch = args.branch or config.GITHUB_DEFAULT_BRANCH
    
    try:
        # 加载GitHub仓库（仅支持公开仓库）
        print(f"\n📂 加载仓库: {owner}/{repo} (分支: {branch})")
        documents = load_documents_from_github(
            owner=owner,
            repo=repo,
            branch=branch
        )
        
        if not documents:
            print("⚠️  未成功加载任何文件")
            return 1
        
        # 创建或更新索引
        print(f"\n🔨 构建索引...")
        index_manager = IndexManager(collection_name=args.collection)
        _, _ = index_manager.build_index(documents)
        
        # 显示统计
        stats = index_manager.get_stats()
        print(f"\n📊 索引统计:")
        print(f"   文档数量: {stats['document_count']}")
        
        print("\n✅ 导入完成")
        return 0
        
    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        return 1


def cmd_query(args):
    """查询命令"""
    print("=" * 60)
    print("🔍 执行查询")
    print("=" * 60)
    
    try:
        # 初始化索引管理器
        index_manager = IndexManager(collection_name=args.collection)
        stats = index_manager.get_stats()
        
        if stats['document_count'] == 0:
            print("⚠️  索引为空，请先导入文档")
            return 1
        
        print(f"\n📊 索引信息: {stats['document_count']} 个文档\n")
        
        # 创建查询引擎
        query_engine = QueryEngine(index_manager)
        
        # 执行查询
        print(f"💬 问题: {args.question}\n")
        answer, sources, _ = query_engine.query(args.question)
        
        print(f"🤖 答案:\n{answer}\n")
        print(format_sources(sources))
        
        return 0
        
    except ValueError as e:
        print(f"❌ 请先设置DEEPSEEK_API_KEY环境变量")
        return 1
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return 1


def cmd_chat(args):
    """交互式对话命令"""
    print("=" * 60)
    print("💬 交互式对话模式")
    print("=" * 60)
    print("输入 'exit' 或 'quit' 退出")
    print("输入 'clear' 清空对话历史")
    print("输入 'save' 保存当前会话")
    print("=" * 60)
    
    try:
        # 初始化
        index_manager = IndexManager(collection_name=args.collection)
        stats = index_manager.get_stats()
        
        if stats['document_count'] == 0:
            print("⚠️  索引为空，请先导入文档")
            return 1
        
        print(f"\n📊 索引信息: {stats['document_count']} 个文档")
        
        # 创建对话管理器
        chat_manager = ChatManager(index_manager)
        chat_manager.start_session()
        
        print("\n✅ 对话已开始，请提问：\n")
        
        # 对话循环
        while True:
            try:
                question = input("👤 您: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['exit', 'quit']:
                    print("\n👋 再见！")
                    break
                
                if question.lower() == 'clear':
                    chat_manager.reset_session()
                    print("🔄 对话历史已清空\n")
                    continue
                
                if question.lower() == 'save':
                    chat_manager.save_current_session()
                    print("💾 会话已保存\n")
                    continue
                
                # 执行对话
                answer, sources = chat_manager.chat(question)
                
                print(f"\n🤖 AI: {answer}\n")
                
                if args.show_sources and sources:
                    print(format_sources(sources))
                    print()
                
            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}\n")
        
        # 询问是否保存
        save = input("\n💾 是否保存会话？(y/n): ").strip().lower()
        if save == 'y':
            chat_manager.save_current_session()
            print("✅ 会话已保存")
        
        return 0
        
    except ValueError as e:
        print(f"❌ 请先设置DEEPSEEK_API_KEY环境变量")
        return 1
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return 1


def cmd_stats(args):
    """显示统计信息命令"""
    print("=" * 60)
    print("📊 索引统计信息")
    print("=" * 60)
    
    try:
        index_manager = IndexManager(collection_name=args.collection)
        stats = index_manager.get_stats()
        
        print(f"\n集合名称: {stats['collection_name']}")
        print(f"文档数量: {stats['document_count']}")
        print(f"Embedding模型: {stats['embedding_model']}")
        print(f"分块大小: {stats['chunk_size']}")
        print(f"分块重叠: {stats['chunk_overlap']}")
        
        return 0
        
    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")
        return 1


def cmd_clear(args):
    """清空索引命令"""
    print("=" * 60)
    print("🗑️  清空索引")
    print("=" * 60)
    
    # 确认
    if not args.force:
        confirm = input(f"\n⚠️  确认要清空集合 '{args.collection}' 吗？(yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ 操作已取消")
            return 0
    
    try:
        index_manager = IndexManager(collection_name=args.collection)
        index_manager.clear_index()
        print("\n✅ 索引已清空")
        return 0
        
    except Exception as e:
        print(f"❌ 清空失败: {e}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="系统科学知识库RAG应用 - CLI工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 导入文档
  python main.py import-docs ./data/raw
  
  # 从URL导入
  python main.py import-urls url1 url2 url3
  python main.py import-urls --file urls.txt
  
  # 从GitHub仓库导入（仅支持公开仓库）
  python main.py import-github microsoft TypeScript --branch main
  
  # 单次查询
  python main.py query "什么是系统科学？"
  
  # 交互式对话
  python main.py chat
  
  # 查看统计
  python main.py stats
  
  # 清空索引
  python main.py clear --force
        """
    )
    
    parser.add_argument(
        '--collection',
        default=config.CHROMA_COLLECTION_NAME,
        help=f"集合名称 (默认: {config.CHROMA_COLLECTION_NAME})"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # import-docs命令
    parser_import = subparsers.add_parser('import-docs', help='导入本地文档')
    parser_import.add_argument('directory', help='文档目录路径')
    parser_import.add_argument('--recursive', action='store_true', help='递归加载子目录')
    parser_import.set_defaults(func=cmd_import_docs)
    
    # import-urls命令
    parser_urls = subparsers.add_parser('import-urls', help='从URL导入文档')
    parser_urls.add_argument('urls', nargs='*', help='URL列表')
    parser_urls.add_argument('--file', help='包含URL列表的文件')
    parser_urls.set_defaults(func=cmd_import_urls)
    
    # import-github命令（仅支持公开仓库）
    parser_github = subparsers.add_parser('import-github', help='从GitHub仓库导入文档（仅支持公开仓库）')
    parser_github.add_argument('owner', help='仓库所有者')
    parser_github.add_argument('repo', help='仓库名称')
    parser_github.add_argument('--branch', help=f'分支名称 (默认: {config.GITHUB_DEFAULT_BRANCH})')
    parser_github.set_defaults(func=cmd_import_github)
    
    # query命令
    parser_query = subparsers.add_parser('query', help='执行单次查询')
    parser_query.add_argument('question', help='问题')
    parser_query.set_defaults(func=cmd_query)
    
    # chat命令
    parser_chat = subparsers.add_parser('chat', help='交互式对话')
    parser_chat.add_argument('--show-sources', action='store_true', help='显示引用来源')
    parser_chat.set_defaults(func=cmd_chat)
    
    # stats命令
    parser_stats = subparsers.add_parser('stats', help='显示统计信息')
    parser_stats.set_defaults(func=cmd_stats)
    
    # clear命令
    parser_clear = subparsers.add_parser('clear', help='清空索引')
    parser_clear.add_argument('--force', action='store_true', help='跳过确认')
    parser_clear.set_defaults(func=cmd_clear)
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # 确保目录存在
    config.ensure_directories()
    
    # 执行命令
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
