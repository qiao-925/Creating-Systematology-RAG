"""
Pipeline执行器 - 步骤执行模块
步骤执行逻辑
"""

from typing import Dict, Any

from src.logger import setup_logger

logger = setup_logger('pipeline_executor')


class StepExecutor:
    """步骤执行器"""
    
    def execute_step(
        self,
        step_name: str,
        context,
        **kwargs
    ) -> Any:
        """执行单个步骤
        
        Args:
            step_name: 步骤名称
            context: 执行上下文
            **kwargs: 其他参数
            
        Returns:
            步骤执行结果
        """
        if step_name == "parse":
            return self._execute_parse(context, **kwargs)
        elif step_name == "chunk":
            return self._execute_chunk(context, **kwargs)
        elif step_name == "embed":
            return self._execute_embed(context, **kwargs)
        elif step_name == "index":
            return self._execute_index(context, **kwargs)
        else:
            raise ValueError(f"未知步骤: {step_name}")
    
    def _execute_parse(self, context, **kwargs):
        """执行解析步骤"""
        documents = context.get_input('documents')
        # 解析逻辑
        return documents
    
    def _execute_chunk(self, context, **kwargs):
        """执行分块步骤"""
        from llama_index.core.node_parser import SentenceSplitter
        
        documents = context.get_step_result('parse') or context.get_input('documents')
        chunk_size = kwargs.get('chunk_size', 512)
        
        parser = SentenceSplitter(chunk_size=chunk_size)
        nodes = parser.get_nodes_from_documents(documents)
        
        return nodes
    
    def _execute_embed(self, context, **kwargs):
        """执行嵌入步骤"""
        nodes = context.get_step_result('chunk')
        # 嵌入逻辑（通常由索引管理器处理）
        return nodes
    
    def _execute_index(self, context, **kwargs):
        """执行索引步骤"""
        nodes = context.get_step_result('embed') or context.get_step_result('chunk')
        index_manager = kwargs.get('index_manager')
        
        if index_manager:
            index_manager.add_documents(nodes)
        
        return {"indexed_count": len(nodes)}

