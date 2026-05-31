"""
配置管理模块单元测试
"""

import pytest
from pathlib import Path
from backend.infrastructure.config import Config


class TestConfig:
    """配置管理测试类"""
    
    def test_config_initialization(self):
        """测试配置初始化"""
        config = Config()
        
        # 验证基本属性
        assert config.PROJECT_ROOT.exists(), "项目根目录应该存在"
        assert config.PROJECT_ROOT.is_dir(), "项目根目录应该是目录"
        
        # 验证数值类型
        assert isinstance(config.CHUNK_SIZE, int), "CHUNK_SIZE应该是整数"
        assert isinstance(config.CHUNK_OVERLAP, int), "CHUNK_OVERLAP应该是整数"
        assert isinstance(config.SIMILARITY_TOP_K, int), "SIMILARITY_TOP_K应该是整数"
    
    def test_config_default_values(self):
        """测试默认配置值"""
        config = Config()
        
        # 测试默认值
        assert config.CHUNK_SIZE > 0, "CHUNK_SIZE应该大于0"
        assert config.CHUNK_OVERLAP >= 0, "CHUNK_OVERLAP应该大于等于0"
        assert config.CHUNK_OVERLAP < config.CHUNK_SIZE, \
            "CHUNK_OVERLAP应该小于CHUNK_SIZE"
    
    def test_config_validation_success(self, monkeypatch):
        """测试配置验证成功的情况"""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "valid_test_key")
        monkeypatch.setenv("CHUNK_SIZE", "512")
        monkeypatch.setenv("CHUNK_OVERLAP", "50")
        
        config = Config()
        is_valid, error = config.validate()
        
        assert is_valid is True, "配置应该有效"
        assert error is None, "不应该有错误消息"
    
    def test_config_validation_missing_api_key(self, monkeypatch):
        """测试缺少API密钥的情况"""
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        
        config = Config()
        is_valid, error = config.validate()
        
        assert is_valid is True, "配置应该仍然有效（API Key 延迟校验）"
        assert error is None
    
    def test_config_invalid_chunk_size_zero(self, monkeypatch):
        """测试CHUNK_SIZE为0的情况"""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key")
        monkeypatch.setenv("CHUNK_SIZE", "0")
        
        config = Config()
        is_valid, error = config.validate()
        
        assert is_valid is False, "配置应该无效"
        assert "CHUNK_SIZE" in error or "大于0" in error
    
    def test_config_invalid_chunk_size_negative(self, monkeypatch):
        """测试CHUNK_SIZE为负数的情况"""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key")
        monkeypatch.setenv("CHUNK_SIZE", "-100")
        
        config = Config()
        is_valid, error = config.validate()
        
        assert is_valid is False
    
    def test_config_invalid_chunk_overlap(self, monkeypatch):
        """测试CHUNK_OVERLAP大于等于CHUNK_SIZE的情况"""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key")
        monkeypatch.setenv("CHUNK_SIZE", "100")
        monkeypatch.setenv("CHUNK_OVERLAP", "100")
        
        config = Config()
        is_valid, error = config.validate()
        
        assert is_valid is False
        assert "CHUNK_OVERLAP" in error
    
    def test_path_resolution_absolute(self):
        """测试绝对路径解析"""
        config = Config()
        
        # 所有路径应该是绝对路径
        assert config.VECTOR_STORE_PATH.is_absolute(), \
            "向量存储路径应该是绝对路径"
        assert config.RAW_DATA_PATH.is_absolute(), \
            "原始数据路径应该是绝对路径"
        assert config.PROCESSED_DATA_PATH.is_absolute(), \
            "处理后数据路径应该是绝对路径"
    
    def test_path_resolution_relative(self, monkeypatch):
        """测试相对路径自动转换"""
        monkeypatch.setenv("VECTOR_STORE_PATH", "./test_store")
        
        config = Config()
        
        # 相对路径应该被转换为绝对路径
        assert config.VECTOR_STORE_PATH.is_absolute()
        assert "test_store" in str(config.VECTOR_STORE_PATH)
    
    def test_ensure_directories(self, tmp_path, monkeypatch):
        """测试确保目录存在"""
        # 使用临时目录
        monkeypatch.setenv("VECTOR_STORE_PATH", str(tmp_path / "vector"))
        monkeypatch.setenv("RAW_DATA_PATH", str(tmp_path / "raw"))
        monkeypatch.setenv("PROCESSED_DATA_PATH", str(tmp_path / "processed"))
        
        config = Config()
        config.ensure_directories()
        
        # 验证目录已创建
        assert config.VECTOR_STORE_PATH.exists()
        assert config.RAW_DATA_PATH.exists()
        assert config.PROCESSED_DATA_PATH.exists()
    
    def test_config_repr(self):
        """测试配置的字符串表示"""
        config = Config()
        repr_str = repr(config)
        
        # 验证关键信息在字符串表示中
        assert "Config" in repr_str
        assert "CHUNK_SIZE" in repr_str
        assert "EMBEDDING_MODEL" in repr_str
        # API密钥不应该出现（安全考虑）


@pytest.mark.parametrize("chunk_size,chunk_overlap,should_valid", [
    (512, 50, True),
    (1024, 100, True),
    (256, 20, True),
    (100, 99, True),
    (100, 100, False),  # overlap等于size
    (100, 101, False),  # overlap大于size
    (0, 0, False),      # size为0
    (-1, 0, False),     # size为负数
])
def test_config_validation_combinations(chunk_size, chunk_overlap, should_valid, monkeypatch):
    """参数化测试：配置验证的各种组合"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key")
    monkeypatch.setenv("CHUNK_SIZE", str(chunk_size))
    monkeypatch.setenv("CHUNK_OVERLAP", str(chunk_overlap))
    
    config = Config()
    is_valid, _ = config.validate()
    
    assert is_valid == should_valid, \
        f"CHUNK_SIZE={chunk_size}, CHUNK_OVERLAP={chunk_overlap} 应该{'有效' if should_valid else '无效'}"

