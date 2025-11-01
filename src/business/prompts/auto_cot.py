"""
Auto-CoT 自动思维链模板

自动生成推理步骤，无需人工设计CoT示例
"""

from typing import Dict, Any, List

from src.business.protocols import PromptModule, PipelineContext
from src.logger import setup_logger

logger = setup_logger('auto_cot_template')


class AutoCoTTemplate(PromptModule):
    """自动思维链模板
    
    自动分析问题并生成推理步骤
    
    Examples:
        >>> auto_cot = AutoCoTTemplate()
        >>> context = PipelineContext(query="如何系统性地分析复杂问题？")
        >>> context = auto_cot.execute(context)
        >>> print(context.prompt)  # 自动生成推理框架
    """
    
    def __init__(
        self,
        name: str = "auto_cot_prompt",
        auto_generate_steps: bool = True,
        max_steps: int = 5,
        config: Dict[str, Any] = None
    ):
        """初始化Auto-CoT模板
        
        Args:
            name: 模块名称
            auto_generate_steps: 是否自动生成推理步骤
            max_steps: 最大推理步骤数
            config: 额外配置
        """
        super().__init__(name, config)
        self.auto_generate_steps = auto_generate_steps
        self.max_steps = max_steps
        
        logger.info(f"AutoCoTTemplate初始化: auto={auto_generate_steps}, max_steps={max_steps}")
    
    def _analyze_question_type(self, query: str) -> str:
        """分析问题类型
        
        Args:
            query: 用户查询
            
        Returns:
            str: 问题类型（定义型/解释型/分析型/应用型）
        """
        # 简化的问题类型判断
        if any(keyword in query for keyword in ["什么是", "如何定义", "定义"]):
            return "definition"
        elif any(keyword in query for keyword in ["为什么", "原因", "解释"]):
            return "explanation"
        elif any(keyword in query for keyword in ["分析", "比较", "区别"]):
            return "analysis"
        elif any(keyword in query for keyword in ["如何", "怎样", "方法"]):
            return "application"
        else:
            return "general"
    
    def _generate_reasoning_steps(self, query: str, question_type: str) -> List[str]:
        """根据问题类型生成推理步骤
        
        Args:
            query: 用户查询
            question_type: 问题类型
            
        Returns:
            List[str]: 推理步骤列表
        """
        if question_type == "definition":
            return [
                "识别需要定义的核心概念",
                "从文档中提取概念的关键特征",
                "整理概念的本质和外延",
                "给出清晰准确的定义"
            ]
        elif question_type == "explanation":
            return [
                "理解需要解释的现象或问题",
                "从文档中找到相关的因果关系",
                "分析内在机制和逻辑",
                "给出系统的解释"
            ]
        elif question_type == "analysis":
            return [
                "明确分析的对象和维度",
                "从文档中提取关键信息",
                "进行多角度对比和分析",
                "总结分析结论"
            ]
        elif question_type == "application":
            return [
                "理解要解决的实际问题",
                "从文档中提取可用的方法和原则",
                "将理论应用到具体场景",
                "给出实践建议"
            ]
        else:
            return [
                "理解问题的核心要求",
                "从文档中提取相关信息",
                "进行逻辑推理和综合",
                "给出完整答案"
            ]
    
    def build_prompt(self, query: str, documents: List[Any]) -> str:
        """构造Auto-CoT提示词
        
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
        
        # 分析问题类型
        question_type = self._analyze_question_type(query)
        
        # 生成推理步骤
        if self.auto_generate_steps:
            reasoning_steps = self._generate_reasoning_steps(query, question_type)
        else:
            reasoning_steps = ["逐步分析", "逻辑推理", "得出结论"]
        
        # 构造提示词
        prompt_parts = [
            "你是一个擅长系统思考和逻辑推理的AI助手。",
            "\n参考文档：",
            context_text,
            "\n---",
            f"\n问题：{query}",
            "\n---",
            "\n推理框架：",
        ]
        
        for i, step in enumerate(reasoning_steps[:self.max_steps], 1):
            prompt_parts.append(f"{i}. {step}")
        
        prompt_parts.append("\n请按照上述推理框架，逐步思考并回答：\n")
        
        return "\n".join(prompt_parts)
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """执行Auto-CoT提示构造"""
        logger.info(f"构造Auto-CoT提示: query={context.query[:50]}...")
        
        try:
            # 确保有检索到的文档
            if not context.retrieved_docs:
                logger.warning("没有检索到文档，使用简化Auto-CoT提示")
                context.prompt = f"问题：{context.query}\n\n请逐步推理并回答：\n"
                return context
            
            # 分析问题类型
            question_type = self._analyze_question_type(context.query)
            
            # 构造提示词
            prompt = self.build_prompt(context.query, context.retrieved_docs)
            context.prompt = prompt
            context.set_metadata('prompt_type', 'auto_cot')
            context.set_metadata('question_type', question_type)
            context.set_metadata('auto_generated', self.auto_generate_steps)
            
            logger.info(f"Auto-CoT提示构造完成: type={question_type}, prompt_len={len(prompt)}")
            
        except Exception as e:
            logger.error(f"Auto-CoT提示构造失败: {e}")
            context.set_error(f"Auto-CoT提示构造失败: {str(e)}")
        
        return context


# ToT (Tree of Thoughts) 思维树接口（预留）

class ToTTemplate(PromptModule):
    """思维树模板（预留接口）
    
    未来实现：探索多个推理路径，选择最优解
    
    TODO: 实现ToT算法
    - 生成多个推理分支
    - 评估各分支质量
    - 选择最优路径
    """
    
    def __init__(self, name: str = "tot_prompt"):
        super().__init__(name, {})
        logger.warning("ToTTemplate尚未实现，仅为预留接口")
    
    def build_prompt(self, query: str, documents: List[Any]) -> str:
        """TODO: 实现ToT提示构造"""
        raise NotImplementedError("ToT模板尚未实现")
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """TODO: 实现ToT执行逻辑"""
        context.set_warning("ToT模板尚未实现，降级到CoT")
        # 降级到CoT
        from .cot import CoTTemplate
        cot = CoTTemplate()
        return cot.execute(context)


# 便捷函数

def create_auto_cot(max_steps: int = 5) -> AutoCoTTemplate:
    """创建Auto-CoT模板
    
    Args:
        max_steps: 最大推理步骤数
        
    Returns:
        AutoCoTTemplate: Auto-CoT模板实例
    """
    return AutoCoTTemplate(max_steps=max_steps)
