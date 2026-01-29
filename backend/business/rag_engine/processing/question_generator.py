"""
根据已选关键词生成 2 个深度问题，供词云「生成问题」使用。
"""

import re
from pathlib import Path
from typing import List

from backend.infrastructure.config import config
from backend.infrastructure.llms.factory import create_llm
from backend.infrastructure.logger import get_logger

logger = get_logger("question_generator")


def _prompt_path() -> Path:
    return config.PROJECT_ROOT / "prompts" / "question" / "generate.txt"


def _load_prompt() -> str:
    with open(_prompt_path(), encoding="utf-8") as f:
        return f.read()


def generate_questions(keywords: List[str], model_id: str | None = None) -> List[str]:
    """根据关键词生成 2 个问题。

    Args:
        keywords: 已选关键词列表
        model_id: 可选模型 ID，默认使用配置

    Returns:
        长度为 2 的问题列表；失败时返回空列表或不足 2 条
    """
    if not keywords:
        return []
    prompt_tpl = _load_prompt()
    prompt = prompt_tpl.replace("{keywords}", "、".join(keywords))
    try:
        llm = create_llm(model_id=model_id, temperature=0.7, max_tokens=256)
        resp = llm.complete(prompt)
        text = resp.text.strip()
    except Exception as e:
        logger.exception("问题生成失败: %s", e)
        return []
    # 解析：按行取非空，取前 2 条
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # 去掉行首的「问题1」「1.」等
    cleaned = []
    for ln in lines:
        ln = re.sub(r"^(?:问题[12]|[\d]+[\.．、])\s*", "", ln).strip()
        if ln:
            cleaned.append(ln)
    return cleaned[:2]
