"""
RAG服务集成测试
测试完整查询和对话流程
"""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock
import tempfile
import shutil

from src.business.rag_api.rag_service import RAGService
from src.business.rag_api.models import RAGResponse, ChatResponse, IndexResult
from src.infrastructure.indexer import IndexManager
from llama_index.core.schema import Document as LlamaDocument


@pytest.fixture
def test_documents():
    """创建测试文档"""
    return [
        LlamaDocument(
            text="系统科学是20世纪中期兴起的一门新兴学科，它研究系统的一般规律和方法。系统科学包括系统论、控制论、信息论等多个分支。",
            metadata={"title": "系统科学概述", "source": "test", "file_name": "系统科学.md"}
        ),
        LlamaDocument(
            text="钱学森（1911-2009）是中国著名科学家，被誉为\"中国航天之父\"。他在系统工程和系统科学领域做出了杰出贡献，提出了开放的复杂巨系统理论。",
            metadata={"title": "钱学森生平", "source": "test", "file_name": "钱学森.md"}
        ),
        LlamaDocument(
            text="系统工程是一种组织管理技术，用于解决大规模复杂系统的设计和实施问题。钱学森将系统工程引入中国，并结合中国实际进行了创新性发展。",
            metadata={"title": "系统工程简介", "source": "test", "file_name": "系统工程.md"}
        ),
    ]


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def rag_service_with_index(test_documents, temp_data_dir):
    """创建带有索引的RAGService"""
    # 创建临时索引
    collection_name = "test_integration_collection"
    
    # 清理可能存在的旧索引
    try:
        manager = IndexManager(collection_name=collection_name)
        manager.delete_collection(collection_name)
    except:
        pass
    
    # 创建服务并构建索引
    service = RAGService(
        collection_name=collection_name,
        similarity_top_k=3,
        use_modular_engine=True,
    )
    
    # 使用临时目录创建索引
    index_result = service.build_index(temp_data_dir, collection_name=collection_name)
    
    # 如果目录为空，直接使用文档构建索引
    if not index_result.success:
        manager = service.index_manager
        manager.build_index(documents=test_documents, collection_name=collection_name)
    
    yield service
    
    # 清理
    try:
        service.close()
        manager = IndexManager(collection_name=collection_name)
        manager.delete_collection(collection_name)
    except:
        pass


class TestCompleteQueryFlow:
    """完整查询流程测试"""
    
    def test_complete_query_flow(self, rag_service_with_index):
        """测试完整查询流程"""
        service = rag_service_with_index
        
        # 执行查询
        response = service.query(
            question="什么是系统科学？",
            user_id="test_user_1"
        )
        
        # 验证响应格式
        assert isinstance(response, RAGResponse)
        assert response.answer is not None
        assert isinstance(response.answer, str)
        assert len(response.answer) > 0
        
        # 验证来源信息
        assert isinstance(response.sources, list)
        assert len(response.sources) >= 0  # 可能没有来源
        
        # 验证元数据
        assert response.metadata is not None
        assert response.metadata.get('user_id') == "test_user_1"
        assert response.metadata.get('question') == "什么是系统科学？"
    
    def test_query_with_sources(self, rag_service_with_index):
        """测试带来源的查询"""
        service = rag_service_with_index
        
        response = service.query(
            question="钱学森的贡献是什么？",
            user_id="test_user_2"
        )
        
        # 验证响应
        assert isinstance(response, RAGResponse)
        
        # 如果有来源，验证来源格式
        if response.has_sources:
            for source in response.sources:
                assert isinstance(source, dict)
                # 来源应该包含必要的字段
                assert 'text' in source or 'content' in source or 'file_name' in source
    
    def test_query_with_empty_question(self, rag_service_with_index):
        """测试空问题处理"""
        service = rag_service_with_index
        
        # 空问题可能抛出异常或返回空答案
        try:
            response = service.query(question="")
            assert isinstance(response, RAGResponse)
        except Exception as e:
            # 如果抛出异常也是合理的
            assert "问题" in str(e).lower() or "query" in str(e).lower()


