"""
GitHub仓库端到端集成测试
测试从GitHub仓库克隆、文档加载、索引构建到查询检索的完整流程

核心原则：
- 只保留一个完整的端到端测试
- 所有操作都在测试中实时执行，不预先构建
- 直接使用项目实际代码，确保测试真实有效
"""

import pytest
import os
import sys
from dotenv import load_dotenv

from src.data_loader import load_documents_from_github
from src.indexer import IndexManager
from src.metadata_manager import MetadataManager
from src.query_engine import QueryEngine
from src.logger import setup_logger

# 设置logger以便测试中使用
logger = setup_logger('test_github_e2e')

# 加载.env文件（如果存在）
load_dotenv()


# ==================== 测试配置 ====================

# 测试用的GitHub仓库配置
# 优先级：环境变量 > .env文件 > 默认值
TEST_GITHUB_REPO = {
    "owner": os.getenv("TEST_GITHUB_OWNER", "octocat"),
    "repo": os.getenv("TEST_GITHUB_REPO", "Hello-World"),
    "branch": os.getenv("TEST_GITHUB_BRANCH", "main")  # GitHub 默认分支已改为 main
}

# 是否显示详细进度（可通过环境变量控制，默认True以查看完整执行过程）
SHOW_PROGRESS = os.getenv("TEST_SHOW_PROGRESS", "true").lower() == "true"


# ==================== 测试标记 ====================

pytestmark = [
    pytest.mark.integration,
    pytest.mark.github_e2e,
    pytest.mark.slow,
]


# ==================== 端到端测试 ====================

