"""
测试 frontend/utils/sources.py
对应源文件：frontend/utils/sources.py
"""

import pytest
from frontend.utils.sources import convert_sources_to_dict


class TestSources:
    """测试 convert_sources_to_dict 函数"""
    
    def test_empty_sources(self):
        """测试空来源列表"""
        result = convert_sources_to_dict([])
        assert result == []
    
    def test_dict_sources(self):
        """测试字典来源"""
        sources = [
            {"text": "test1", "score": 0.9, "metadata": {"file_name": "doc1.md"}},
            {"text": "test2", "score": 0.8, "metadata": {"file_name": "doc2.md"}},
        ]
        result = convert_sources_to_dict(sources)
        
        assert len(result) == 2
        assert result[0]['index'] == 1
        assert result[0]['text'] == "test1"
        assert result[0]['score'] == 0.9
        assert result[1]['index'] == 2
        assert result[1]['text'] == "test2"
        assert result[1]['score'] == 0.8
    
    def test_model_sources(self):
        """测试 SourceModel 对象"""
        # 创建一个简单的 Mock 对象，模拟 SourceModel
        class MockSourceModel:
            def __init__(self, text, score):
                self.text = text
                self.score = score
            
            def model_dump(self):
                return {"text": self.text, "score": self.score}
        
        source1 = MockSourceModel("test1", 0.9)
        source2 = MockSourceModel("test2", 0.8)
        
        result = convert_sources_to_dict([source1, source2])
        
        assert len(result) == 2
        assert result[0]['index'] == 1
        assert result[0]['text'] == "test1"
        assert result[0]['score'] == 0.9
        assert result[1]['index'] == 2
        assert result[1]['text'] == "test2"
        assert result[1]['score'] == 0.8
    
    def test_mixed_sources(self):
        """测试混合来源（字典和对象）"""
        class MockSourceModel:
            def __init__(self, text, score):
                self.text = text
                self.score = score
            
            def model_dump(self):
                return {"text": self.text, "score": self.score}
        
        sources = [
            {"text": "dict1", "score": 0.9},
            MockSourceModel("model1", 0.8),
            {"text": "dict2", "score": 0.7},
        ]
        
        result = convert_sources_to_dict(sources)
        
        assert len(result) == 3
        assert result[0]['index'] == 1
        assert result[0]['text'] == "dict1"
        assert result[1]['index'] == 2
        assert result[1]['text'] == "model1"
        assert result[2]['index'] == 3
        assert result[2]['text'] == "dict2"
    
    def test_sources_with_existing_index(self):
        """测试已包含 index 字段的来源"""
        sources = [
            {"text": "test1", "score": 0.9, "index": 10},
            {"text": "test2", "score": 0.8, "index": 20},
        ]
        
        result = convert_sources_to_dict(sources)
        
        # 应该覆盖原有的 index
        assert len(result) == 2
        assert result[0]['index'] == 1  # 从1开始
        assert result[1]['index'] == 2

