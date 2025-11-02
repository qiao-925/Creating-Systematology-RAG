"""
Grep检索器

基于文本搜索的检索方式，支持正则表达式和文件系统操作
类似Cursor Cloud的grep方案
"""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from llama_index.core.schema import NodeWithScore, TextNode

from src.logger import setup_logger
from src.config import config

logger = setup_logger('grep_retriever')


class GrepRetriever:
    """Grep检索器
    
    基于文本搜索的检索方式，支持正则表达式和文件系统操作
    类似Cursor Cloud的grep方案
    
    Examples:
        >>> retriever = GrepRetriever(data_source_path="data/")
        >>> results = retriever.retrieve("系统科学", top_k=5)
    """
    
    def __init__(
        self,
        data_source_path: Optional[str] = None,
        enable_regex: bool = True,
        case_sensitive: bool = False,
        max_results: int = 10,
        timeout: int = 5,
    ):
        """初始化Grep检索器
        
        Args:
            data_source_path: 数据源路径（文档目录），默认使用config.RAW_DATA_PATH
            enable_regex: 是否启用正则表达式
            case_sensitive: 是否区分大小写
            max_results: 最大返回结果数
            timeout: 搜索超时时间（秒）
        """
        if data_source_path:
            self.data_source_path = Path(data_source_path)
        else:
            # 使用配置中的原始数据路径
            self.data_source_path = config.RAW_DATA_PATH
            
        # 确保路径存在
        if not self.data_source_path.exists():
            logger.warning(f"数据源路径不存在: {self.data_source_path}")
            self.data_source_path.mkdir(parents=True, exist_ok=True)
        
        self.enable_regex = enable_regex
        self.case_sensitive = case_sensitive
        self.max_results = max_results
        self.timeout = timeout
        
        logger.info(
            f"Grep检索器初始化: "
            f"路径={self.data_source_path}, "
            f"正则={enable_regex}, "
            f"大小写敏感={case_sensitive}, "
            f"最大结果数={max_results}"
        )
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[NodeWithScore]:
        """执行grep检索
        
        Args:
            query: 查询文本（可以是关键词或正则表达式）
            top_k: 返回Top-K结果
            
        Returns:
            检索到的节点列表（带分数）
        """
        top_k = top_k or self.max_results
        
        # 使用grep搜索文件
        results = self._grep_search(query)
        
        if not results:
            logger.info(f"Grep检索未找到结果: {query}")
            return []
        
        # 转换为NodeWithScore格式
        nodes = self._convert_to_nodes(results, query)
        
        # 按相关性排序
        nodes = self._rank_results(nodes, query)
        
        return nodes[:top_k]
    
    def _grep_search(self, pattern: str) -> List[Dict]:
        """执行grep搜索
        
        Returns:
            [{"file": path, "line": num, "content": text, "matches": count}]
        """
        import platform
        
        results = []
        
        # 跨平台支持：Windows使用Python实现，Linux/Mac使用grep
        if platform.system() == "Windows":
            results = self._grep_search_windows(pattern)
        else:
            results = self._grep_search_unix(pattern)
        
        return results
    
    def _grep_search_unix(self, pattern: str) -> List[Dict]:
        """Unix/Linux系统使用grep命令"""
        results = []
        
        # 构建grep命令
        cmd = ["grep", "-rn"]
        if not self.case_sensitive:
            cmd.append("-i")
        if self.enable_regex:
            cmd.append("-E")
        cmd.extend([pattern, str(self.data_source_path)])
        
        try:
            # 执行grep
            output = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            # 解析结果
            for line in output.stdout.splitlines():
                match = re.match(r"([^:]+):(\d+):(.+)", line)
                if match:
                    file_path, line_num, content = match.groups()
                    matches = len(re.findall(pattern, content, re.IGNORECASE if not self.case_sensitive else 0))
                    results.append({
                        "file": file_path,
                        "line": int(line_num),
                        "content": content,
                        "matches": matches,
                    })
        except subprocess.TimeoutExpired:
            logger.warning(f"Grep搜索超时（{self.timeout}秒）: {pattern}")
        except Exception as e:
            logger.warning(f"Grep搜索失败: {e}")
        
        return results
    
    def _grep_search_windows(self, pattern: str) -> List[Dict]:
        """Windows系统使用Python实现grep功能"""
        results = []
        
        # 编译正则表达式
        flags = 0 if self.case_sensitive else re.IGNORECASE
        if self.enable_regex:
            regex = re.compile(pattern, flags)
        else:
            # 转义特殊字符
            escaped_pattern = re.escape(pattern)
            regex = re.compile(escaped_pattern, flags)
        
        # 遍历文件
        try:
            for file_path in self.data_source_path.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # 跳过二进制文件
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line_content in enumerate(f, start=1):
                            matches = regex.findall(line_content)
                            if matches:
                                results.append({
                                    "file": str(file_path),
                                    "line": line_num,
                                    "content": line_content.strip(),
                                    "matches": len(matches),
                                })
                                
                                # 限制结果数量，避免内存溢出
                                if len(results) >= self.max_results * 10:
                                    break
                except Exception as e:
                    logger.debug(f"跳过文件 {file_path}: {e}")
                    continue
                
                # 超时保护
                if len(results) >= self.max_results * 10:
                    break
                    
        except Exception as e:
            logger.warning(f"Windows grep搜索失败: {e}")
        
        return results
    
    def _convert_to_nodes(self, results: List[Dict], query: str) -> List[NodeWithScore]:
        """转换为NodeWithScore格式"""
        nodes = []
        
        for result in results:
            # 创建TextNode
            node = TextNode(
                text=result["content"],
                metadata={
                    "file_path": result["file"],
                    "line_number": result["line"],
                    "retrieval_method": "grep",
                    "query": query,
                }
            )
            
            # 计算分数（基于匹配次数）
            score = self._calculate_score(result, query)
            
            nodes.append(NodeWithScore(node=node, score=score))
        
        return nodes
    
    def _calculate_score(self, result: Dict, query: str) -> float:
        """计算相关性分数
        
        可以基于：
        - 匹配次数
        - 匹配位置（行号）
        - 查询长度匹配度
        """
        # 基础分数：基于匹配次数
        base_score = min(result["matches"] / 10.0, 1.0)
        
        # 位置权重：越靠前的行号权重越高（假设重要信息在文件前面）
        line_weight = max(0.5, 1.0 / (result["line"] / 100.0 + 1))
        
        # 查询长度匹配度：查询越长，匹配越精确
        query_len_weight = min(len(query) / 20.0, 1.0)
        
        # 综合分数
        final_score = base_score * line_weight * query_len_weight
        
        return min(final_score, 1.0)
    
    def _rank_results(self, nodes: List[NodeWithScore], query: str) -> List[NodeWithScore]:
        """按相关性排序结果"""
        # 按分数降序排序
        return sorted(nodes, key=lambda x: x.score, reverse=True)
