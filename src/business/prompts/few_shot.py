"""
Few-shot提示模板

通过提供示例来引导模型生成更好的答案
"""

from typing import List, Dict, Any
from dataclasses import dataclass

from src.business.protocols import PromptModule, PipelineContext
from src.logger import setup_logger

logger = setup_logger('few_shot_template')


@dataclass
class Example:
    """Few-shot示例"""
    question: str
    context: str
    answer: str
    
    def to_prompt(self) -> str:
        """转换为提示词格式"""
        return f"""示例：
问题：{self.question}
参考文档：{self.context}
答案：{self.answer}
"""


class FewShotTemplate(PromptModule):
    """Few-shot提示模板
    
    通过提供少量示例来引导模型更好地理解任务
    
    Examples:
        >>> examples = [
        ...     Example(question="什么是系统思维？", context="...", answer="..."),
        ...     Example(question="如何应用系统思维？", context="...", answer="..."),
        ... ]
        >>> few_shot = FewShotTemplate(examples=examples)
        >>> context = PipelineContext(query="系统思维的核心是什么？")
        >>> context = few_shot.execute(context)
        >>> print(context.prompt)
    """
    
    def __init__(
        self,
        examples: List[Example] = None,
        name: str = "few_shot_prompt",
        num_examples: int = 3,
        config: Dict[str, Any] = None
    ):
        """初始化Few-shot模板
        
        Args:
            examples: 示例列表
            name: 模块名称
            num_examples: 使用的示例数量
            config: 额外配置
        """
        super().__init__(name, config)
        self.examples = examples or self._get_default_examples()
        self.num_examples = num_examples
        
        logger.info(f"FewShotTemplate初始化: examples={len(self.examples)}, use={num_examples}")
    
    def _get_default_examples(self) -> List[Example]:
        """获取默认示例"""
        return [
            Example(
                question="什么是系统思维？",
                context="系统思维是一种从整体角度看待问题的思考方式，强调各部分之间的相互关系和相互作用。",
                answer="系统思维是一种从整体角度看待问题的思考方式。它不是孤立地看待事物，而是关注各部分之间的相互关系和相互作用，从而更好地理解复杂系统的行为。"
            ),
            Example(
                question="系统思维有什么特点？",
                context="系统思维的特点包括整体性、动态性、层次性和目的性。它强调整体大于部分之和。",
                answer="系统思维有四个主要特点：\n1. 整体性：关注整体而非局部\n2. 动态性：理解系统的变化过程\n3. 层次性：认识系统的多层次结构\n4. 目的性：明确系统的目标和功能\n\n核心理念是'整体大于部分之和'。"
            ),
        ]
    
    def build_prompt(self, query: str, documents: List[Any]) -> str:
        """构造Few-shot提示词
        
        Args:
            query: 用户查询
            documents: 参考文档
            
        Returns:
            str: 构造的提示词
        """
        # 选择示例
        selected_examples = self.examples[:self.num_examples]
        
        # 构建提示词
        prompt_parts = ["以下是一些示例，展示如何基于参考文档回答问题：\n"]
        
        # 添加示例
        for i, example in enumerate(selected_examples, 1):
            prompt_parts.append(f"\n=== 示例 {i} ===")
            prompt_parts.append(example.to_prompt())
        
        # 添加当前任务
        prompt_parts.append("\n\n=== 现在请回答以下问题 ===")
        prompt_parts.append(f"\n问题：{query}")
        
        # 添加参考文档
        context_text = "\n\n".join([doc.text if hasattr(doc, 'text') else str(doc) for doc in documents])
        prompt_parts.append(f"\n参考文档：{context_text}")
        
        prompt_parts.append("\n答案：")
        
        return "\n".join(prompt_parts)
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """执行Few-shot提示构造"""
        logger.info(f"构造Few-shot提示: query={context.query[:50]}...")
        
        try:
            # 确保有检索到的文档
            if not context.retrieved_docs:
                logger.warning("没有检索到文档，使用简化提示")
                context.prompt = f"问题：{context.query}\n\n答案："
                return context
            
            # 构造提示词
            prompt = self.build_prompt(context.query, context.retrieved_docs)
            context.prompt = prompt
            context.set_metadata('prompt_type', 'few_shot')
            context.set_metadata('num_examples', self.num_examples)
            
            logger.info(f"Few-shot提示构造完成: prompt_len={len(prompt)}")
            
        except Exception as e:
            logger.error(f"Few-shot提示构造失败: {e}")
            context.set_error(f"Few-shot提示构造失败: {str(e)}")
        
        return context
    
    def add_example(self, example: Example):
        """添加示例"""
        self.examples.append(example)
        logger.info(f"添加示例: total={len(self.examples)}")
    
    def clear_examples(self):
        """清空示例"""
        self.examples.clear()
        logger.info("清空所有示例")


# 便捷函数

def create_few_shot_template(
    examples: List[Example] = None,
    num_examples: int = 3
) -> FewShotTemplate:
    """创建Few-shot模板
    
    Args:
        examples: 示例列表
        num_examples: 使用的示例数量
        
    Returns:
        FewShotTemplate: Few-shot模板实例
    """
    return FewShotTemplate(examples=examples, num_examples=num_examples)
