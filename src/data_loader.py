"""
数据加载器模块
支持从多种数据源加载文档：Markdown文件、网页等
"""

import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from llama_index.core import Document
from llama_index.core.schema import Document as LlamaDocument


class MarkdownLoader:
    """Markdown文件加载器"""
    
    def __init__(self):
        self.supported_extensions = [".md", ".markdown"]
    
    def load_file(self, file_path: Path) -> Optional[LlamaDocument]:
        """加载单个Markdown文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            LlamaDocument对象，如果加载失败返回None
        """
        try:
            if not file_path.exists():
                print(f"❌ 文件不存在: {file_path}")
                return None
                
            if file_path.suffix.lower() not in self.supported_extensions:
                print(f"❌ 不支持的文件格式: {file_path.suffix}")
                return None
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取标题作为文档标题（如果有的话）
            title = self._extract_title(content)
            if not title:
                title = file_path.stem
            
            # 创建Document对象
            doc = LlamaDocument(
                text=content,
                metadata={
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "title": title,
                    "source_type": "markdown",
                }
            )
            
            return doc
            
        except Exception as e:
            print(f"❌ 加载文件失败 {file_path}: {e}")
            return None
    
    def load_directory(self, directory_path: Path, recursive: bool = True) -> List[LlamaDocument]:
        """加载目录中的所有Markdown文件
        
        Args:
            directory_path: 目录路径
            recursive: 是否递归加载子目录
            
        Returns:
            Document对象列表
        """
        documents = []
        
        if not directory_path.exists() or not directory_path.is_dir():
            print(f"❌ 目录不存在或不是有效目录: {directory_path}")
            return documents
        
        # 查找所有Markdown文件
        pattern = "**/*" if recursive else "*"
        for ext in self.supported_extensions:
            for file_path in directory_path.glob(f"{pattern}{ext}"):
                if file_path.is_file():
                    doc = self.load_file(file_path)
                    if doc:
                        documents.append(doc)
                        print(f"✅ 已加载: {file_path.name}")
        
        print(f"\n📚 总共加载了 {len(documents)} 个Markdown文件")
        return documents
    
    def _extract_title(self, content: str) -> Optional[str]:
        """从Markdown内容中提取标题（第一个一级标题）"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return None


class WebLoader:
    """网页内容加载器"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def load_url(self, url: str) -> Optional[LlamaDocument]:
        """从URL加载网页内容
        
        Args:
            url: 网页URL
            
        Returns:
            LlamaDocument对象，如果加载失败返回None
        """
        try:
            # 验证URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                print(f"❌ 无效的URL: {url}")
                return None
            
            # 发送HTTP请求
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 移除脚本和样式标签
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 提取文本内容
            text = soup.get_text(separator='\n', strip=True)
            
            # 清理多余的空行
            text = re.sub(r'\n\s*\n', '\n\n', text)
            
            # 提取标题
            title = soup.title.string if soup.title else parsed.netloc
            
            # 创建Document对象
            doc = LlamaDocument(
                text=text,
                metadata={
                    "url": url,
                    "title": title,
                    "source_type": "web",
                    "domain": parsed.netloc,
                }
            )
            
            return doc
            
        except requests.RequestException as e:
            print(f"❌ 网络请求失败 {url}: {e}")
            return None
        except Exception as e:
            print(f"❌ 处理网页失败 {url}: {e}")
            return None
    
    def load_urls(self, urls: List[str]) -> List[LlamaDocument]:
        """批量加载多个URL
        
        Args:
            urls: URL列表
            
        Returns:
            Document对象列表
        """
        documents = []
        
        for url in urls:
            doc = self.load_url(url)
            if doc:
                documents.append(doc)
                print(f"✅ 已加载: {url}")
        
        print(f"\n🌐 总共加载了 {len(documents)} 个网页")
        return documents


class DocumentProcessor:
    """文档预处理器"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        # 移除多余的空白字符
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 移除行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        
        # 移除多余的空行（保留最多一个空行，即最多两个连续换行）
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            if line:  # 非空行
                cleaned_lines.append(line)
                prev_empty = False
            else:  # 空行
                if not prev_empty:  # 只保留第一个空行
                    cleaned_lines.append(line)
                    prev_empty = True
                # 连续的空行跳过
        
        text = '\n'.join(cleaned_lines)
        return text.strip()
    
    @staticmethod
    def enrich_metadata(document: LlamaDocument, additional_metadata: dict) -> LlamaDocument:
        """为文档添加额外的元数据
        
        Args:
            document: 原始文档
            additional_metadata: 要添加的元数据
            
        Returns:
            更新后的文档
        """
        document.metadata.update(additional_metadata)
        return document
    
    @staticmethod
    def filter_by_length(documents: List[LlamaDocument], 
                        min_length: int = 50) -> List[LlamaDocument]:
        """过滤掉太短的文档
        
        Args:
            documents: 文档列表
            min_length: 最小长度
            
        Returns:
            过滤后的文档列表
        """
        filtered = [doc for doc in documents if len(doc.text) >= min_length]
        
        removed_count = len(documents) - len(filtered)
        if removed_count > 0:
            print(f"⚠️  过滤掉 {removed_count} 个过短的文档")
        
        return filtered


# 便捷函数
def load_documents_from_directory(directory_path: str | Path, 
                                 recursive: bool = True,
                                 clean: bool = True) -> List[LlamaDocument]:
    """从目录加载所有Markdown文档（便捷函数）
    
    Args:
        directory_path: 目录路径
        recursive: 是否递归加载
        clean: 是否清理文本
        
    Returns:
        Document对象列表
    """
    directory_path = Path(directory_path)
    loader = MarkdownLoader()
    documents = loader.load_directory(directory_path, recursive=recursive)
    
    if clean:
        processor = DocumentProcessor()
        # Document.text 是只读属性，需要创建新的 Document 对象
        cleaned_documents = []
        for doc in documents:
            cleaned_text = processor.clean_text(doc.text)
            cleaned_doc = LlamaDocument(
                text=cleaned_text,
                metadata=doc.metadata,
                id_=doc.id_
            )
            cleaned_documents.append(cleaned_doc)
        return cleaned_documents
    
    return documents


def load_documents_from_urls(urls: List[str], clean: bool = True) -> List[LlamaDocument]:
    """从URL列表加载文档（便捷函数）
    
    Args:
        urls: URL列表
        clean: 是否清理文本
        
    Returns:
        Document对象列表
    """
    loader = WebLoader()
    documents = loader.load_urls(urls)
    
    if clean:
        processor = DocumentProcessor()
        # Document.text 是只读属性，需要创建新的 Document 对象
        cleaned_documents = []
        for doc in documents:
            cleaned_text = processor.clean_text(doc.text)
            cleaned_doc = LlamaDocument(
                text=cleaned_text,
                metadata=doc.metadata,
                id_=doc.id_
            )
            cleaned_documents.append(cleaned_doc)
        return cleaned_documents
    
    return documents


if __name__ == "__main__":
    # 测试代码
    from src.config import config
    
    print("=== 测试Markdown加载器 ===")
    documents = load_documents_from_directory(config.RAW_DATA_PATH)
    print(f"加载了 {len(documents)} 个文档")
    
    if documents:
        print("\n第一个文档预览:")
        print(f"标题: {documents[0].metadata.get('title')}")
        print(f"内容长度: {len(documents[0].text)}")
        print(f"内容预览: {documents[0].text[:200]}...")

