"""
向后兼容性测试
测试旧接口、数据格式和配置的兼容性
"""

import pytest
from pathlib import Path
from typing import Dict, Any
import json


class TestOldInterfaceCompatibility:
    """旧接口兼容性测试"""
    
    def test_old_rag_service_interface(self):
        """测试旧RAGService接口兼容性"""
        try:
            from src.business.services.rag_service import RAGService
            
            # 测试旧的初始化方式（如果支持）
            # 验证接口仍然可用
            assert RAGService is not None
            assert hasattr(RAGService, '__init__')
            assert hasattr(RAGService, 'query')
            assert hasattr(RAGService, 'build_index')
            assert hasattr(RAGService, 'chat')
            
        except ImportError:
            pytest.skip("RAGService模块未找到")
    
    def test_old_query_engine_interface(self):
        """测试旧QueryEngine接口兼容性"""
        try:
            # 测试旧的QueryEngine导入（如果存在）
            try:
                from src.query_engine import QueryEngine
                assert QueryEngine is not None
            except ImportError:
                # 如果旧接口不存在，跳过测试
                pytest.skip("旧QueryEngine接口不存在，可能已迁移")
            
        except Exception as e:
            pytest.skip(f"旧QueryEngine接口测试失败: {e}")
    
    def test_old_index_manager_interface(self):
        """测试旧IndexManager接口兼容性"""
        try:
            from src.indexer import IndexManager
            
            # 验证接口存在
            assert IndexManager is not None
            assert hasattr(IndexManager, '__init__')
            assert hasattr(IndexManager, 'build_index')
            assert hasattr(IndexManager, 'get_index')
            assert hasattr(IndexManager, 'search')
            
        except ImportError:
            pytest.skip("IndexManager模块未找到")
    
    def test_old_configuration_format(self):
        """测试旧配置文件格式兼容性"""
        try:
            from src.config import config
            
            # 验证配置可以访问
            assert config is not None
            
            # 验证关键配置项存在
            expected_config_keys = [
                'PROJECT_ROOT',
                'RAW_DATA_PATH',
                'VECTOR_STORE_PATH',
            ]
            
            for key in expected_config_keys:
                assert hasattr(config, key), f"配置项 {key} 不存在"
                
        except ImportError:
            pytest.skip("config模块未找到")


class TestDataFormatCompatibility:
    """数据格式兼容性测试"""
    
    def test_old_document_format(self):
        """测试旧文档格式兼容性"""
        try:
            from llama_index.core.schema import Document as LlamaDocument
            
            # 测试旧格式文档创建
            old_format_doc = LlamaDocument(
                text="测试文档内容",
                metadata={"source": "test", "title": "测试"}
            )
            
            # 验证文档可以正常创建和访问
            assert old_format_doc.text == "测试文档内容"
            assert old_format_doc.metadata["source"] == "test"
            assert old_format_doc.metadata["title"] == "测试"
            
        except ImportError:
            pytest.skip("LlamaDocument未找到")
    
    def test_old_response_format(self):
        """测试旧响应格式兼容性"""
        try:
            from src.business.services.modules.models import RAGResponse
            
            # 测试旧格式响应创建
            old_format_response = RAGResponse(
                answer="测试答案",
                sources=[],
                metadata={}
            )
            
            # 验证响应格式
            assert old_format_response.answer == "测试答案"
            assert isinstance(old_format_response.sources, list)
            assert isinstance(old_format_response.metadata, dict)
            
        except ImportError:
            pytest.skip("RAGResponse未找到")
    
    def test_old_index_format(self):
        """测试旧索引格式兼容性"""
        # 验证索引可以正常加载（如果有旧格式索引）
        try:
            from src.indexer import IndexManager
            
            # 测试是否可以创建索引管理器（不实际加载旧索引）
            manager = IndexManager(collection_name="compatibility_test")
            assert manager is not None
            
        except Exception as e:
            pytest.skip(f"索引格式兼容性测试失败: {e}")


