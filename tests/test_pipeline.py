"""
Pipeline流水线集成测试
"""

import pytest
from unittest.mock import Mock, patch

from src.business.protocols import (
    PipelineModule,
    PipelineContext,
    ModuleType,
    RetrievalModule,
    GenerationModule,
)
from src.business.pipeline import PipelineExecutor, Pipeline, ExecutionResult


# === Mock模块 ===

class MockRetrievalModule(RetrievalModule):
    """Mock检索模块"""
    
    def retrieve(self, query: str, top_k: int = 5):
        return [f"doc_{i}" for i in range(top_k)]
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        context.retrieved_docs = self.retrieve(context.query, top_k=3)
        context.set_metadata('retrieval_done', True)
        return context


class MockGenerationModule(GenerationModule):
    """Mock生成模块"""
    
    def generate(self, prompt: str) -> str:
        return f"答案: {prompt}"
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        context.raw_answer = f"基于 {len(context.retrieved_docs)} 个文档的答案"
        context.formatted_answer = context.raw_answer
        context.set_metadata('generation_done', True)
        return context


class FailingModule(PipelineModule):
    """会失败的Mock模块"""
    
    def __init__(self):
        super().__init__("failing", ModuleType.CUSTOM)
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        raise Exception("故意失败")


# === 测试用例 ===

class TestPipelineContext:
    """测试PipelineContext"""
    
    def test_context_creation(self):
        """测试创建上下文"""
        context = PipelineContext(
            query="测试问题",
            user_id="user1",
            session_id="session1"
        )
        
        assert context.query == "测试问题"
        assert context.user_id == "user1"
        assert context.session_id == "session1"
        assert len(context.retrieved_docs) == 0
        assert len(context.errors) == 0
    
    def test_context_metadata(self):
        """测试元数据操作"""
        context = PipelineContext()
        
        context.set_metadata('key1', 'value1')
        assert context.get_metadata('key1') == 'value1'
        assert context.get_metadata('key2', 'default') == 'default'
    
    def test_context_errors(self):
        """测试错误处理"""
        context = PipelineContext()
        
        assert context.has_errors() is False
        
        context.set_error("错误1")
        context.set_error("错误2")
        
        assert context.has_errors() is True
        assert len(context.errors) == 2
    
    def test_context_warnings(self):
        """测试警告"""
        context = PipelineContext()
        
        context.set_warning("警告1")
        assert len(context.warnings) == 1


class TestPipeline:
    """测试Pipeline"""
    
    def test_pipeline_creation(self):
        """测试创建流水线"""
        pipeline = Pipeline(
            name="test",
            modules=[MockRetrievalModule(), MockGenerationModule()],
            description="测试流水线"
        )
        
        assert pipeline.name == "test"
        assert len(pipeline.modules) == 2
    
    def test_pipeline_add_remove_module(self):
        """测试添加和移除模块"""
        pipeline = Pipeline(name="test", modules=[])
        
        retrieval = MockRetrievalModule()
        generation = MockGenerationModule()
        
        pipeline.add_module(retrieval)
        pipeline.add_module(generation)
        assert len(pipeline) == 2
        
        pipeline.remove_module("retrieval")
        assert len(pipeline) == 1
    
    def test_pipeline_get_module(self):
        """测试获取模块"""
        retrieval = MockRetrievalModule()
        pipeline = Pipeline(name="test", modules=[retrieval])
        
        module = pipeline.get_module("retrieval")
        assert module is retrieval
        
        module = pipeline.get_module("nonexistent")
        assert module is None


