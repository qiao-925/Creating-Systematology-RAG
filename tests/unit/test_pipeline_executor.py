"""
PipelineExecutor模块单元测试
测试流水线执行、钩子和错误处理
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Any

from src.business.pipeline.executor import (
    PipelineExecutor,
    Pipeline,
    ExecutionResult,
    create_simple_rag_pipeline,
    create_advanced_rag_pipeline,
)
from src.business.protocols import (
    PipelineModule,
    PipelineContext,
    ModuleType,
    RetrievalModule,
    GenerationModule,
    FormattingModule,
)


class MockRetrievalModule(RetrievalModule):
    """Mock检索模块"""
    
    def __init__(self, name: str = "mock_retrieval"):
        super().__init__(name)
        self.execute_called = False
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """执行检索"""
        self.execute_called = True
        context.retrieved_docs = [
            {"text": "doc1", "score": 0.9},
            {"text": "doc2", "score": 0.8},
        ]
        return context
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Any]:
        return [{"text": "doc1"}, {"text": "doc2"}]


class MockGenerationModule(GenerationModule):
    """Mock生成模块"""
    
    def __init__(self, name: str = "mock_generation"):
        super().__init__(name)
        self.execute_called = False
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """执行生成"""
        self.execute_called = True
        context.raw_answer = "这是生成的答案"
        return context
    
    def generate(self, prompt: str) -> str:
        return "这是生成的答案"


class MockFormattingModule(FormattingModule):
    """Mock格式化模块"""
    
    def __init__(self, name: str = "mock_formatting"):
        super().__init__(name)
        self.execute_called = False
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """执行格式化"""
        self.execute_called = True
        context.formatted_answer = f"格式化后的答案: {context.raw_answer}"
        return context
    
    def format(self, answer: str, sources: List[Any]) -> str:
        return f"格式化后的答案: {answer}"


class FailingModule(PipelineModule):
    """总是失败的模块（用于错误处理测试）"""
    
    def __init__(self, name: str = "failing_module"):
        super().__init__(name, ModuleType.CUSTOM)
        self.execute_called = False
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """总是抛出异常"""
        self.execute_called = True
        raise Exception("模块执行失败")


class TestPipelineExecutor:
    """PipelineExecutor测试"""
    
    def test_pipeline_executor_init(self):
        """测试PipelineExecutor初始化"""
        executor = PipelineExecutor(
            enable_hooks=True,
            stop_on_error=False,
            max_execution_time=30.0
        )
        
        assert executor.enable_hooks is True
        assert executor.stop_on_error is False
        assert executor.max_execution_time == 30.0
        assert executor.hook_manager is not None
        assert executor.executor_core is not None
    
    def test_pipeline_executor_init_defaults(self):
        """测试默认初始化参数"""
        executor = PipelineExecutor()
        
        assert executor.enable_hooks is True
        assert executor.stop_on_error is False
        assert executor.max_execution_time is None
    
    def test_pipeline_execution(self):
        """测试流水线执行"""
        executor = PipelineExecutor()
        
        retrieval_module = MockRetrievalModule()
        generation_module = MockGenerationModule()
        
        pipeline = Pipeline(
            name="test_pipeline",
            modules=[retrieval_module, generation_module]
        )
        
        context = PipelineContext(query="测试问题")
        
        result = executor.execute(pipeline, context)
        
        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert len(result.modules_executed) == 2
        assert "mock_retrieval" in result.modules_executed
        assert "mock_generation" in result.modules_executed
        assert retrieval_module.execute_called is True
        assert generation_module.execute_called is True
    
    def test_module_execution_order(self):
        """测试模块执行顺序"""
        executor = PipelineExecutor()
        
        execution_order = []
        
        class OrderedModule(PipelineModule):
            def __init__(self, name: str, order_list: list):
                super().__init__(name, ModuleType.CUSTOM)
                self.order_list = order_list
            
            def execute(self, context: PipelineContext) -> PipelineContext:
                self.order_list.append(self.name)
                return context
        
        order_list = []
        modules = [
            OrderedModule("module1", order_list),
            OrderedModule("module2", order_list),
            OrderedModule("module3", order_list),
        ]
        
        pipeline = Pipeline(name="order_test", modules=modules)
        context = PipelineContext(query="测试")
        
        executor.execute(pipeline, context)
        
        # 验证执行顺序
        assert order_list == ["module1", "module2", "module3"]
    
    def test_pipeline_hooks_pre_pipeline(self):
        """测试流水线执行前钩子"""
        executor = PipelineExecutor(enable_hooks=True)
        
        hook_called = []
        
        def pre_hook(pipeline, context):
            hook_called.append("pre_pipeline")
        
        executor.add_pre_pipeline_hook(pre_hook)
        
        pipeline = Pipeline(
            name="hook_test",
            modules=[MockRetrievalModule()]
        )
        context = PipelineContext(query="测试")
        
        executor.execute(pipeline, context)
        
        assert "pre_pipeline" in hook_called
    
    def test_pipeline_hooks_post_pipeline(self):
        """测试流水线执行后钩子"""
        executor = PipelineExecutor(enable_hooks=True)
        
        hook_called = []
        
        def post_hook(pipeline, context):
            hook_called.append("post_pipeline")
        
        executor.add_post_pipeline_hook(post_hook)
        
        pipeline = Pipeline(
            name="hook_test",
            modules=[MockRetrievalModule()]
        )
        context = PipelineContext(query="测试")
        
        executor.execute(pipeline, context)
        
        assert "post_pipeline" in hook_called
    
    def test_pipeline_hooks_pre_module(self):
        """测试模块执行前钩子"""
        executor = PipelineExecutor(enable_hooks=True)
        
        hook_calls = []
        
        def pre_module_hook(module, context):
            hook_calls.append(f"pre_{module.name}")
        
        executor.add_pre_module_hook(pre_module_hook)
        
        retrieval = MockRetrievalModule("retrieval")
        generation = MockGenerationModule("generation")
        
        pipeline = Pipeline(
            name="hook_test",
            modules=[retrieval, generation]
        )
        context = PipelineContext(query="测试")
        
        executor.execute(pipeline, context)
        
        assert "pre_retrieval" in hook_calls
        assert "pre_generation" in hook_calls
    
    def test_pipeline_hooks_post_module(self):
        """测试模块执行后钩子"""
        executor = PipelineExecutor(enable_hooks=True)
        
        hook_calls = []
        
        def post_module_hook(module, context):
            hook_calls.append(f"post_{module.name}")
        
        executor.add_post_module_hook(post_module_hook)
        
        retrieval = MockRetrievalModule("retrieval")
        
        pipeline = Pipeline(
            name="hook_test",
            modules=[retrieval]
        )
        context = PipelineContext(query="测试")
        
        executor.execute(pipeline, context)
        
        assert "post_retrieval" in hook_calls
    
    def test_pipeline_hooks_disabled(self):
        """测试禁用钩子"""
        executor = PipelineExecutor(enable_hooks=False)
        
        hook_called = []
        
        def hook(pipeline, context):
            hook_called.append("called")
        
        executor.add_pre_pipeline_hook(hook)
        
        pipeline = Pipeline(
            name="hook_test",
            modules=[MockRetrievalModule()]
        )
        context = PipelineContext(query="测试")
        
        executor.execute(pipeline, context)
        
        # 钩子不应该被调用
        assert "called" not in hook_called
    
    def test_pipeline_error_handling_continue(self):
        """测试错误处理（继续执行）"""
        executor = PipelineExecutor(stop_on_error=False)
        
        failing = FailingModule()
        retrieval = MockRetrievalModule()
        
        pipeline = Pipeline(
            name="error_test",
            modules=[failing, retrieval]
        )
        context = PipelineContext(query="测试")
        
        result = executor.execute(pipeline, context)
        
        # 应该继续执行，但标记为失败
        assert result.success is False
        assert len(result.errors) > 0
        assert "failing_module" in result.modules_executed or retrieval.execute_called
    
    def test_pipeline_error_handling_stop(self):
        """测试错误处理（停止执行）"""
        executor = PipelineExecutor(stop_on_error=True)
        
        failing = FailingModule()
        retrieval = MockRetrievalModule()
        
        pipeline = Pipeline(
            name="error_test",
            modules=[failing, retrieval]
        )
        context = PipelineContext(query="测试")
        
        result = executor.execute(pipeline, context)
        
        # 应该停止执行
        assert result.success is False
        assert len(result.errors) > 0
        # retrieval不应该被执行
        assert not retrieval.execute_called
    
    def test_pipeline_error_hooks(self):
        """测试错误钩子"""
        executor = PipelineExecutor(enable_hooks=True)
        
        error_hook_called = []
        
        def error_hook(module, context, error):
            error_hook_called.append(f"error_{module.name}")
        
        executor.add_error_hook(error_hook)
        
        failing = FailingModule("failing")
        
        pipeline = Pipeline(
            name="error_test",
            modules=[failing]
        )
        context = PipelineContext(query="测试")
        
        result = executor.execute(pipeline, context)
        
        assert "error_failing" in error_hook_called
        assert result.success is False
    
    def test_pipeline_context_propagation(self):
        """测试上下文传递"""
        executor = PipelineExecutor()
        
        class ContextCheckModule(PipelineModule):
            def __init__(self, name: str):
                super().__init__(name, ModuleType.CUSTOM)
                self.received_context = None
            
            def execute(self, context: PipelineContext) -> PipelineContext:
                self.received_context = context
                # 修改上下文
                context.set_metadata("test_key", "test_value")
                return context
        
        module1 = ContextCheckModule("module1")
        module2 = ContextCheckModule("module2")
        
        pipeline = Pipeline(
            name="context_test",
            modules=[module1, module2]
        )
        context = PipelineContext(query="测试问题")
        
        result = executor.execute(pipeline, context)
        
        # 验证上下文被传递
        assert module1.received_context is not None
        assert module2.received_context is not None
        assert module2.received_context.get_metadata("test_key") == "test_value"
    
    def test_pipeline_timeout(self):
        """测试执行超时"""
        import time
        
        class SlowModule(PipelineModule):
            def __init__(self, name: str, delay: float):
                super().__init__(name, ModuleType.CUSTOM)
                self.delay = delay
            
            def execute(self, context: PipelineContext) -> PipelineContext:
                time.sleep(self.delay)
                return context
        
        executor = PipelineExecutor(max_execution_time=0.1)
        
        slow_module = SlowModule("slow", delay=0.2)
        
        pipeline = Pipeline(
            name="timeout_test",
            modules=[slow_module]
        )
        context = PipelineContext(query="测试")
        
        result = executor.execute(pipeline, context)
        
        # 应该因为超时而失败或停止
        assert result.success is False or len(result.modules_executed) == 0
        assert len(result.errors) > 0 or context.has_errors()


class TestPipeline:
    """Pipeline类测试"""
    
    def test_pipeline_init(self):
        """测试Pipeline初始化"""
        pipeline = Pipeline(
            name="test",
            modules=[],
            description="测试流水线",
            version="1.0.0"
        )
        
        assert pipeline.name == "test"
        assert len(pipeline.modules) == 0
        assert pipeline.description == "测试流水线"
        assert pipeline.version == "1.0.0"
    
    def test_pipeline_add_remove_module(self):
        """测试添加和移除模块"""
        pipeline = Pipeline(name="test", modules=[])
        
        module1 = MockRetrievalModule("module1")
        module2 = MockGenerationModule("module2")
        
        pipeline.add_module(module1)
        pipeline.add_module(module2)
        
        assert len(pipeline.modules) == 2
        
        pipeline.remove_module("module1")
        
        assert len(pipeline.modules) == 1
        assert pipeline.modules[0].name == "module2"
    
    def test_pipeline_get_module(self):
        """测试获取模块"""
        module1 = MockRetrievalModule("module1")
        
        pipeline = Pipeline(
            name="test",
            modules=[module1]
        )
        
        retrieved = pipeline.get_module("module1")
        assert retrieved is module1
        
        not_found = pipeline.get_module("nonexistent")
        assert not_found is None


class TestPipelineHelpers:
    """Pipeline便捷函数测试"""
    
    def test_create_simple_rag_pipeline(self):
        """测试创建简单RAG流水线"""
        retrieval = MockRetrievalModule()
        generation = MockGenerationModule()
        formatting = MockFormattingModule()
        
        pipeline = create_simple_rag_pipeline(
            retrieval_module=retrieval,
            generation_module=generation,
            formatting_module=formatting,
            name="simple_test"
        )
        
        assert pipeline.name == "simple_test"
        assert len(pipeline.modules) == 3
        assert pipeline.modules[0] is retrieval
        assert pipeline.modules[1] is generation
        assert pipeline.modules[2] is formatting
    
    def test_create_simple_rag_pipeline_no_formatting(self):
        """测试创建简单RAG流水线（无格式化模块）"""
        retrieval = MockRetrievalModule()
        generation = MockGenerationModule()
        
        pipeline = create_simple_rag_pipeline(
            retrieval_module=retrieval,
            generation_module=generation
        )
        
        assert len(pipeline.modules) == 2
    
    def test_create_advanced_rag_pipeline(self):
        """测试创建高级RAG流水线"""
        retrieval = MockRetrievalModule()
        
        class MockRerankingModule(PipelineModule):
            def execute(self, context: PipelineContext) -> PipelineContext:
                context.reranked_docs = context.retrieved_docs
                return context
        
        class MockPromptModule(PipelineModule):
            def execute(self, context: PipelineContext) -> PipelineContext:
                context.prompt = "prompt"
                return context
        
        reranking = MockRerankingModule("reranking", ModuleType.RERANKING)
        prompt = MockPromptModule("prompt", ModuleType.PROMPT)
        generation = MockGenerationModule()
        formatting = MockFormattingModule()
        
        pipeline = create_advanced_rag_pipeline(
            retrieval_module=retrieval,
            reranking_module=reranking,
            prompt_module=prompt,
            generation_module=generation,
            formatting_module=formatting,
            name="advanced_test"
        )
        
        assert pipeline.name == "advanced_test"
        assert len(pipeline.modules) == 5


class TestPipelineContextPropagation:
    """流水线上下文传递测试"""
    
    def test_context_data_flow(self):
        """测试上下文数据流"""
        executor = PipelineExecutor()
        
        class DataFlowModule(PipelineModule):
            def __init__(self, name: str, set_key: str, read_key: str = None):
                super().__init__(name, ModuleType.CUSTOM)
                self.set_key = set_key
                self.read_key = read_key
            
            def execute(self, context: PipelineContext) -> PipelineContext:
                if self.read_key:
                    value = context.get_metadata(self.read_key, "not_found")
                    context.set_metadata(self.set_key, f"{value}_processed")
                else:
                    context.set_metadata(self.set_key, "initial_value")
                return context
        
        module1 = DataFlowModule("module1", "key1")
        module2 = DataFlowModule("module2", "key2", read_key="key1")
        
        pipeline = Pipeline(
            name="dataflow_test",
            modules=[module1, module2]
        )
        context = PipelineContext(query="测试")
        
        result = executor.execute(pipeline, context)
        
        assert result.success is True
        assert context.get_metadata("key1") == "initial_value"
        assert context.get_metadata("key2") == "initial_value_processed"

