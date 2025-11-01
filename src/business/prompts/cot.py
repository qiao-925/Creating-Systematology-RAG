"""
CoT (Chain of Thought) 思维链提示模板

引导模型一步步推理，提高复杂问题的回答质量
"""

from typing import Dict, Any, List

from src.business.protocols import PromptModule, PipelineContext
from src.logger import setup_logger

logger = setup_logger('cot_template')


class CoTTemplate(PromptModule):
    """思维链提示模板
    
    引导模型进行逐步推理，适合复杂问题
    
    Examples:
        >>> cot = CoTTemplate()
        >>> context = PipelineContext(query="如何应用系统思维解决问题？")
        >>> context = cot.execute(context)
        >>> print(context.prompt)  # 包含"让我们一步步思考"的引导
    """
    
    def __init__(
        self,
        name: str = "cot_prompt",
        reasoning_style: str = "step_by_step",
        config: Dict[str, Any] = None
    ):
        """初始化CoT模板
        
        Args:
            name: 模块名称
            reasoning_style: 推理风格（step_by_step, analytical, etc.）
            config: 额外配置
        """
        super().__init__(name, config)
        self.reasoning_style = reasoning_style
        
        logger.info(f"CoTTemplate初始化: style={reasoning_style}")
    
    def build_prompt(self, query: str, documents: List[Any]) -> str:
        """构造CoT提示词
        
        Args:
            query: 用户查询
            documents: 参考文档
            
        Returns:
            str: 构造的提示词
        """
        # 提取文档文本
        context_text = "\n\n".join([
            doc.text if hasattr(doc, 'text') else str(doc) 
            for doc in documents
        ])
        
        # 根据推理风格选择模板
        if self.reasoning_style == "step_by_step":
            prompt = self._build_step_by_step_prompt(query, context_text)
        elif self.reasoning_style == "analytical":
            prompt = self._build_analytical_prompt(query, context_text)
        else:
            prompt = self._build_default_prompt(query, context_text)
        
        return prompt
    
    def _build_step_by_step_prompt(self, query: str, context: str) -> str:
        """构造分步推理提示"""
        return f"""你是一个擅长逐步推理的AI助手。请基于以下参考文档，通过分步思考来回答问题。

参考文档：
{context}

---

用户问题：{query}

---

请按照以下步骤思考并回答：

步骤1：理解问题的核心要点
步骤2：从参考文档中提取关键信息
步骤3：分析信息之间的逻辑关系
步骤4：综合推理并得出结论

让我们一步步思考：
"""
    
    def _build_analytical_prompt(self, query: str, context: str) -> str:
        """构造分析式推理提示"""
        return f"""请基于参考文档，通过深入分析来回答问题。

参考文档：
{context}

---

问题：{query}

---

分析框架：
1. 问题分解：将问题拆分为子问题
2. 信息提取：从文档中提取相关信息
3. 逻辑推理：分析因果关系和逻辑链条
4. 综合回答：整合分析结果

请进行深入分析并回答：
"""
    
    def _build_default_prompt(self, query: str, context: str) -> str:
        """构造默认CoT提示"""
        return f"""基于以下参考文档，请通过逐步推理来回答问题。

参考文档：
{context}

问题：{query}

让我们一步步思考：
1. 首先，理解问题的关键点
2. 然后，从文档中找到相关信息
3. 接着，进行逻辑推理
4. 最后，给出完整答案

请开始推理：
"""
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """执行CoT提示构造"""
        logger.info(f"构造CoT提示: query={context.query[:50]}...")
        
        try:
            # 确保有检索到的文档
            if not context.retrieved_docs:
                logger.warning("没有检索到文档，使用简化CoT提示")
                context.prompt = f"问题：{context.query}\n\n让我们一步步思考：\n"
                return context
            
            # 构造提示词
            prompt = self.build_prompt(context.query, context.retrieved_docs)
            context.prompt = prompt
            context.set_metadata('prompt_type', 'cot')
            context.set_metadata('reasoning_style', self.reasoning_style)
            
            logger.info(f"CoT提示构造完成: prompt_len={len(prompt)}")
            
        except Exception as e:
            logger.error(f"CoT提示构造失败: {e}")
            context.set_error(f"CoT提示构造失败: {str(e)}")
        
        return context


class ZeroShotCoTTemplate(CoTTemplate):
    """Zero-shot CoT模板
    
    只添加"让我们一步步思考"提示，不提供示例
    """
    
    def __init__(self, name: str = "zero_shot_cot"):
        super().__init__(name=name, reasoning_style="step_by_step")
    
    def build_prompt(self, query: str, documents: List[Any]) -> str:
        """构造Zero-shot CoT提示"""
        context_text = "\n\n".join([
            doc.text if hasattr(doc, 'text') else str(doc) 
            for doc in documents
        ])
        
        return f"""基于以下参考文档回答问题。

参考文档：
{context_text}

问题：{query}

让我们一步步思考：
"""


# 便捷函数

def create_cot_template(reasoning_style: str = "step_by_step") -> CoTTemplate:
    """创建CoT模板
    
    Args:
        reasoning_style: 推理风格
        
    Returns:
        CoTTemplate: CoT模板实例
    """
    return CoTTemplate(reasoning_style=reasoning_style)


def create_zero_shot_cot() -> ZeroShotCoTTemplate:
    """创建Zero-shot CoT模板
    
    Returns:
        ZeroShotCoTTemplate: Zero-shot CoT模板
    """
    return ZeroShotCoTTemplate()