@pytest.mark.integration
@pytest.mark.github_e2e
def test_github_e2e_full_pipeline(
    temp_vector_store,
    tmp_path
):
    """GitHub仓库完整端到端测试
    
    测试完整流程：
    1. GitHub仓库克隆/更新
    2. 文档加载和解析
    3. 索引构建（实时）
    4. 向量检索
    5. 查询引擎（如果配置了API密钥）
    
    所有操作都在测试中实时执行，不使用预先构建的索引。
    """
    owner = TEST_GITHUB_REPO["owner"]
    repo = TEST_GITHUB_REPO["repo"]
    branch = TEST_GITHUB_REPO["branch"]
    
    # 强制刷新输出，确保立即可见
    def log_print(msg):
        print(msg, flush=True)
        logger.info(msg)
    
    log_print(f"\n{'='*70}")
    log_print(f"🚀 GitHub仓库端到端测试")
    log_print(f"{'='*70}")
    log_print(f"仓库: {owner}/{repo}@{branch}")
    log_print(f"进度显示: {'启用' if SHOW_PROGRESS else '禁用'}")
    log_print(f"{'='*70}\n")
    
    log_print("🔍 调用项目实际代码路径:")
    log_print(f"   → load_documents_from_github() [src/data_loader.py]")
    log_print(f"      → GitHubSource.get_file_paths() [src/data_source/github_source.py]")
    log_print(f"         → GitRepositoryManager.clone_or_update() [src/git_repository_manager.py]")
    log_print(f"            → 执行真实 git clone/pull 命令")
    log_print(f"      → DocumentParser.parse_files() [src/data_parser/document_parser.py]")
    log_print(f"      → 返回 Document 对象列表")
    log_print(f"   → IndexManager.build_index() [src/indexer.py]")
    log_print(f"      → 实时构建向量索引")
    log_print(f"   → IndexManager.search() [src/indexer.py]")
    log_print(f"      → 向量检索")
    log_print(f"   → QueryEngine.query() [src/query_engine.py]")
    log_print(f"      → RAG查询（如配置了API密钥）\n")
    
    # ========== 步骤1: GitHub仓库克隆和文档加载 ==========
    log_print("=" * 70)
    log_print("步骤1: GitHub仓库克隆和文档加载")
    log_print("=" * 70)
    
    documents = load_documents_from_github(
        owner=owner,
        repo=repo,
        branch=branch,
        clean=True,
        show_progress=SHOW_PROGRESS
    )
    
    # 验证文档加载
    assert len(documents) > 0, f"应该加载到文档，但实际加载了 {len(documents)} 个"
    assert all(hasattr(doc, 'text') for doc in documents), "所有文档应该有text属性"
    assert all(hasattr(doc, 'metadata') for doc in documents), "所有文档应该有metadata属性"
    
    # 验证元数据
    for doc in documents:
        assert doc.metadata.get('source_type') == 'github', "文档源类型应该是github"
        assert doc.metadata.get('repository') == f"{owner}/{repo}", "仓库信息应该正确"
        assert doc.metadata.get('branch') == branch, "分支信息应该正确"
        assert 'file_path' in doc.metadata, "应该有文件路径"
    
    log_print(f"✅ 成功加载 {len(documents)} 个文档")
    log_print(f"   第一个文档: {documents[0].metadata.get('file_path', 'N/A')}")
    log_print(f"   文档总长度: {sum(len(doc.text) for doc in documents)} 字符\n")
    
    # ========== 步骤2: 实时构建索引 ==========
    log_print("=" * 70)
    log_print("步骤2: 实时构建向量索引")
    log_print("=" * 70)
    
    # 创建索引管理器（使用临时存储）
    index_manager = IndexManager(
        collection_name="github_e2e_test",
        persist_dir=temp_vector_store
    )
    
    # 实时构建索引（不预先构建）
    index, vector_ids_map = index_manager.build_index(
        documents,
        show_progress=SHOW_PROGRESS
    )
    
    # 验证索引构建
    assert index is not None, "索引应该成功构建"
    stats = index_manager.get_stats()
    assert stats['document_count'] > 0, f"索引应该包含文档，但实际为 {stats['document_count']}"
    assert stats['embedding_model'] is not None, "应该有embedding模型信息"
    
    log_print(f"✅ 索引构建完成")
    log_print(f"   向量数量: {stats['document_count']}")
    log_print(f"   Embedding模型: {stats['embedding_model']}")
    log_print(f"   集合名称: {stats['collection_name']}\n")
    
    # ========== 步骤3: 向量检索测试 ==========
    log_print("=" * 70)
    log_print("步骤3: 向量检索测试")
    log_print("=" * 70)
    
    query = "Hello"
    results = index_manager.search(query, top_k=5)
    
    # 验证检索结果
    assert len(results) > 0, f"应该检索到结果，但实际检索到 {len(results)} 个"
    assert all('text' in r for r in results), "所有结果应该有text字段"
    assert all('score' in r for r in results), "所有结果应该有score字段"
    assert all('metadata' in r for r in results), "所有结果应该有metadata字段"
    
    # 验证相似度排序
    scores = [r['score'] for r in results]
    assert scores == sorted(scores, reverse=True), "结果应该按相似度降序排列"
    
    log_print(f"✅ 检索成功")
    log_print(f"   查询: '{query}'")
    log_print(f"   找到 {len(results)} 个相关文档")
    log_print(f"   相似度分数范围: {min(scores):.4f} - {max(scores):.4f}")
    log_print(f"   最佳匹配文档: {results[0]['metadata'].get('file_path', 'N/A')}\n")
    
    # ========== 步骤4: 查询引擎测试（如果配置了API密钥）==========
    log_print("=" * 70)
    log_print("步骤4: RAG查询引擎测试（可选）")
    log_print("=" * 70)
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key and not api_key.startswith("test_"):
        log_print("检测到真实的DEEPSEEK_API_KEY，执行RAG查询测试...")
        
        # 创建查询引擎（使用刚构建的索引）
        query_engine = QueryEngine(index_manager)
        
        # 执行查询
        question = "What is this repository about?"
        answer, sources, trace = query_engine.query(question, collect_trace=False)
        
        # 验证结果
        assert isinstance(answer, str), "答案应该是字符串"
        assert len(answer) > 10, "答案应该有足够的内容"
        assert isinstance(sources, list), "引用来源应该是列表"
        
        log_print(f"✅ RAG查询成功")
        log_print(f"   问题: {question}")
        log_print(f"   答案长度: {len(answer)} 字符")
        log_print(f"   引用数量: {len(sources)} 个")
        log_print(f"   答案预览: {answer[:200]}...\n")
    else:
        log_print("⚠️  未配置真实的DEEPSEEK_API_KEY，跳过RAG查询测试")
        log_print("   如需测试RAG查询，请设置环境变量: DEEPSEEK_API_KEY=your_key\n")
    
    # ========== 测试完成 ==========
    log_print("=" * 70)
    log_print("✅ 端到端测试完成")
    log_print("=" * 70)
    log_print(f"测试覆盖的完整流程:")
    log_print(f"  ✓ GitHub仓库克隆/更新")
    log_print(f"  ✓ 文档加载和解析")
    log_print(f"  ✓ 元数据验证")
    log_print(f"  ✓ 索引实时构建")
    log_print(f"  ✓ 向量检索")
    if api_key and not api_key.startswith("test_"):
        log_print(f"  ✓ RAG查询引擎")
    log_print("=" * 70)
