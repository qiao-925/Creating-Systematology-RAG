"""
配置管理模块单元测试
"""

import pytest
from pathlib import Path
from backend.infrastructure.config import Config


def _build_config(
    *,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    vector_store_path: str | None = None,
    raw_data_path: str | None = None,
    processed_data_path: str | None = None,
) -> Config:
    """基于当前 YAML 配置构造 Config，并按需覆写模型值。"""
    config = Config()
    if chunk_size is not None:
        config._model.index.chunk_size = chunk_size
    if chunk_overlap is not None:
        config._model.index.chunk_overlap = chunk_overlap
    if vector_store_path is not None:
        config._model.paths.vector_store = vector_store_path
    if raw_data_path is not None:
        config._model.paths.raw_data = raw_data_path
    if processed_data_path is not None:
        config._model.paths.processed_data = processed_data_path
    return config


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
        config = _build_config(chunk_size=0)
        is_valid, error = config.validate()
        
        assert is_valid is False, "配置应该无效"
        assert "CHUNK_SIZE" in error or "大于0" in error
    
    def test_config_invalid_chunk_size_negative(self, monkeypatch):
        """测试CHUNK_SIZE为负数的情况"""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key")
        config = _build_config(chunk_size=-100)
        is_valid, error = config.validate()
        
        assert is_valid is False
    
    def test_config_invalid_chunk_overlap(self, monkeypatch):
        """测试CHUNK_OVERLAP大于等于CHUNK_SIZE的情况"""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key")
        config = _build_config(chunk_size=100, chunk_overlap=100)
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
        config = _build_config(vector_store_path="./test_store")
        
        # 相对路径应该被转换为绝对路径
        assert config.VECTOR_STORE_PATH.is_absolute()
        assert "test_store" in str(config.VECTOR_STORE_PATH)
    
    def test_ensure_directories(self, tmp_path, monkeypatch):
        """测试确保目录存在"""
        config = _build_config(
            vector_store_path=str(tmp_path / "vector"),
            raw_data_path=str(tmp_path / "raw"),
            processed_data_path=str(tmp_path / "processed"),
        )
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
        assert "PROJECT_ROOT" in repr_str
        assert "DEEPSEEK_API_KEY" not in repr_str
        assert "HF_TOKEN" not in repr_str


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
    config = _build_config(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    is_valid, _ = config.validate()
    
    assert is_valid == should_valid, \
        f"CHUNK_SIZE={chunk_size}, CHUNK_OVERLAP={chunk_overlap} 应该{'有效' if should_valid else '无效'}"
