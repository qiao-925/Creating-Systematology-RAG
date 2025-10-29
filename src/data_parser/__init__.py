"""
数据解析层
统一使用 SimpleDirectoryReader 解析所有支持的文件格式
"""

from src.data_parser.document_parser import DocumentParser

__all__ = ['DocumentParser']

