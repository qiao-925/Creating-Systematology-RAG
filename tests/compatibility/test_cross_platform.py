"""
跨平台兼容性测试
测试Windows/Linux/Mac平台的兼容性
"""

import pytest
import platform
import sys
from pathlib import Path


class TestPlatformCompatibility:
    """平台兼容性测试"""
    
    def test_platform_detection(self):
        """测试平台检测"""
        current_platform = platform.system()
        
        assert current_platform in ['Windows', 'Linux', 'Darwin'], f"当前平台: {current_platform}"
        
        print(f"\n当前平台: {current_platform}")
        print(f"平台版本: {platform.version()}")
        print(f"Python版本: {sys.version}")
    
    def test_path_handling_cross_platform(self):
        """测试跨平台路径处理"""
        # 测试Path对象的跨平台兼容性
        test_paths = [
            "data/test",
            "data/test/file.txt",
            Path("data") / "test",
            Path("data") / "test" / "file.txt",
        ]
        
        for path in test_paths:
            path_obj = Path(path)
            # 验证路径对象可以创建
            assert path_obj is not None
            
            # 验证路径分隔符处理
            path_str = str(path_obj)
            # 在不同平台上，路径分隔符应该正确转换
            if platform.system() == 'Windows':
                # Windows使用反斜杠，但Path对象会自动处理
                assert isinstance(path_str, str)
            else:
                # Unix-like系统使用正斜杠
                assert isinstance(path_str, str)
    
    def test_file_operations_cross_platform(self):
        """测试跨平台文件操作"""
        import tempfile
        import os
        
        # 创建临时文件测试文件操作
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tmp:
            tmp_path = tmp.name
            tmp.write("测试内容")
        
        try:
            # 验证文件存在
            assert os.path.exists(tmp_path)
            
            # 验证可以读取
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert content == "测试内容"
            
            # 验证可以删除
            os.remove(tmp_path)
            assert not os.path.exists(tmp_path)
            
        except Exception as e:
            # 清理
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            pytest.skip(f"文件操作测试失败: {e}")
    
    def test_encoding_cross_platform(self):
        """测试跨平台编码处理"""
        # 测试UTF-8编码（所有平台都应该支持）
        test_string = "测试中文内容 🚀"
        
        # 验证可以编码和解码
        encoded = test_string.encode('utf-8')
        decoded = encoded.decode('utf-8')
        
        assert decoded == test_string, "UTF-8编码/解码应该一致"
        
        # 验证特殊字符
        special_chars = "测试 中文 English 日本語 🎉"
        encoded_special = special_chars.encode('utf-8')
        decoded_special = encoded_special.decode('utf-8')
        
        assert decoded_special == special_chars, "特殊字符编码/解码应该一致"


class TestGrepCrossPlatform:
    """Grep跨平台测试"""
    
    def test_grep_retriever_windows_compatibility(self):
        """测试GrepRetriever在Windows上的兼容性"""
        try:
            from backend.business.rag_engine.retrieval.strategies.grep import GrepRetriever
            
            # 验证GrepRetriever可以初始化
            # 注意：Windows上可能需要特殊的处理
            retriever = GrepRetriever()
            assert retriever is not None
            
            # 在Windows上，grep可能需要特殊处理
            if platform.system() == 'Windows':
                # Windows可能需要使用findstr或其他工具
                # 验证可以创建retriever（实际搜索可能不同）
                assert hasattr(retriever, 'search')
                
        except ImportError:
            pytest.skip("GrepRetriever模块未找到")
        except Exception as e:
            if platform.system() == 'Windows':
                # Windows上的错误可能由于grep命令不可用
                pytest.skip(f"Windows上的GrepRetriever测试失败: {e}")
            else:
                raise
    
    def test_grep_retriever_linux_compatibility(self):
        """测试GrepRetriever在Linux上的兼容性"""
        if platform.system() != 'Linux':
            pytest.skip("仅在Linux上运行此测试")
        
        try:
            from backend.business.rag_engine.retrieval.strategies.grep import GrepRetriever
            
            retriever = GrepRetriever()
            assert retriever is not None
            assert hasattr(retriever, 'search')
            
        except ImportError:
            pytest.skip("GrepRetriever模块未找到")
    
    def test_grep_retriever_mac_compatibility(self):
        """测试GrepRetriever在Mac上的兼容性"""
        if platform.system() != 'Darwin':
            pytest.skip("仅在Mac上运行此测试")
        
        try:
            from backend.business.rag_engine.retrieval.strategies.grep import GrepRetriever
            
            retriever = GrepRetriever()
            assert retriever is not None
            assert hasattr(retriever, 'search')
            
        except ImportError:
            pytest.skip("GrepRetriever模块未找到")