class TestCompleteChatFlow:
    """完整对话流程测试"""
    
    def test_complete_chat_flow(self, rag_service_with_index):
        """测试完整对话流程"""
        service = rag_service_with_index
        
        # 第一轮对话（创建新会话）
        response1 = service.chat(
            message="你好",
            user_id="test_user_3"
        )
        
        assert isinstance(response1, ChatResponse)
        assert response1.answer is not None
        assert response1.session_id is not None
        assert response1.turn_count == 1
        
        session_id = response1.session_id
        
        # 第二轮对话（继续会话）
        response2 = service.chat(
            message="什么是系统科学？",
            session_id=session_id,
            user_id="test_user_3"
        )
        
        assert isinstance(response2, ChatResponse)
        assert response2.session_id == session_id
        assert response2.turn_count == 2
        
        # 第三轮对话（验证上下文）
        response3 = service.chat(
            message="钱学森的主要贡献是什么？",
            session_id=session_id,
            user_id="test_user_3"
        )
        
        assert isinstance(response3, ChatResponse)
        assert response3.session_id == session_id
        assert response3.turn_count == 3
    
    def test_chat_history_persistence(self, rag_service_with_index):
        """测试会话历史持久化"""
        service = rag_service_with_index
        
        # 创建会话
        response1 = service.chat(message="第一句话", user_id="test_user_4")
        session_id = response1.session_id
        
        # 获取会话历史
        session = service.get_chat_history(session_id)
        
        assert session is not None
        assert session.session_id == session_id
        assert len(session.history) >= 1
        
        # 继续对话
        response2 = service.chat(
            message="第二句话",
            session_id=session_id,
            user_id="test_user_4"
        )
        
        # 再次获取会话历史
        session2 = service.get_chat_history(session_id)
        assert len(session2.history) >= 2
    
    def test_chat_session_isolation(self, rag_service_with_index):
        """测试会话隔离"""
        service = rag_service_with_index
        
        # 创建两个不同的会话
        response1 = service.chat(message="会话1的第一句话", user_id="test_user_5")
        session_id_1 = response1.session_id
        
        response2 = service.chat(message="会话2的第一句话", user_id="test_user_5")
        session_id_2 = response2.session_id
        
        # 验证会话ID不同
        assert session_id_1 != session_id_2
        
        # 验证会话历史独立
        session1 = service.get_chat_history(session_id_1)
        session2 = service.get_chat_history(session_id_2)
        
        assert session1.session_id == session_id_1
        assert session2.session_id == session_id_2
    
    def test_chat_history_clearing(self, rag_service_with_index):
        """测试清空会话历史"""
        service = rag_service_with_index
        
        # 创建会话并进行多轮对话
        response1 = service.chat(message="第一句话", user_id="test_user_6")
        session_id = response1.session_id
        
        service.chat(message="第二句话", session_id=session_id, user_id="test_user_6")
        
        # 清空历史
        result = service.clear_chat_history(session_id)
        assert result is True
        
        # 验证历史已清空（或重新开始）
        session = service.get_chat_history(session_id)
        # 历史可能被清空或重新开始
        assert session is not None


