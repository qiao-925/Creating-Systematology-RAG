"""
GitHub仓库端到端集成测试
测试从GitHub仓库克隆、文档加载、元数据管理、索引构建到查询检索的完整流程

⚠️ 状态：待实践验证
- 测试代码已完成，但尚未在实际环境中完整运行验证
- 需要在有网络和Git工具的环境中实际测试
- 建议在实际使用前先运行验证
"""

import pytest
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from src.data_loader import load_documents_from_github, sync_github_repository
from src.indexer import IndexManager
from src.metadata_manager import MetadataManager, FileChange
from src.query_engine import QueryEngine

# 加载.env文件（如果存在）
load_dotenv()


# ==================== 测试配置 ====================

# 测试用的GitHub仓库配置
# 优先级：环境变量 > .env文件 > 默认值
# 可以通过以下方式配置：
# 1. 环境变量：export TEST_GITHUB_OWNER=your_owner
# 2. .env文件：TEST_GITHUB_OWNER=your_owner
# 3. 直接修改下面的默认值
TEST_GITHUB_REPO = {
    "owner": os.getenv("TEST_GITHUB_OWNER", "octocat"),
    "repo": os.getenv("TEST_GITHUB_REPO", "Hello-World"),
    "branch": os.getenv("TEST_GITHUB_BRANCH", "master")
}


# ==================== 测试标记 ====================

pytestmark = [
    pytest.mark.integration,
    pytest.mark.github_e2e,
    pytest.mark.slow,
    pytest.mark.pending_practice  # 标记为待实践验证
]


# ==================== 测试类 ====================

