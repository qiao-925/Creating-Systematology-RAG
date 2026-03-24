"""
RAG引擎查询处理模块 - 查询处理器：统一处理意图理解和查询改写

主要功能：
- QueryProcessor类：查询处理器，统一处理意图理解和改写（一次LLM调用）
- process()：处理查询，返回意图理解和改写结果

执行流程：
1. 评估查询复杂度（简单/中等/复杂）
2. 简单查询跳过LLM，直接返回
3. 复杂查询使用LLM进行意图理解和改写
4. 返回处理结果

特性：
- 分层决策（简单查询不走LLM）
- 一次LLM调用完成意图理解和改写
- 缓存机制（LRU）
- 完整的错误处理和降级
- 模板文件化：支持从文件加载模板，方便修改
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger
from backend.infrastructure.llms import create_deepseek_llm_for_structure

logger = get_logger('rag_engine.processing.query_processor')


class QueryProcessor:
    """查询处理器 - 统一处理意图理解和改写（一次LLM调用）"""
    
    # 默认模板（作为后备，如果文件不存在时使用）
    DEFAULT_TEMPLATE = """你是一个RAG系统查询处理专家，负责同时完成查询意图理解和查询改写。

【任务1：意图理解】
分析查询的意图和特征，提取：
- 查询类型（factual/comparative/explanatory/exploratory/specific）
- 查询复杂度（simple/medium/complex）
- 关键实体和概念
- 查询意图（一句话描述）

查询类型说明：
- factual: 事实查询（具体数据、定义、事实）
- comparative: 对比查询（比较、差异、异同）
- explanatory: 解释性查询（如何、为什么、原理）
- exploratory: 探索性查询（概述、介绍、总结）
- specific: 特定查询（精确匹配、文件名）

【任务2：查询改写】
将查询改写为更适合检索的形式：
- 补充领域关键词（如：系统科学、钱学森、系统工程、RAG、向量检索等）
- 扩展同义表达和概念
- 明确问题意图和焦点
- 保留核心查询意图，不要改变原意
- 移除口语化表达和冗余词汇

【原始查询】
{query}

【输出格式】
请以JSON格式返回：
{{
  "understanding": {{
    "query_type": "查询类型",
    "complexity": "复杂度",
    "entities": ["实体1", "实体2"],
    "intent": "查询意图描述",
    "confidence": 0.0-1.0
  }},
  "rewritten_queries": [
    "改写后的查询1",
    "改写后的查询2（如果需要多个角度）"
  ]
}}

