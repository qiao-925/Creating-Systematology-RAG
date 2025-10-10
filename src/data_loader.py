"""
数据加载器模块
支持从多种数据源加载文档：Markdown文件、网页、GitHub仓库等
"""

import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from llama_index.core import Document
from llama_index.core.schema import Document as LlamaDocument

try:
    from llama_index.readers.github import GithubRepositoryReader, GithubClient
except ImportError:
    GithubRepositoryReader = None
    GithubClient = None

from src.logger import setup_logger

# 创建日志器
logger = setup_logger('data_loader')


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


class GithubLoader:
    """GitHub仓库内容加载器"""
    
    def __init__(self, github_token: Optional[str] = None):
        """初始化GitHub加载器
        
        Args:
            github_token: GitHub访问令牌（可选，用于访问私有仓库）
        """
        if GithubRepositoryReader is None:
            raise ImportError(
                "需要安装 llama-index-readers-github 包。"
                "运行: pip install llama-index-readers-github"
            )
        
        self.github_token = github_token
        self.github_client = GithubClient(github_token=github_token) if github_token else GithubClient()
    
    def load_repository(self, 
                       owner: str, 
                       repo: str, 
                       branch: Optional[str] = None,
                       show_progress: bool = True) -> List[LlamaDocument]:
        """从GitHub仓库加载文档
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称（可选，默认为仓库默认分支）
            show_progress: 是否显示进度条
            
        Returns:
            Document对象列表
        """
        try:
            branch = branch or "main"
            logger.info(f"开始加载 GitHub 仓库: {owner}/{repo}, 分支: {branch}")
            
            if show_progress:
                print(f"📦 正在从 GitHub 加载 {owner}/{repo} (分支: {branch})...")
            
            # 创建 Reader
            reader = GithubRepositoryReader(
                github_client=self.github_client,
                owner=owner,
                repo=repo,
                use_parser=False,
                verbose=False,
            )
            
            # 加载文档
            documents = reader.load_data(branch=branch)
            
            if not documents:
                logger.warning(f"仓库 {owner}/{repo} 未返回任何文档")
                print(f"⚠️  仓库为空或无可读文件")
                return []
            
            # 增强元数据（带进度条）
            if show_progress:
                print(f"正在处理 {len(documents)} 个文件...")
                iterator = tqdm(documents, desc="增强元数据", unit="文件")
            else:
                iterator = documents
            
            for doc in iterator:
                if not doc.metadata:
                    doc.metadata = {}
                doc.metadata.update({
                    "source_type": "github",
                    "repository": f"{owner}/{repo}",
                    "branch": branch,
                })
            
            if show_progress:
                print(f"✅ 成功加载 {len(documents)} 个文件")
            
            logger.info(f"成功加载 {len(documents)} 个文件从 {owner}/{repo}")
            return documents
            
        except Exception as e:
            # 详细错误处理
            error_msg = self._handle_error(e, owner, repo)
            logger.error(f"加载失败 {owner}/{repo}: {error_msg}")
            return []
    
    def load_repositories(self, repo_configs: List[dict]) -> List[LlamaDocument]:
        """批量加载多个GitHub仓库
        
        Args:
            repo_configs: 仓库配置列表，每个配置包含 owner, repo, branch
            
        Returns:
            Document对象列表
        """
        all_documents = []
        
        for config in repo_configs:
            owner = config.get("owner")
            repo = config.get("repo")
            branch = config.get("branch")
            
            if not owner or not repo:
                print(f"⚠️  跳过无效配置: {config}")
                continue
            
            documents = self.load_repository(owner, repo, branch)
            all_documents.extend(documents)
        
        print(f"\n📚 总共从 {len(repo_configs)} 个仓库加载了 {len(all_documents)} 个文件")
        return all_documents
    
    def _handle_error(self, error: Exception, owner: str, repo: str) -> str:
        """统一错误处理
        
        Args:
            error: 异常对象
            owner: 仓库所有者
            repo: 仓库名称
            
        Returns:
            错误描述字符串
        """
        error_type = type(error).__name__
        error_str = str(error)
        
        # 网络相关错误
        if isinstance(error, requests.Timeout):
            print(f"❌ 网络超时: {owner}/{repo}")
            print("   建议：1) 检查网络连接 2) 稍后重试")
            return "网络超时"
        
        elif isinstance(error, requests.ConnectionError):
            print(f"❌ 网络连接失败")
            print("   建议：1) 检查网络 2) 检查代理设置")
            return "网络连接失败"
        
        # GitHub API 错误（通过错误消息判断）
        elif "404" in error_str or "Not Found" in error_str:
            print(f"❌ 仓库不存在: {owner}/{repo}")
            print("   请检查：1) 仓库名拼写 2) 是否为私有仓库（需要Token）")
            return "仓库不存在(404)"
        
        elif "403" in error_str or "Forbidden" in error_str or "rate limit" in error_str.lower():
            print(f"❌ 访问被拒绝: {owner}/{repo}")
            print("   请检查：1) Token权限 2) API限流（GitHub限制：每小时60次）")
            return "访问被拒绝(403)"
        
        elif "401" in error_str or "Unauthorized" in error_str or "Bad credentials" in error_str:
            print(f"❌ 认证失败")
            print("   请检查：1) Token是否正确 2) Token是否过期")
            return "认证失败(401)"
        
        # 通用错误
        else:
            print(f"❌ 未知错误: {error_type}: {error}")
            print(f"   请报告此问题到项目 Issue")
            return f"{error_type}: {error_str}"


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


def load_documents_from_github(owner: str,
                               repo: str,
                               branch: Optional[str] = None,
                               github_token: Optional[str] = None,
                               clean: bool = True,
                               show_progress: bool = True) -> List[LlamaDocument]:
    """从GitHub仓库加载文档（便捷函数）
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名称（可选）
        github_token: GitHub访问令牌（可选）
        clean: 是否清理文本
        show_progress: 是否显示进度条
        
    Returns:
        Document对象列表
    """
    loader = GithubLoader(github_token=github_token)
    documents = loader.load_repository(owner, repo, branch, show_progress=show_progress)
    
    if clean and documents:
        processor = DocumentProcessor()
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