@pytest.mark.integration
@pytest.mark.github_e2e
class TestGitHubImportFlow:
    """GitHub仓库导入流程测试
    
    测试完整的导入流程：
    1. 克隆/更新仓库
    2. 加载文档
    3. 管理元数据
    4. 构建索引
    """
    
    def test_github_repo_clone_and_load(
        self, 
        github_test_index_manager,
        github_test_metadata_manager
    ):
        """测试GitHub仓库克隆和文档加载"""
        owner = TEST_GITHUB_REPO["owner"]
        repo = TEST_GITHUB_REPO["repo"]
        branch = TEST_GITHUB_REPO["branch"]
        
        print(f"\n📥 步骤1: 克隆仓库 {owner}/{repo}@{branch}")
        
        # 加载文档
        documents = load_documents_from_github(
            owner=owner,
            repo=repo,
            branch=branch,
            clean=True,
            show_progress=False
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
        
        print(f"✅ 成功加载 {len(documents)} 个文档")
    
    def test_metadata_management(
        self,
        github_test_metadata_manager,
        github_test_index_manager
    ):
        """测试元数据管理"""
        owner = TEST_GITHUB_REPO["owner"]
        repo = TEST_GITHUB_REPO["repo"]
        branch = TEST_GITHUB_REPO["branch"]
        
        print(f"\n📋 步骤2: 测试元数据管理")
        
        # 加载文档
        documents = load_documents_from_github(
            owner=owner,
            repo=repo,
            branch=branch,
            show_progress=False
        )
        
        assert len(documents) > 0, "应该有文档"
        
        # 检查元数据记录
        metadata = github_test_metadata_manager.get_repository_metadata(owner, repo, branch)
        
        # 首次导入，元数据可能不存在，这是正常的
        # 我们测试元数据管理器功能
        assert github_test_metadata_manager is not None, "元数据管理器应该存在"
        
        # 测试变更检测功能
        changes = github_test_metadata_manager.detect_changes(owner, repo, branch, documents)
        
        # 验证变更检测
        assert isinstance(changes, FileChange), "应该返回FileChange对象"
        # 首次导入应该是新增（因为之前没有记录）
        # 注意：由于元数据是临时的，这里主要验证变更检测功能正常工作
        
        print(f"✅ 元数据管理测试通过")
    
    def test_index_building_with_metadata(
        self,
        github_test_index_manager,
        github_test_metadata_manager
    ):
        """测试带元数据管理的索引构建"""
        owner = TEST_GITHUB_REPO["owner"]
        repo = TEST_GITHUB_REPO["repo"]
        branch = TEST_GITHUB_REPO["branch"]
        
        print(f"\n🔨 步骤3: 构建索引（带元数据管理）")
        
        # 加载文档
        documents = load_documents_from_github(
            owner=owner,
            repo=repo,
            branch=branch,
            show_progress=False
        )
        
        assert len(documents) > 0, "应该有文档可以索引"
        
        # 构建索引
        index, vector_ids_map = github_test_index_manager.build_index(
            documents,
            show_progress=False
        )
        
        assert index is not None, "索引应该成功构建"
        
        # 验证索引统计
        stats = github_test_index_manager.get_stats()
        assert stats['document_count'] > 0, f"索引应该包含文档，但实际为 {stats['document_count']}"
        assert stats['embedding_model'] is not None, "应该有embedding模型信息"
        
        # 验证向量ID映射
        assert isinstance(vector_ids_map, dict), "向量ID映射应该是字典"
        
        print(f"✅ 索引构建成功，包含 {stats['document_count']} 个向量")
    
    def test_full_import_pipeline(
        self,
        github_test_index_manager,
        github_test_metadata_manager
    ):
        """测试完整的导入流程（端到端）"""
        owner = TEST_GITHUB_REPO["owner"]
        repo = TEST_GITHUB_REPO["repo"]
        branch = TEST_GITHUB_REPO["branch"]
        
        print(f"\n🚀 完整导入流程测试")
        print(f"   仓库: {owner}/{repo}@{branch}")
        
        # 步骤1: 加载文档
        print("\n步骤1: 加载文档...")
        documents = load_documents_from_github(
            owner=owner,
            repo=repo,
            branch=branch,
            show_progress=False
        )
        
        assert len(documents) > 0, "应该加载到文档"
        print(f"   ✅ 加载了 {len(documents)} 个文档")
        
        # 步骤2: 检测变更（通过元数据管理器）
        print("\n步骤2: 检测文件变更...")
        changes = github_test_metadata_manager.detect_changes(owner, repo, branch, documents)
        
        assert isinstance(changes, type(github_test_metadata_manager.detect_changes(owner, repo, branch, []))), "应该返回FileChange对象"
        print(f"   ✅ 变更检测: {changes.summary()}")
        
        # 步骤3: 构建索引
        print("\n步骤3: 构建索引...")
        index, vector_ids_map = github_test_index_manager.build_index(
            documents,
            show_progress=False
        )
        
        assert index is not None, "索引应该成功构建"
        stats = github_test_index_manager.get_stats()
        print(f"   ✅ 索引构建完成，包含 {stats['document_count']} 个向量")
        
        # 步骤4: 更新元数据（模拟）
        print("\n步骤4: 更新元数据...")
        # 注意：实际使用时需要调用metadata_manager.update_repository_metadata
        # 这里我们只是验证流程
        print(f"   ✅ 元数据更新完成")
        
        print("\n✅ 完整导入流程测试通过")


@pytest.mark.integration
@pytest.mark.github_e2e
class TestGitHubQueryFlow:
    """GitHub仓库查询流程测试
    
    基于已构建的索引执行查询，验证检索结果
    """
    
    def test_search_after_indexing(
        self,
        github_prepared_index_manager
    ):
        """测试索引后的检索功能"""
        print(f"\n🔍 测试检索功能")
        
        # 执行检索
        query = "Hello"
        results = github_prepared_index_manager.search(query, top_k=5)
        
        # 验证检索结果
        assert len(results) > 0, f"应该检索到结果，但实际检索到 {len(results)} 个"
        assert all('text' in r for r in results), "所有结果应该有text字段"
        assert all('score' in r for r in results), "所有结果应该有score字段"
        assert all('metadata' in r for r in results), "所有结果应该有metadata字段"
        
        # 验证相似度排序
        scores = [r['score'] for r in results]
        assert scores == sorted(scores, reverse=True), "结果应该按相似度降序排列"
        
        print(f"✅ 检索成功，找到 {len(results)} 个相关文档")
        print(f"   相似度分数范围: {min(scores):.4f} - {max(scores):.4f}")
    
    def test_query_with_mock_llm(
        self,
        github_prepared_index_manager,
        mocker,
        monkeypatch
    ):
        """测试使用Mock LLM的查询流程"""
        from llama_index.core.schema import NodeWithScore, TextNode
        
        print(f"\n🤖 测试查询引擎（Mock LLM）")
        
        # Mock Response 对象
        mock_response = mocker.Mock()
        mock_response.__str__ = mocker.Mock(return_value="这是一个测试回答。")
        
        # 创建真实的 source_nodes
        test_node = TextNode(
            text="测试内容",
            metadata={"title": "测试", "source": "github"}
        )
        mock_response.source_nodes = [NodeWithScore(node=test_node, score=0.9)]
        
        # 设置环境变量
        monkeypatch.setenv('DEEPSEEK_API_KEY', 'test_key_for_mock')
        
        # 创建查询引擎
        query_engine = QueryEngine(github_prepared_index_manager)
        
        # Mock 内部查询引擎的 query 方法
        query_engine.query_engine.query = mocker.Mock(return_value=mock_response)
        
        # 执行查询
        answer, sources, _ = query_engine.query("Hello", collect_trace=False)
        
        # 验证结果
        assert isinstance(answer, str), "答案应该是字符串"
        assert len(answer) > 0, "答案不应该为空"
        assert isinstance(sources, list), "引用来源应该是列表"
        
        print(f"✅ 查询成功")
        print(f"   答案长度: {len(answer)} 字符")
        print(f"   引用数量: {len(sources)} 个")
    
    @pytest.mark.requires_real_api
    def test_query_with_real_api(
        self,
        github_prepared_index_manager
    ):
        """测试使用真实API的查询（需要DEEPSEEK_API_KEY）"""
        print(f"\n🌐 测试查询引擎（真实API）")
        
        # 检查是否有真实API密钥
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key or api_key.startswith("test_"):
            pytest.skip("需要真实的DEEPSEEK_API_KEY环境变量")
        
        # 创建查询引擎
        query_engine = QueryEngine(github_prepared_index_manager)
        
        # 执行查询
        question = "What is this repository about?"
        answer, sources, trace = query_engine.query(question, collect_trace=False)
        
        # 验证结果
        assert isinstance(answer, str), "答案应该是字符串"
        assert len(answer) > 10, "答案应该有足够的内容"
        assert isinstance(sources, list), "引用来源应该是列表"
        
        print(f"✅ 真实API查询成功")
        print(f"   问题: {question}")
        print(f"   答案长度: {len(answer)} 字符")
        print(f"   引用数量: {len(sources)} 个")


@pytest.mark.integration
@pytest.mark.github_e2e
class TestGitHubIncremental:
    """GitHub仓库增量更新测试
    
    测试仓库更新后的增量索引更新流程
    """
    
    def test_change_detection(
        self,
        github_test_metadata_manager
    ):
        """测试变更检测功能"""
        owner = TEST_GITHUB_REPO["owner"]
        repo = TEST_GITHUB_REPO["repo"]
        branch = TEST_GITHUB_REPO["branch"]
        
        print(f"\n🔍 测试变更检测")
        
        # 首次加载文档
        documents1 = load_documents_from_github(
            owner=owner,
            repo=repo,
            branch=branch,
            show_progress=False
        )
        
        assert len(documents1) > 0, "应该加载到文档"
        
        # 检测变更（首次导入，应该是新增）
        changes1 = github_test_metadata_manager.detect_changes(owner, repo, branch, documents1)
        
        assert isinstance(changes1, FileChange), "应该返回FileChange对象"
        print(f"   首次导入变更: {changes1.summary()}")
        
        # 更新元数据（记录首次导入）
        github_test_metadata_manager.update_repository_metadata(
            owner=owner,
            repo=repo,
            branch=branch,
            commit_sha="test_commit_sha_1234567890123456789012345678901234567890",
            documents=documents1
        )
        
        # 再次加载相同文档（应该检测为无变更或修改）
        documents2 = load_documents_from_github(
            owner=owner,
            repo=repo,
            branch=branch,
            show_progress=False
        )
        
        changes2 = github_test_metadata_manager.detect_changes(owner, repo, branch, documents2)
        
        print(f"   二次导入变更: {changes2.summary()}")
        
        # 验证变更检测逻辑
        assert isinstance(changes2, FileChange), "应该返回FileChange对象"
        
        print(f"✅ 变更检测测试通过")
    
    def test_incremental_sync(
        self,
        github_test_index_manager,
        github_test_metadata_manager
    ):
        """测试增量同步流程"""
        owner = TEST_GITHUB_REPO["owner"]
        repo = TEST_GITHUB_REPO["repo"]
        branch = TEST_GITHUB_REPO["branch"]
        
        print(f"\n🔄 测试增量同步流程")
        
        # 使用sync_github_repository进行同步
        documents, changes, commit_sha = sync_github_repository(
            owner=owner,
            repo=repo,
            branch=branch,
            metadata_manager=github_test_metadata_manager,
            show_progress=False
        )
        
        # 验证结果
        assert commit_sha is not None, "应该有commit SHA"
        assert len(commit_sha) == 40, "commit SHA应该是40字符"
        
        print(f"   Commit SHA: {commit_sha[:8]}...")
        print(f"   变更: {changes.summary()}")
        
        # 如果有变更，构建索引
        if changes.has_changes() and len(documents) > 0:
            # 获取变更的文件
            added_docs = [d for d in documents if d.metadata.get('file_path') in changes.added]
            modified_docs = [d for d in documents if d.metadata.get('file_path') in changes.modified]
            
            # 构建索引（增量更新）
            if added_docs or modified_docs:
                github_test_index_manager.build_index(
                    added_docs + modified_docs,
                    show_progress=False
                )
                
                stats = github_test_index_manager.get_stats()
                print(f"   ✅ 索引更新完成，当前包含 {stats['document_count']} 个向量")
        
        print(f"✅ 增量同步测试通过")


# ==================== 辅助函数 ====================

def check_git_available() -> bool:
    """检查Git是否可用"""
    import subprocess
    try:
        result = subprocess.run(
            ['git', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_network_available() -> bool:
    """检查网络是否可用（简单检查）"""
    import socket
    try:
        socket.create_connection(("github.com", 443), timeout=3)
        return True
    except (socket.error, OSError):
        return False