class TestPipelineExecutor:
    """测试PipelineExecutor"""
    
    def test_executor_creation(self):
        """测试创建执行器"""
        executor = PipelineExecutor(
            enable_hooks=True,
            stop_on_error=False
        )
        
        assert executor.enable_hooks is True
        assert executor.stop_on_error is False
    
    def test_executor_simple_pipeline(self):
        """测试执行简单流水线"""
        # 创建流水线
        pipeline = Pipeline(
            name="simple_rag",
            modules=[MockRetrievalModule(), MockGenerationModule()]
        )
        
        # 创建执行器
        executor = PipelineExecutor()
        
        # 创建上下文
        context = PipelineContext(query="什么是系统思维？")
        
        # 执行
        result = executor.execute(pipeline, context)
        
        # 验证结果
        assert result.success is True
        assert len(result.modules_executed) == 2
        assert result.context.get_metadata('retrieval_done') is True
        assert result.context.get_metadata('generation_done') is True
        assert len(result.context.retrieved_docs) == 3
        assert result.context.formatted_answer is not None
    
    def test_executor_with_failing_module(self):
        """测试包含失败模块的流水线"""
        # 创建流水线（中间有失败模块）
        pipeline = Pipeline(
            name="failing_pipeline",
            modules=[
                MockRetrievalModule(),
                FailingModule(),
                MockGenerationModule(),
            ]
        )
        
        executor = PipelineExecutor(stop_on_error=False)
        context = PipelineContext(query="测试")
        
        result = executor.execute(pipeline, context)
        
        # 应该有错误但不停止
        assert result.success is False
        assert len(result.errors) > 0
        assert "故意失败" in result.errors[0]
    
    def test_executor_stop_on_error(self):
        """测试遇到错误停止"""
        pipeline = Pipeline(
            name="stop_on_error",
            modules=[
                MockRetrievalModule(),
                FailingModule(),
                MockGenerationModule(),
            ]
        )
        
        executor = PipelineExecutor(stop_on_error=True)
        context = PipelineContext(query="测试")
        
        result = executor.execute(pipeline, context)
        
        # 应该在失败模块处停止
        assert result.success is False
        assert len(result.modules_executed) < 3
    
    def test_executor_hooks(self):
        """测试事件钩子"""
        pipeline = Pipeline(name="test", modules=[MockRetrievalModule()])
        executor = PipelineExecutor(enable_hooks=True)
        
        # 记录钩子调用
        hook_calls = []
        
        def pre_pipeline_hook(p, c):
            hook_calls.append('pre_pipeline')
        
        def post_pipeline_hook(p, c):
            hook_calls.append('post_pipeline')
        
        def pre_module_hook(m, c):
            hook_calls.append(f'pre_module:{m.name}')
        
        def post_module_hook(m, c):
            hook_calls.append(f'post_module:{m.name}')
        
        # 注册钩子
        executor.add_pre_pipeline_hook(pre_pipeline_hook)
        executor.add_post_pipeline_hook(post_pipeline_hook)
        executor.add_pre_module_hook(pre_module_hook)
        executor.add_post_module_hook(post_module_hook)
        
        # 执行
        context = PipelineContext(query="测试")
        result = executor.execute(pipeline, context)
        
        # 验证钩子被调用
        assert 'pre_pipeline' in hook_calls
        assert 'post_pipeline' in hook_calls
        assert 'pre_module:retrieval' in hook_calls
        assert 'post_module:retrieval' in hook_calls
    
    def test_executor_max_execution_time(self):
        """测试超时控制"""
        import time
        
        class SlowModule(PipelineModule):
            def __init__(self):
                super().__init__("slow", ModuleType.CUSTOM)
            
            def execute(self, context):
                time.sleep(0.2)
                return context
        
        pipeline = Pipeline(name="slow", modules=[SlowModule()])
        executor = PipelineExecutor(max_execution_time=0.1)  # 100ms超时
        context = PipelineContext(query="测试")
        
        result = executor.execute(pipeline, context)
        
        # 应该超时
        assert result.success is False
        assert any("超时" in err for err in result.errors)


class TestModularzQueryEngine:
    """测试ModularQueryEngine"""
    
    @pytest.fixture
    def mock_index_manager(self):
        """Mock IndexManager"""
        with patch('src.business.modular_query_engine.IndexManager') as mock:
            yield mock
    
    @pytest.fixture
    def mock_query_engine(self):
        """Mock QueryEngine"""
        with patch('src.business.modular_query_engine.QueryEngine') as mock:
            yield mock
    
    def test_modular_query_engine_creation(self, mock_index_manager, mock_query_engine):
        """测试创建模块化查询引擎"""
        from src.business.modular_query_engine import ModularQueryEngine
        
        mock_im = Mock()
        engine = ModularQueryEngine(mock_im, enable_pipeline=True)
        
        assert engine.enable_pipeline is True
        assert engine.pipeline is not None
        assert engine.executor is not None
    
    def test_modular_query_engine_query(self, mock_index_manager, mock_query_engine):
        """测试查询"""
        from src.business.modular_query_engine import ModularQueryEngine
        
        mock_im = Mock()
        mock_qe_instance = mock_query_engine.return_value
        mock_qe_instance.query.return_value = ("测试答案", [{"file": "test.md"}])
        
        engine = ModularQueryEngine(mock_im, enable_pipeline=False)
        answer, sources = engine.query("什么是系统思维？")
        
        assert answer == "测试答案"
        assert len(sources) == 1


class TestExecutionResult:
    """测试ExecutionResult"""
    
    def test_execution_result_to_dict(self):
        """测试转换为字典"""
        context = PipelineContext()
        result = ExecutionResult(
            success=True,
            context=context,
            execution_time=1.23,
            modules_executed=["m1", "m2"],
            errors=[]
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['success'] is True
        assert result_dict['execution_time'] == 1.23
        assert len(result_dict['modules_executed']) == 2
        assert result_dict['has_errors'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
