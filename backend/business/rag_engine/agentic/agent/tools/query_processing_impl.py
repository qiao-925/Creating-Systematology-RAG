"""
查询处理工具实现：意图理解、查询改写、多意图分解的核心逻辑

主要功能：
- analyze_intent()：分析查询意图
- rewrite_query()：改写查询
- decompose_multi_intent()：分解多意图查询
"""

import json
from typing import Optional

from backend.infrastructure.logger import get_logger
from backend.infrastructure.config import config
from backend.infrastructure.llms import create_deepseek_llm_for_structure

logger = get_logger('rag_engine.agentic.tools.query_processing')

_llm_instance = None


def _get_llm():
    """获取LLM实例（延迟初始化，单例模式）"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = create_deepseek_llm_for_structure(
            api_key=config.DEEPSEEK_API_KEY,
            model=config.LLM_MODEL,
            max_tokens=1024,
        )
        logger.info("查询处理工具LLM已初始化")
    return _llm_instance


def _extract_json(text: str) -> str:
    """从文本中提取JSON（处理markdown代码块）"""
    text = text.strip()
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        return text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        return text[start:end].strip()
    return text


def analyze_intent(query: str) -> str:
    """分析查询意图，识别查询类型、复杂度和关键实体
    
    Args:
        query: 用户原始查询
        
    Returns:
        JSON字符串，包含意图分析结果
    """
    try:
        llm = _get_llm()
        
        prompt = f"""分析查询的意图和特征，返回JSON。

【查询】{query}

【查询类型】factual/comparative/explanatory/exploratory/specific/multi_intent
【复杂度】simple/medium/complex

返回JSON：
{{"query_type":"类型","complexity":"复杂度","entities":["实体"],"intent_summary":"意图描述","needs_rewrite":bool,"needs_decompose":bool,"confidence":0.0-1.0}}

只返回JSON。"""

        response = llm.complete(prompt)
        result_text = _extract_json(response.text)
        result = json.loads(result_text)
        
        logger.info(
            "意图分析完成",
            query=query[:50],
            query_type=result.get("query_type"),
            needs_rewrite=result.get("needs_rewrite"),
        )
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        logger.error("意图分析失败", error=str(e), query=query[:50])
        return json.dumps({
            "query_type": "factual",
            "complexity": "medium",
            "entities": [],
            "intent_summary": query,
            "needs_rewrite": False,
            "needs_decompose": False,
            "confidence": 0.5,
            "error": str(e)
        }, ensure_ascii=False)


def rewrite_query(query: str, intent_analysis: Optional[str] = None) -> str:
    """改写查询以提升检索效果
    
    Args:
        query: 原始查询
        intent_analysis: 意图分析结果（可选，JSON字符串）
        
    Returns:
        JSON字符串，包含改写后的查询列表
    """
    try:
        llm = _get_llm()
        
        intent_info = ""
        if intent_analysis:
            try:
                intent = json.loads(intent_analysis)
                intent_info = f"【意图】类型:{intent.get('query_type')}, 实体:{intent.get('entities', [])}\n"
            except json.JSONDecodeError:
                pass
        
        prompt = f"""改写查询使其更适合检索。

【原始查询】{query}
{intent_info}
【原则】必须保留所有关键实体，补充领域关键词，扩展语义。

返回JSON：
{{"original_query":"原查询","rewritten_queries":["改写1","改写2"],"preserved_entities":["实体"],"added_keywords":["关键词"],"rewrite_reason":"理由"}}

只返回JSON。"""

        response = llm.complete(prompt)
        result_text = _extract_json(response.text)
        result = json.loads(result_text)
        
        logger.info(
            "查询改写完成",
            original=query[:50],
            rewritten_count=len(result.get("rewritten_queries", [])),
        )
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        logger.error("查询改写失败", error=str(e), query=query[:50])
        return json.dumps({
            "original_query": query,
            "rewritten_queries": [query],
            "preserved_entities": [],
            "added_keywords": [],
            "rewrite_reason": f"改写失败: {str(e)}",
            "error": str(e)
        }, ensure_ascii=False)


def decompose_multi_intent(query: str) -> str:
    """将多意图查询分解为多个子查询
    
    Args:
        query: 包含多个意图的查询
        
    Returns:
        JSON字符串，包含分解后的子查询列表
    """
    try:
        llm = _get_llm()
        
        prompt = f"""判断查询是否包含多个意图，如果是则分解。

【查询】{query}

返回JSON：
{{"is_multi_intent":bool,"intent_count":数量,"sub_queries":[{{"query":"子查询","intent_type":"类型","priority":1}}],"decompose_reason":"理由"}}

只返回JSON。"""

        response = llm.complete(prompt)
        result_text = _extract_json(response.text)
        result = json.loads(result_text)
        
        logger.info(
            "多意图分解完成",
            query=query[:50],
            is_multi_intent=result.get("is_multi_intent"),
            intent_count=result.get("intent_count", 1),
        )
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        logger.error("多意图分解失败", error=str(e), query=query[:50])
        return json.dumps({
            "is_multi_intent": False,
            "intent_count": 1,
            "sub_queries": [{"query": query, "intent_type": "unknown", "priority": 1}],
            "decompose_reason": f"分解失败: {str(e)}",
            "error": str(e)
        }, ensure_ascii=False)