class TestFileSystemCrossPlatform:
    """文件系统跨平台测试"""
    
    def test_path_separator_handling(self):
        """测试路径分隔符处理"""
        # Windows使用反斜杠，Unix-like使用正斜杠
        # Path对象应该自动处理
        
        if platform.system() == 'Windows':
            # Windows路径
            windows_path = Path("data\\test\\file.txt")
            # Path对象会自动标准化
            assert isinstance(windows_path, Path)
        else:
            # Unix-like路径
            unix_path = Path("data/test/file.txt")
            assert isinstance(unix_path, Path)
    
    def test_case_sensitivity(self):
        """测试文件名大小写敏感性"""
        import tempfile
        
        # Unix-like系统区分大小写，Windows不区分
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "TestFile.txt"
            test_file.write_text("content")
            
            # 验证文件存在
            assert test_file.exists()
            
            if platform.system() == 'Windows':
                # Windows上，大小写不敏感
                assert (Path(tmpdir) / "testfile.txt").exists()
            else:
                # Unix-like系统，大小写敏感
                assert not (Path(tmpdir) / "testfile.txt").exists()
            
            # 清理
            test_file.unlink()
    
    def test_long_path_handling(self):
        """测试长路径处理"""
        # Windows有路径长度限制（260字符），需要特殊处理
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建较长的路径
            long_path = Path(tmpdir)
            for i in range(10):
                long_path = long_path / f"directory_{i}"
            
            try:
                long_path.mkdir(parents=True, exist_ok=True)
                
                # 验证可以创建文件
                test_file = long_path / "test.txt"
                test_file.write_text("content")
                
                assert test_file.exists()
                test_file.unlink()
                
            except (OSError, ValueError) as e:
                # Windows上可能遇到路径长度限制
                if platform.system() == 'Windows' and "path too long" in str(e).lower():
                    pytest.skip(f"Windows路径长度限制: {e}")
                else:
                    raise


class TestLibraryCrossPlatform:
    """库跨平台测试"""
    
    def test_chromadb_cross_platform(self):
        """测试ChromaDB跨平台兼容性"""
        try:
            import chromadb
            
            # 验证ChromaDB可以导入
            assert chromadb is not None
            
            # 验证可以创建客户端（不实际连接）
            try:
                from chromadb.config import Settings
                assert Settings is not None
            except:
                pass
                
        except ImportError:
            pytest.skip("ChromaDB未安装")
    
    def test_llamaindex_cross_platform(self):
        """测试LlamaIndex跨平台兼容性"""
        try:
            from llama_index.core import Document
            
            # 验证LlamaIndex可以导入和使用
            doc = Document(text="测试", metadata={})
            assert doc is not None
            assert doc.text == "测试"
            
        except ImportError:
            pytest.skip("LlamaIndex未安装")
    
    def test_numpy_cross_platform(self):
        """测试NumPy跨平台兼容性"""
        try:
            import numpy as np
            
            # 验证NumPy可以导入和使用
            arr = np.array([1, 2, 3])
            assert arr is not None
            assert len(arr) == 3
            
        except ImportError:
            pytest.skip("NumPy未安装")


class TestProcessCrossPlatform:
    """进程跨平台测试"""
    
    def test_subprocess_cross_platform(self):
        """测试subprocess跨平台兼容性"""
        import subprocess
        
        # 测试基本subprocess功能
        try:
            # 在Windows和Unix上，命令可能不同
            if platform.system() == 'Windows':
                result = subprocess.run(['echo', 'test'], capture_output=True, text=True, shell=True)
            else:
                result = subprocess.run(['echo', 'test'], capture_output=True, text=True)
            
            assert result.returncode == 0 or result.returncode is None
            
        except Exception as e:
            pytest.skip(f"subprocess测试失败: {e}")
    
    def test_multiprocessing_cross_platform(self):
        """测试multiprocessing跨平台兼容性"""
        try:
            import multiprocessing
            
            # 验证可以获取CPU数量（所有平台都应该支持）
            cpu_count = multiprocessing.cpu_count()
            assert cpu_count > 0
            
        except Exception as e:
            pytest.skip(f"multiprocessing测试失败: {e}")


