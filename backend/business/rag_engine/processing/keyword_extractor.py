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
# 词的最大长度：每个词不能超过5个字
MAX_WORD_LEN = 5
# 过滤无意义的词（如 "(1)", "第1", "第2" 等）
MEANINGLESS_PATTERNS = [
    re.compile(r"^\([\d]+\)$"),  # (1), (2) 等
    re.compile(r"^第[\d]+[章节部分]$"),  # 第1章、第2节等
    re.compile(r"^[\d]+[\.、]$"),  # 1.、2、等
    re.compile(r"^[\d]+$"),  # 纯数字
    re.compile(r"^[\(\)\[\]（）【】]+$"),  # 纯括号
]

# 无意义的结尾字符（这些词通常是不完整的片段）
MEANINGLESS_SUFFIXES = ["的", "和", "与", "及", "或", "等", "——", "—", "-", "、", "，", "。", "：", "；"]
# 无意义的开头字符
MEANINGLESS_PREFIXES = ["——", "—", "-", "、", "，", "。", "：", "；", "的", "和", "与", "及", "或"]

# 语义不通的片段黑名单（明显残缺或误切）
SEMANTIC_BLOCKLIST = frozenset({
    "从系", "封信", "一封信", "系统工", "系统科", "统工程", "钱学", "学森",
    "于景", "景元", "戴汝", "汝为", "东川", "孙东",
})


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


def _is_complete_segment(word: str, source: str, start_pos: int) -> bool:
    """检查从滑动窗口提取的词是否是完整的片段。
    
    对于滑动窗口提取的词，需要检查：
    1. 是否在词的边界（开头或结尾）
    2. 是否是一个完整的语义单元
    """
    # 如果词在源字符串的开头或结尾，更可能是完整的
    is_at_start = start_pos == 0
    is_at_end = start_pos + len(word) == len(source)
    
    if is_at_start or is_at_end:
        # 在边界位置的词，需要检查是否是常见完整词
        common_words = {
            # 2-3字常见词
            "系统", "工程", "科学", "技术", "方法", "理论", "思想", "实践", "中国",
            "钱学", "学森",  # 这些是"钱学森"的一部分，但可以保留
            # 4-5字常见词
            "系统工程", "系统科学", "复杂巨系统", "马克思主义", "科学技术",
            "系统思想", "系统实践", "系统方法", "系统理论", "钱学森", "中国系统工"
        }
        if word in common_words:
            return True
        # 对于不在常见词列表中的边界词，如果是2-3字，允许；4-5字需要更严格
        if len(word) <= 3:
            return True
        # 4-5字的边界词，如果不是常见词，很可能是片段
        return False
    
    # 对于不在边界的词，需要更严格的检查
    # 检查词的前后字符
    before_char = source[start_pos - 1] if start_pos > 0 else ""
    after_char = source[start_pos + len(word)] if start_pos + len(word) < len(source) else ""
    
    # 如果前后是标点、空格或分隔符，说明是完整片段
    separators = r"，。！？、；：\-,.()[]（）【】\s_———"
    if before_char in separators or after_char in separators:
        # 即使前后有分隔符，也需要检查是否是常见完整词
        common_words = {
            "系统工程", "系统科学", "复杂巨系统", "马克思主义", "科学技术",
            "系统思想", "系统实践", "系统方法", "系统理论"
        }
        if word in common_words:
            return True
        # 对于不在常见词列表中的词，如果是2-3字，允许；4-5字需要更严格
        if len(word) <= 3:
            return True
        # 4-5字的词，如果不是常见词，很可能是片段
        return False
    
    # 对于完全在中间的词（前后都没有分隔符），只保留常见完整词
    common_words = {
        "系统工程", "系统科学", "复杂巨系统", "马克思主义", "科学技术",
        "系统思想", "系统实践", "系统方法", "系统理论", "钱学森"
    }
    if word in common_words:
        return True
    
    # 其他在中间的词，很可能是片段，过滤掉
    return False


def _is_meaningful_word(word: str) -> bool:
    """判断一个词是否有意义（不是无意义的片段）。"""
    if not word or len(word) < MIN_WORD_LEN:
        return False
    
    # 检查无意义模式
    if any(pattern.match(word) for pattern in MEANINGLESS_PATTERNS):
        return False
    
    # 检查是否以无意义字符开头或结尾
    if word.startswith(tuple(MEANINGLESS_PREFIXES)):
        return False
    if word.endswith(tuple(MEANINGLESS_SUFFIXES)):
        return False
    
    # 检查是否包含过多的标点符号
    punct_chars = r"———，。！？、；：\-,.()[]（）【】"
    punct_count = sum(1 for c in word if c in punct_chars)
    if punct_count > len(word) * 0.3:
        return False
    
    # 检查是否是明显不完整的片段（如"国系统工程"、"学森系统科"等）
    # 这些词通常缺少开头或结尾的关键字
    incomplete_starts = ["国", "统", "学", "森", "的", "和", "与", "及", "或", "等", "工", "程", "部", "者", "员", "志", "会", "萍", "香"]
    incomplete_ends = ["国", "统", "学", "森", "的", "和", "与", "及", "或", "等", "工", "程"]
    
    # 常见完整词的白名单（扩展）
    common_complete_words = {
        "系统工程", "系统科学", "钱学森", "马克思主义", "科学技术", 
        "复杂巨系统", "系统思想", "系统实践", "系统方法", "系统理论",
        "系统分析", "系统设计", "系统管理", "系统优化", "国防", "国家",
        "学问", "学习", "学成就", "学体系", "学技术", "学革命", "学思想",
        "统管理", "统论", "统工程", "系统工", "系统科"
    }
    
    # 对于3-5字的词，如果开头或结尾是这些模式，很可能是片段
    if len(word) >= 3:
        # 如果词在白名单中，直接通过
        if word in common_complete_words:
            return True
        
        # 检查开头是否是不完整模式
        if word[0] in incomplete_starts:
            # 对于4-5字的词，如果以这些字符开头，很可能是片段
            if len(word) >= 4:
                return False
            # 对于3字的词，也需要检查是否是常见完整词
            if len(word) == 3:
                # 允许一些常见的3字词
                allowed_3char = {"系统", "科学", "工程", "技术", "方法", "理论", "思想", "实践", "中国", "国防", "国家"}
                if word not in allowed_3char:
                    return False
        
        # 检查结尾是否是不完整模式
        if word[-1] in incomplete_ends:
            # 如果结尾是"国"、"统"、"学"、"森"、"的"等，很可能是片段
            if word[-1] in ["国", "统", "学", "森", "的"]:
                return False
            # 如果结尾是"和"、"与"、"及"等，也很可能是片段
            if word[-1] in ["和", "与", "及", "或", "等"]:
                return False
    
    return True