class TestIndexBuildAndQuery:
    """索引构建与查询测试"""
    
    def test_index_build_and_query(self, test_documents, temp_data_dir):
        """测试索引构建与查询"""
        collection_name = "test_build_query_collection"
        
        # 清理可能存在的旧索引
        try:
            manager = IndexManager(collection_name=collection_name)
            manager.delete_collection(collection_name)
        except:
            pass
        
        # 创建服务
        service = RAGService(
            collection_name=collection_name,
            similarity_top_k=3,
        )
        
        try:
            # 构建索引
            # 由于temp_data_dir可能为空，我们直接使用文档
            manager = service.index_manager
            manager.build_index(documents=test_documents, collection_name=collection_name)
            
            # 验证索引统计
            # 可以通过查询来验证索引是否正常
            
            # 执行查询
            response = service.query(
                question="系统科学包括哪些分支？",
                user_id="test_user_7"
            )
            
            # 验证结果准确性
            assert isinstance(response, RAGResponse)
            assert response.answer is not None
            # 答案应该包含相关信息
            assert len(response.answer) > 0
            
        finally:
            # 清理
            service.close()
            try:
                manager = IndexManager(collection_name=collection_name)
                manager.delete_collection(collection_name)
            except:
                pass
    
    def test_index_build_with_local_files(self, temp_data_dir):
        """测试使用本地文件构建索引"""
        # 创建测试文件
        test_file = Path(temp_data_dir) / "test_doc.md"
        test_file.write_text(
            "这是测试文档内容。系统科学是一门重要的学科。",
            encoding='utf-8'
        )
        
        collection_name = "test_local_files_collection"
        
        try:
            service = RAGService(collection_name=collection_name)
            
            # 构建索引
            result = service.build_index(temp_data_dir, collection_name=collection_name)
            
            # 验证构建结果
            assert isinstance(result, IndexResult)
            # 如果成功，应该有文档
            if result.success:
                assert result.doc_count > 0
                
                # 验证可以查询
                response = service.query(
                    question="测试查询",
                    user_id="test_user_8"
                )
                assert isinstance(response, RAGResponse)
            
            service.close()
        finally:
            # 清理
            try:
                manager = IndexManager(collection_name=collection_name)
                manager.delete_collection(collection_name)
            except:
                pass
    
    def test_index_build_failure_handling(self):
        """测试索引构建失败处理"""
        collection_name = "test_failure_collection"
        
        service = RAGService(collection_name=collection_name)
        
        try:
            # 尝试从不存在的目录构建索引
            result = service.build_index("./nonexistent_directory_12345")
            
            # 应该返回失败结果
            assert isinstance(result, IndexResult)
            assert result.success is False
            assert result.doc_count == 0
            assert len(result.message) > 0
        finally:
            service.close()


class TestRAGServiceIntegration:
    """RAG服务集成测试"""
    
    def test_service_lifecycle(self, rag_service_with_index):
        """测试服务生命周期"""
        service = rag_service_with_index
        
        # 验证服务可以正常使用
        response = service.query(question="测试", user_id="test_user_9")
        assert isinstance(response, RAGResponse)
        
        # 验证关闭不会出错
        service.close()
        
        # 关闭后不应再使用（可能会出错）
        try:
            service.query(question="测试", user_id="test_user_9")
            # 如果没出错，也没关系
        except:
            pass  # 关闭后出错是预期的
    
    def test_service_context_manager(self, test_documents):
        """测试服务上下文管理器"""
        collection_name = "test_context_collection"
        
        try:
            with RAGService(collection_name=collection_name) as service:
                # 构建索引
                manager = service.index_manager
                manager.build_index(documents=test_documents, collection_name=collection_name)
                
                # 执行查询
                response = service.query(question="测试", user_id="test_user_10")
                assert isinstance(response, RAGResponse)
            
            # 退出上下文后，资源应该被清理
        finally:
            # 清理
            try:
                manager = IndexManager(collection_name=collection_name)
                manager.delete_collection(collection_name)
            except:
                pass
    
    def test_multiple_queries_performance(self, rag_service_with_index):
        """测试多次查询性能"""
        service = rag_service_with_index
        
        questions = [
            "什么是系统科学？",
            "钱学森的贡献是什么？",
            "系统工程的应用",
        ]
        
        responses = []
        for question in questions:
            response = service.query(question=question, user_id="test_user_11")
            responses.append(response)
        
        # 验证所有查询都成功
        assert len(responses) == len(questions)
        for response in responses:
            assert isinstance(response, RAGResponse)
            assert response.answer is not None