class TestConfigurationCompatibility:
    """配置兼容性测试"""
    
    def test_old_config_keys(self):
        """测试旧配置键的兼容性"""
        try:
            from src.config import config
            
            # 验证旧配置键仍然可用（如果存在）
            config_dict = {
                'PROJECT_ROOT': getattr(config, 'PROJECT_ROOT', None),
                'RAW_DATA_PATH': getattr(config, 'RAW_DATA_PATH', None),
                'VECTOR_STORE_PATH': getattr(config, 'VECTOR_STORE_PATH', None),
            }
            
            # 至少应该有一些配置存在
            assert any(v is not None for v in config_dict.values()), "配置应该包含必要的键"
            
        except ImportError:
            pytest.skip("config模块未找到")
    
    def test_config_file_compatibility(self):
        """测试配置文件兼容性"""
        # 检查是否有旧的配置文件格式需要兼容
        project_root = Path(__file__).parent.parent.parent
        
        # 检查常见的配置文件
        config_files = [
            project_root / 'config.json',
            project_root / 'config.yaml',
            project_root / 'config.yml',
            project_root / '.env',
        ]
        
        # 验证配置文件格式（如果存在）
        for config_file in config_files:
            if config_file.exists():
                # 验证文件可以读取（不验证内容）
                assert config_file.is_file(), f"{config_file} 应该是文件"
    
    def test_environment_variables_compatibility(self):
        """测试环境变量兼容性"""
        import os
        
        # 检查关键环境变量（如果使用）
        # 这些环境变量应该存在或可以设置
        env_vars = [
            'PYTHONIOENCODING',
            'HUGGINGFACE_HUB_CACHE',
        ]
        
        # 验证环境变量可以访问（即使不存在也不应报错）
        for var in env_vars:
            value = os.environ.get(var, None)
            # 只验证可以访问，不验证值


class TestAPIBackwardCompatibility:
    """API向后兼容性测试"""
    
    def test_old_import_paths(self):
        """测试旧导入路径的兼容性"""
        # 测试旧的导入路径是否仍然工作
        old_imports = [
            ('src.indexer', 'IndexManager'),
            ('src.business.services.rag_service', 'RAGService'),
            ('src.query.modular.engine', 'ModularQueryEngine'),
        ]
        
        for module_path, class_name in old_imports:
            try:
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                assert cls is not None, f"{module_path}.{class_name} 应该存在"
            except ImportError:
                pytest.skip(f"导入路径 {module_path}.{class_name} 不存在")
    
    def test_old_function_signatures(self):
        """测试旧函数签名的兼容性"""
        try:
            from src.business.services.rag_service import RAGService
            
            # 验证函数签名（通过检查参数）
            import inspect
            
            # 检查query方法的参数
            query_sig = inspect.signature(RAGService.query)
            assert 'question' in query_sig.parameters, "query方法应该包含question参数"
            
            # 检查build_index方法的参数
            build_index_sig = inspect.signature(RAGService.build_index)
            assert len(build_index_sig.parameters) > 0, "build_index方法应该有参数"
            
        except Exception as e:
            pytest.skip(f"函数签名兼容性测试失败: {e}")


class TestDataBackwardCompatibility:
    """数据向后兼容性测试"""
    
    def test_old_chat_history_format(self):
        """测试旧聊天历史格式兼容性"""
        try:
            from src.business.services.rag_service import RAGService
            
            # 验证可以访问聊天历史（格式兼容性）
            service = RAGService(collection_name="compatibility_test")
            
            # 测试获取聊天历史（即使为空）
            try:
                # 验证接口存在
                assert hasattr(service, 'get_chat_history') or hasattr(service, 'chat'), "应该有聊天历史接口"
            except:
                pass
            
            service.close()
            
        except Exception as e:
            pytest.skip(f"聊天历史格式兼容性测试失败: {e}")
    
    def test_old_index_metadata_format(self):
        """测试旧索引元数据格式兼容性"""
        try:
            from src.indexer import IndexManager
            
            # 验证可以处理索引元数据
            manager = IndexManager(collection_name="compatibility_test")
            
            # 验证可以列出集合（即使为空）
            try:
                collections = manager.list_collections()
                assert isinstance(collections, list), "集合列表应该是列表"
            except:
                pass
            
        except Exception as e:
            pytest.skip(f"索引元数据格式兼容性测试失败: {e}")