只返回JSON，不要其他说明。改写后的查询数量：简单查询1个，复杂查询1-3个。
"""
    
    def __init__(
        self, 
        llm=None, 
        domain_keywords: Optional[List[str]] = None,
        template_path: Optional[str] = None
    ):
        """初始化查询处理器
        
        Args:
            llm: LLM实例（可选，默认使用DeepSeek）
            domain_keywords: 领域关键词列表（可选）
            template_path: 模板文件路径（可选，默认使用 query_rewrite_template.txt）
        """
        self._llm = llm
        self._llm_initialized = False
        self.domain_keywords = domain_keywords or []
        
        # 加载模板
        self.template = self._load_template(template_path)
        
        # 缓存（LRU，最多100个）
        self._cache = {}
        self._cache_size = 100
        
        template_source = "file" if template_path or self._template_file_exists() else "default"
        logger.info("查询处理器初始化完成", template_source=template_source)
    
    def _get_default_template_path(self) -> Path:
        """获取默认模板文件路径"""
        # 新路径：prompts/query/rewrite.txt（集中管理）
        new_path = config.PROJECT_ROOT / "prompts" / "query" / "rewrite.txt"
        if new_path.exists():
            return new_path
        # 向后兼容：旧路径
        return config.PROJECT_ROOT / "query_rewrite_template.txt"
    
    def _template_file_exists(self) -> bool:
        """检查默认模板文件是否存在"""
        return self._get_default_template_path().exists()
    
    def _load_template(self, template_path: Optional[str] = None) -> str:
        """加载模板（优先从文件，否则使用默认模板）
        
        Args:
            template_path: 模板文件路径（可选）
            
        Returns:
            模板内容字符串
        """
        # 确定模板文件路径
        if template_path:
            template_file = Path(template_path)
            if not template_file.is_absolute():
                template_file = config.PROJECT_ROOT / template_file
        else:
            template_file = self._get_default_template_path()
        
        # 尝试从文件加载
        if template_file.exists():
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_content = f.read().strip()
                
                logger.info(
                    "成功加载查询改写模板文件",
                    template_path=str(template_file)
                )
                return template_content
            
            except Exception as e:
                logger.warning(
                    "加载模板文件失败，使用默认模板",
                    template_path=str(template_file),
                    error=str(e)
                )
        else:
            logger.debug(
                "模板文件不存在，使用默认模板",
                template_path=str(template_file)
            )
        
        # 使用默认模板
        return self.DEFAULT_TEMPLATE
    
    def _initialize_llm(self):
        """初始化LLM（延迟加载）"""
        if self._llm_initialized:
            return
        
        if self._llm is None:
            try:
                # 使用工厂函数创建 LLM（结构化场景，JSON Output）
                self._llm = create_deepseek_llm_for_structure(
                    api_key=config.DEEPSEEK_API_KEY,
                    model=config.LLM_MODEL,
                    max_tokens=1024,
                )
                logger.info("查询处理器LLM已初始化（结构化场景，JSON Output）")
            except Exception as e:
                logger.error("查询处理器LLM初始化失败", error=str(e))
                raise
        
        self._llm_initialized = True
    
    def _assess_complexity_simple(self, query: str) -> str:
        """快速评估查询复杂度（规则判断，用于分层决策）
        
        Returns:
            "simple" | "medium" | "complex"
        """
        query_lower = query.lower()
        medium_indicators = [
            "介绍", "概述", "总结", "背景", "历史", "发展", "发展历程",
        ]
        
        # 简单查询的特征
        simple_indicators = [
            len(query) < 30,  # 短查询
            query.count(' ') < 4,  # 词数少
            any(kw in query_lower for kw in ['文件', '文档', 'pdf', '.md', '.py']),  # 明确关键词
            not any(kw in query_lower for kw in ['为什么', '如何', '解释', '比较', '差异']),  # 无复杂意图词
        ]
        
        # 复杂查询的特征
        complex_indicators = [
            len(query) > 100,  # 长查询
            query.count('?') > 1,  # 多个问题
            any(kw in query_lower for kw in ['为什么', '如何', '解释', '比较', '差异', '异同']),  # 复杂意图词
            '和' in query or '或' in query or '与' in query,  # 复合查询
            query.count('，') > 2 or query.count(',') > 2,  # 多个分句
        ]
        
        if any(complex_indicators):
            return "complex"
        elif any(keyword in query_lower for keyword in medium_indicators):
            return "medium"
        elif any(simple_indicators):
            return "simple"
        else:
            return "medium"

    def _render_prompt(self, query: str, domain_context: str) -> str:
        """渲染提示词模板。

        文件模板里可能直接包含 JSON 示例的花括号，这里在保留 `{query}` 占位符的同时
        兼容未转义的 JSON 块，避免 `str.format()` 将示例 JSON 误识别为占位符。
        """
        try:
            prompt = self.template.format(query=query)
        except KeyError:
            escaped_template = (
                self.template
                .replace("{", "{{")
                .replace("}", "}}")
                .replace("{{query}}", "{query}")
            )
            prompt = escaped_template.format(query=query)
        return prompt + domain_context
    
    def process(
        self, 
        query: str,
        use_cache: bool = True,
        force_llm: bool = False
    ) -> Dict[str, Any]:
        """处理查询：意图理解 + 改写（一次LLM调用）
        
        Args:
            query: 原始查询
            use_cache: 是否使用缓存
            force_llm: 是否强制使用LLM（忽略分层决策）
            
        Returns:
            处理结果字典，包含：
            - original_query: 原始查询
            - understanding: 意图理解结果（如果使用LLM）
            - rewritten_queries: 改写后的查询列表
            - final_query: 最终使用的查询（改写后的第一个或原始）
            - processing_method: 处理方式（"simple" / "llm"）
        """
        # 检查缓存
        if use_cache and query in self._cache:
            logger.debug("使用缓存的处理结果", query=query[:50] if len(query) > 50 else query)
            cached_result = self._cache[query].copy()
            cached_result["from_cache"] = True
            return cached_result
        
        # 初始化结果
        result = {
            "original_query": query,
            "understanding": None,
            "rewritten_queries": [query],
            "final_query": query,
            "processing_method": "simple",
            "from_cache": False,
        }
        
        # 分层决策：简单查询不走LLM
        if not force_llm:
            complexity = self._assess_complexity_simple(query)
            
            if complexity == "simple":
                # 简单查询：直接返回，不走LLM
                logger.info(
                    f"📝 查询处理: "
                    f"查询={query[:50]}..., "
                    f"方式=简单查询（跳过LLM）, "
                    f"复杂度={complexity}"
                )
                result["processing_method"] = "simple"
                result["complexity"] = complexity
                self._update_cache(query, result)
                return result
        
        # 复杂/中等查询：使用LLM处理
        try:
            self._initialize_llm()
            
            # 构建提示词（如果有关键词，添加到提示词中）
            domain_context = ""
            if self.domain_keywords:
                domain_context = f"\n领域关键词：{', '.join(self.domain_keywords)}"
            
            # 使用加载的模板（支持从文件加载）
            prompt = self._render_prompt(query=query, domain_context=domain_context)
            
            # 调用LLM
            response = self._llm.complete(prompt)
            response_text = response.text.strip()
            
            # 解析JSON响应
            try:
                # 尝试提取JSON（可能包含markdown代码块）
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                parsed_result = json.loads(response_text)
                
                # 提取结果
                understanding = parsed_result.get("understanding", {})
                rewritten_queries = parsed_result.get("rewritten_queries", [query])
                
                # 验证改写结果
                if not rewritten_queries or not isinstance(rewritten_queries, list):
                    rewritten_queries = [query]
                
                # 确保至少有一个查询
                if not rewritten_queries:
                    rewritten_queries = [query]
                
                # 最多保留3个
                rewritten_queries = rewritten_queries[:3]
                
                # 更新结果
                result["understanding"] = understanding
                result["rewritten_queries"] = rewritten_queries
                result["final_query"] = rewritten_queries[0]
                result["processing_method"] = "llm"
                result["complexity"] = understanding.get("complexity", "medium")
                
                logger.info(
                    f"📝 查询处理: "
                    f"原始='{query[:50]}...', "
                    f"最终='{result['final_query'][:50]}...', "
                    f"类型={understanding.get('query_type')}, "
                    f"复杂度={understanding.get('complexity')}, "
                    f"改写数量={len(rewritten_queries)}"
                )
                
            except json.JSONDecodeError as e:
                logger.error(
                    "解析LLM响应JSON失败",
                    error=str(e),
                    response_preview=response_text[:200] if len(response_text) > 200 else response_text
                )
                # 降级：使用原始查询
                result["processing_method"] = "llm_failed"
                result["final_query"] = query
                
        except Exception as e:
            logger.error("查询处理失败", error=str(e), exc_info=True)
            # 降级：使用原始查询
            result["processing_method"] = "llm_failed"
            result["final_query"] = query
        
        # 更新缓存
        self._update_cache(query, result)
        
        return result
    
    def _update_cache(self, query: str, result: Dict[str, Any]):
        """更新缓存（LRU策略）"""
        if len(self._cache) >= self._cache_size:
            # 移除最旧的（FIFO）
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        # 创建缓存副本（移除from_cache标记）
        cache_result = result.copy()
        cache_result.pop("from_cache", None)
        self._cache[query] = cache_result
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("查询处理器缓存已清空")
    
    def reload_template(self, template_path: Optional[str] = None) -> None:
        """重新加载模板（用于运行时更新）
        
        Args:
            template_path: 模板文件路径（可选，默认使用默认路径）
        """
        old_template = self.template
        self.template = self._load_template(template_path)
        
        if old_template != self.template:
            logger.info("查询改写模板已重新加载")
            # 清空缓存，因为模板已更改
            self.clear_cache()
        else:
            logger.debug("模板未变化，无需重新加载")


# 全局查询处理器实例（延迟初始化）
_global_query_processor: Optional[QueryProcessor] = None


def get_query_processor() -> QueryProcessor:
    """获取全局查询处理器实例"""
    global _global_query_processor
    if _global_query_processor is None:
        _global_query_processor = QueryProcessor()
    return _global_query_processor


def reset_query_processor() -> None:
    """重置全局查询处理器（用于测试）"""
    global _global_query_processor
    _global_query_processor = None
    logger.info("查询处理器已重置")