def _extract_keywords_from_long_word(word: str) -> List[str]:
    """从超过MAX_WORD_LEN的长词中提取2-5字的有意义关键词。
    
    策略：
    1. 优先按标点符号分割，提取完整片段
    2. 对于没有标点的长词，尝试识别其中的完整词组
    3. 过滤掉无意义的片段（如以"的"、"和"等结尾的片段）
    """
    if len(word) <= MAX_WORD_LEN:
        if _is_meaningful_word(word):
            return [word]
        return []
    
    keywords = []
    seen = set()
    
    # 策略1: 先尝试按常见分隔符分割（破折号、空格等）
    # 这些分隔符通常表示完整的词组边界
    separators = ["——", "—", "-", "：", ":", "（", "(", "）", ")", "【", "[", "】", "]"]
    parts = [word]
    for sep in separators:
        new_parts = []
        for part in parts:
            if sep in part:
                new_parts.extend(part.split(sep))
            else:
                new_parts.append(part)
        parts = [p.strip() for p in new_parts if p.strip()]
    
    # 处理分割后的片段
    for part in parts:
        if len(part) <= MAX_WORD_LEN:
            if _is_meaningful_word(part) and part not in seen:
                keywords.append(part)
                seen.add(part)
        else:
            # 对于仍然过长的片段，使用滑动窗口提取
            # 但只保留有意义的片段，并且更严格地过滤
            for length in range(MAX_WORD_LEN, MIN_WORD_LEN - 1, -1):
                for i in range(len(part) - length + 1):
                    subword = part[i:i + length]
                    # 更严格的检查：对于滑动窗口提取的词，需要额外验证
                    if (_is_meaningful_word(subword) and 
                        subword not in seen and
                        _is_complete_segment(subword, part, i)):
                        keywords.append(subword)
                        seen.add(subword)
                
                # 如果已经提取到足够的5字片段，提前结束
                if length == MAX_WORD_LEN and len([k for k in keywords if len(k) == MAX_WORD_LEN]) >= 3:
                    break
    
    # 如果没有找到有意义的关键词，尝试提取前5个字（如果它有意义）
    if not keywords:
        candidate = word[:MAX_WORD_LEN]
        if _is_meaningful_word(candidate):
            return [candidate]
    
    return keywords


def _tokenize_title(title: str) -> List[str]:
    """按标点/空白分词，保留长度>=MIN_WORD_LEN且<=MAX_WORD_LEN的有意义片段。"""
    parts = TITLE_SPLIT_PATTERN.split(title)
    words = []
    for s in parts:
        s = s.strip()
        if not s:
            continue
        # 基本过滤：长度和数字检查
        if len(s) < MIN_WORD_LEN or s.isdigit():
            continue
        # 过滤无意义的词
        if any(pattern.match(s) for pattern in MEANINGLESS_PATTERNS):
            continue
        
        # 如果词超过最大长度，提取其中的关键词片段
        if len(s) > MAX_WORD_LEN:
            extracted = _extract_keywords_from_long_word(s)
            words.extend(extracted)
        else:
            # 只保留有意义的词
            if _is_meaningful_word(s):
                words.append(s)
    return words


def _filter_semantic_fragments(word_count_list: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
    """过滤语义不通的片段：黑名单 + 去掉被更长词包含的 3 字及以上词。"""
    # 先按黑名单过滤
    filtered = [(w, c) for w, c in word_count_list if w not in SEMANTIC_BLOCKLIST]
    words_set = {w for w, _ in filtered}
    # 再去掉「被更长词包含」的 3 字及以上词，保留更长、语义更完整的词
    result = []
    for w, c in filtered:
        if len(w) < 3:
            result.append((w, c))
            continue
        # 若存在更长词包含 w，则 w 视为片段，去掉
        if any(w in other and other != w for other in words_set if len(other) > len(w)):
            continue
        result.append((w, c))
    return result


def build_keywords_from_titles(
    title_tuples: List[Tuple[str, str]],
) -> List[dict]:
    """从 (标题, 文件名) 列表统计词频，返回 [{"word": "x", "weight": n}, ...]。"""
    counter: Counter[str] = Counter()
    for title, _ in title_tuples:
        for w in _tokenize_title(title):
            counter[w] += 1
    raw = counter.most_common()
    filtered = _filter_semantic_fragments(raw)
    return [{"word": w, "weight": c} for w, c in filtered]
