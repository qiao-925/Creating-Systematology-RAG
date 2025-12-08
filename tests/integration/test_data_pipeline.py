"""
数据处理流程集成测试
测试从加载到索引的完整流程
"""

import pytest
from pathlib import Path
from src.infrastructure.data_loader import load_documents_from_directory, load_documents_from_github
from src.infrastructure.indexer import IndexManager


@pytest.mark.integration
class TestDataPipeline:
    """数据处理流程集成测试"""
    
    def test_load_and_index_pipeline(self, sample_markdown_dir, temp_vector_store):
        """测试从加载到索引的完整流程"""
        # 步骤1：加载文档
        print("\n步骤1：加载文档")
        documents = load_documents_from_directory(sample_markdown_dir, recursive=True)
        
        assert len(documents) == 3, "应该加载3个文档"
        assert all(hasattr(doc, 'text') for doc in documents)
        assert all(hasattr(doc, 'metadata') for doc in documents)
        
        # 步骤2：构建索引
        print("步骤2：构建索引")
        index_manager = IndexManager(
            collection_name="pipeline_test",
            persist_dir=temp_vector_store
        )
        index = index_manager.build_index(documents, show_progress=False)
        
        assert index is not None
        
        # 步骤3：验证索引
        print("步骤3：验证索引")
        stats = index_manager.get_stats()
        assert stats['document_count'] > 0
        
        # 步骤4：测试检索
        print("步骤4：测试检索")
        results = index_manager.search("系统科学", top_k=3)
        
        assert len(results) > 0
        assert any("系统" in r['text'] for r in results)
    
    def test_incremental_loading(self, sample_markdown_dir, temp_vector_store):
        """测试增量加载和索引"""
        # 第一批文档
        docs1 = load_documents_from_directory(sample_markdown_dir, recursive=False)
        
        index_manager = IndexManager(
            collection_name="incremental_test",
            persist_dir=temp_vector_store
        )
        index_manager.build_index(docs1, show_progress=False)
        
        count1 = index_manager.get_stats()['document_count']
        
        # 添加更多文档
        subdir = sample_markdown_dir / "subdir"
        if subdir.exists():
            docs2 = load_documents_from_directory(subdir, recursive=False)
            index_manager.build_index(docs2, show_progress=False)
            
            count2 = index_manager.get_stats()['document_count']
            assert count2 > count1, "文档数量应该增加"
    
    def test_rebuild_index(self, sample_markdown_dir, temp_vector_store):
        """测试重建索引"""
        documents = load_documents_from_directory(sample_markdown_dir)
        
        index_manager = IndexManager(
            collection_name="rebuild_test",
            persist_dir=temp_vector_store
        )
        
        # 第一次构建
        index_manager.build_index(documents, show_progress=False)
        count1 = index_manager.get_stats()['document_count']
        
        # 清空并重建
        index_manager.clear_index()
        index_manager.build_index(documents, show_progress=False)
        count2 = index_manager.get_stats()['document_count']
        
        # 文档数量应该相同
        assert count1 == count2
    
    def test_github_to_index_pipeline(self, mocker, temp_vector_store):
        """测试 GitHub → Indexer 完整流程（Mock）"""
        # Mock GitHub 数据源
        from llama_index.core import Document
        
        mock_docs = [
            Document(
                text="# GitHub Repository\nThis is from a GitHub repo.",
                metadata={"file_path": "README.md", "source_type": "github", "repository": "test/test-repo"}
            ),
            Document(
                text="# Documentation\nSome docs from GitHub.",
                metadata={"file_path": "docs/guide.md", "source_type": "github", "repository": "test/test-repo"}
            )
        ]
        
        # Mock DataImportService 的 import_from_github 方法
        from unittest.mock import MagicMock
        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.documents = mock_docs
        mock_service.import_from_github.return_value = mock_result
        
        mocker.patch('src.infrastructure.data_loader.service.DataImportService', return_value=mock_service)
        
        # 步骤1：从 GitHub 加载文档
        print("\n步骤1：从 GitHub 加载文档")
        documents = load_documents_from_github(
            owner="test", 
            repo="test-repo", 
            branch="main"
        )
        
        assert len(documents) == 2, "应该加载2个文档"
        assert all(doc.metadata.get('source_type') == 'github' for doc in documents)
        assert all(doc.metadata.get('repository') == 'test/test-repo' for doc in documents)
        
        # 步骤2：构建索引
        print("步骤2：构建索引")
        index_manager = IndexManager(
            collection_name="github_test",
            persist_dir=temp_vector_store
        )
        index = index_manager.build_index(documents, show_progress=False)
        
        assert index is not None
        
        # 步骤3：验证索引
        print("步骤3：验证索引")
        stats = index_manager.get_stats()
        assert stats['document_count'] > 0
        
        # 步骤4：测试检索
        print("步骤4：测试检索")
        results = index_manager.search("GitHub", top_k=2)
        
        assert len(results) > 0
        assert any("GitHub" in r['text'] for r in results)


@pytest.mark.integration
class TestDataValidation:
    """数据验证集成测试"""
    
    def test_document_metadata_consistency(self, sample_markdown_dir):
        """测试文档元数据一致性"""
        documents = load_documents_from_directory(sample_markdown_dir)
        
        for doc in documents:
            # 所有文档都应该有基本元数据
            assert 'file_name' in doc.metadata
            assert 'file_path' in doc.metadata
            assert 'source_type' in doc.metadata
            
            # source_type应该是markdown
            assert doc.metadata['source_type'] == 'markdown'
    
    def test_text_cleaning_pipeline(self, tmp_path):
        """测试文本清理流程"""
        test_dir = tmp_path / "clean_test"
        test_dir.mkdir()
        
        # 创建包含各种格式问题的文档
        dirty_content = """# 标题

这是    多余空格的内容。


多余的空行。

  
  前后空白  
"""
        (test_dir / "dirty.md").write_text(dirty_content, encoding='utf-8')
        
        # 加载并清理
        documents = load_documents_from_directory(test_dir, clean=True)
        
        assert len(documents) == 1
        text = documents[0].text
        
        # 验证清理效果
        assert "    " not in text or text.count("    ") <= 1  # 允许代码块中的空格
        assert "\n\n\n" not in text

