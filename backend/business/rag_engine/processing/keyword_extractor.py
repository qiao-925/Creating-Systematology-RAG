"""
从 PDF 标题提取关键词，供离线词云使用。

主要接口：
- extract_pdf_titles(dir_path): 扫描目录下所有 PDF，返回 (标题文本, 文件名) 列表
- build_keywords_from_titles(titles): 从标题文本分词并统计词频，返回带权关键词列表
"""

import re
from pathlib import Path
from typing import List, Tuple
from collections import Counter

from backend.infrastructure.logger import get_logger

logger = get_logger("keyword_extractor")

# 仅处理 PDF
PDF_SUFFIX = ".pdf"
# 分词：空白、下划线、常见中英文标点
TITLE_SPLIT_PATTERN = re.compile(r"[\s_，。！？、；：\-,.]+")
# 过滤：至少 2 个字符（避免单字噪声），且非纯数字
MIN_WORD_LEN = 2


def _get_pdf_title(file_path: Path) -> str:
    """从 PDF 元数据或文件名取标题。只读元数据，不解析正文。"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(file_path))
        if reader.metadata and getattr(reader.metadata, "title", None):
            t = reader.metadata.title
            if t and isinstance(t, str) and t.strip():
                return t.strip()
    except Exception as e:
        logger.debug("PDF metadata read failed %s: %s", file_path.name, e)
    return file_path.stem


def extract_pdf_titles(dir_path: Path) -> List[Tuple[str, str]]:
    """扫描目录下所有 PDF，返回 [(标题文本, 文件名), ...]。"""
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        logger.warning("Not a directory: %s", dir_path)
        return []
    result = []
    for p in dir_path.rglob("*"):
        if p.is_file() and p.suffix.lower() == PDF_SUFFIX:
            title = _get_pdf_title(p)
            result.append((title, p.name))
    return result


def _tokenize_title(title: str) -> List[str]:
    """按标点/空白分词，保留长度>=MIN_WORD_LEN 且非纯数字的片段。"""
    parts = TITLE_SPLIT_PATTERN.split(title)
    words = []
    for s in parts:
        s = s.strip()
        if not s:
            continue
        if len(s) >= MIN_WORD_LEN and not s.isdigit():
            words.append(s)
    return words


def build_keywords_from_titles(
    title_tuples: List[Tuple[str, str]],
) -> List[dict]:
    """从 (标题, 文件名) 列表统计词频，返回 [{"word": "x", "weight": n}, ...]。"""
    counter: Counter[str] = Counter()
    for title, _ in title_tuples:
        for w in _tokenize_title(title):
            counter[w] += 1
    return [{"word": w, "weight": c} for w, c in counter.most_common()]
