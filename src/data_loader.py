"""
数据加载器模块
使用 LlamaIndex 官方 Reader 组件，支持从多种数据源加载文档
"""

import os
import re
from pathlib import Path
from typing import List, Optional

from tqdm import tqdm
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document as LlamaDocument

try:
    from llama_index.readers.web import SimpleWebPageReader
except ImportError:
    SimpleWebPageReader = None

try:
    from llama_index.readers.github import GithubRepositoryReader, GithubClient
except ImportError:
    GithubRepositoryReader = None
    GithubClient = None

try:
    from llama_index.readers.wikipedia import WikipediaReader
except ImportError:
    WikipediaReader = None

from src.logger import setup_logger

# 创建日志器
logger = setup_logger('data_loader')


def safe_print(text: str):
    """安全打印（处理编码问题）"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 在 Windows GBK 编码下，回退到 ASCII 友好的输出
        text = text.encode('ascii', 'replace').decode('ascii')
        print(text)


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
            safe_print(f"⚠️  过滤掉 {removed_count} 个过短的文档")
        
        return filtered
    
    @staticmethod
    def extract_title_from_markdown(content: str) -> Optional[str]:
        """从Markdown内容中提取标题（第一个一级标题）
        
        Args:
            content: Markdown 文本内容
            
        Returns:
            提取的标题，如果没有则返回 None
        """
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return None


def load_documents_from_directory(directory_path: str | Path, 
                                 recursive: bool = True,
                                 clean: bool = True,
                                 required_exts: Optional[List[str]] = None) -> List[LlamaDocument]:
    """从目录加载所有文档（使用官方 SimpleDirectoryReader）
    
    Args:
        directory_path: 目录路径
        recursive: 是否递归加载
        clean: 是否清理文本
        required_exts: 文件扩展名列表（默认：[".md", ".markdown"]）
        
    Returns:
        Document对象列表
    """
    directory_path = Path(directory_path)
    required_exts = required_exts or [".md", ".markdown"]
    
    # 验证目录
    if not directory_path.exists() or not directory_path.is_dir():
        safe_print(f"❌ 目录不存在或不是有效目录: {directory_path}")
        logger.error(f"目录不存在: {directory_path}")
        return []
    
    try:
        logger.info(f"开始加载目录: {directory_path}, 递归: {recursive}")
        
        # 使用 SimpleDirectoryReader 加载文档
        reader = SimpleDirectoryReader(
            input_dir=str(directory_path),
            recursive=recursive,
            required_exts=required_exts,
            filename_as_id=True,
            errors='ignore',  # 忽略不可读文件
        )
        
        documents = reader.load_data()
        
        if not documents:
            safe_print(f"⚠️  未找到任何文档（支持格式：{', '.join(required_exts)}）")
            logger.warning(f"目录为空: {directory_path}")
            return []
        
        # 增强元数据
        for doc in documents:
            # 提取文件路径信息
            file_path = doc.metadata.get('file_path', '')
            file_name = doc.metadata.get('file_name', '')
            
            # 为 Markdown 文件提取标题
            if any(file_name.endswith(ext) for ext in ['.md', '.markdown']):
                title = DocumentProcessor.extract_title_from_markdown(doc.text)
                if not title:
                    title = Path(file_name).stem if file_name else "未命名"
                
                doc.metadata.update({
                    "title": title,
                    "source_type": "markdown",
                })
            
            # 确保基础元数据存在
            if not doc.metadata.get('file_path'):
                doc.metadata['file_path'] = file_path
            if not doc.metadata.get('file_name'):
                doc.metadata['file_name'] = file_name
            
            # 输出加载进度
            safe_print(f"✅ 已加载: {file_name}")
        
        safe_print(f"\n📚 总共加载了 {len(documents)} 个文档")
        logger.info(f"成功加载 {len(documents)} 个文档")
        
        # 可选的文本清理
        if clean:
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
        
    except Exception as e:
        safe_print(f"❌ 加载目录失败: {e}")
        logger.error(f"加载目录失败 {directory_path}: {e}")
        return []


def load_documents_from_urls(urls: List[str], 
                            clean: bool = True) -> List[LlamaDocument]:
    """从URL列表加载文档（使用官方 SimpleWebPageReader）
    
    Args:
        urls: URL列表
        clean: 是否清理文本
        
    Returns:
        Document对象列表
    """
    if SimpleWebPageReader is None:
        safe_print("❌ 缺少依赖：llama-index-readers-web")
        safe_print("   安装：pip install llama-index-readers-web")
        logger.error("SimpleWebPageReader 未安装")
        return []
    
    if not urls:
        safe_print("⚠️  URL 列表为空")
        return []
    
    try:
        logger.info(f"开始加载 {len(urls)} 个网页")
        
        # 使用 SimpleWebPageReader 加载网页
        reader = SimpleWebPageReader(html_to_text=True)
        documents = reader.load_data(urls)
        
        if not documents:
            safe_print("⚠️  未成功加载任何网页")
            logger.warning("没有成功加载任何网页")
            return []
        
        # 增强元数据
        for i, doc in enumerate(documents):
            url = urls[i] if i < len(urls) else "unknown"
            
            # 确保有 source_type
            doc.metadata.update({
                "source_type": "web",
                "url": url,
            })
            
            safe_print(f"✅ 已加载: {url}")
        
        safe_print(f"\n🌐 总共加载了 {len(documents)} 个网页")
        logger.info(f"成功加载 {len(documents)} 个网页")
        
        # 可选的文本清理
        if clean:
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
        
    except Exception as e:
        safe_print(f"❌ 加载网页失败: {e}")
        logger.error(f"加载网页失败: {e}")
        return []


def load_documents_from_github(owner: str,
                               repo: str,
                               branch: Optional[str] = None,
                               github_token: Optional[str] = None,
                               clean: bool = True,
                               show_progress: bool = True,
                               filter_directories: Optional[List[str]] = None,
                               filter_file_extensions: Optional[List[str]] = None) -> List[LlamaDocument]:
    """从GitHub仓库加载文档（使用官方 GithubRepositoryReader）
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名称（可选，默认 main）
        github_token: GitHub访问令牌（可选，未提供则尝试从环境变量 GITHUB_TOKEN 获取）
        clean: 是否清理文本
        show_progress: 是否显示进度条
        filter_directories: 只加载指定目录（列表格式，如 ["docs", "examples"]）
        filter_file_extensions: 只加载指定扩展名（列表格式，如 [".md", ".py"]）
                               默认排除图片、二进制等文件
        
    Returns:
        Document对象列表
        
    Notes:
        - 公开仓库无需 token，但配置 token 可提高 API 限额（60次/小时 → 5000次/小时）
        - filter 参数内部会自动转换为官方 API 要求的元组格式
        - 默认会过滤掉图片、压缩包等二进制文件
    """
    if GithubRepositoryReader is None or GithubClient is None:
        safe_print("❌ 缺少依赖：llama-index-readers-github")
        safe_print("   安装：pip install llama-index-readers-github")
        logger.error("GithubRepositoryReader 未安装")
        return []
    
    try:
        branch = branch or "main"
        logger.info(f"开始加载 GitHub 仓库: {owner}/{repo}, 分支: {branch}")
        
        if show_progress:
            safe_print(f"📦 正在从 GitHub 加载 {owner}/{repo} (分支: {branch})...")
        
        # 创建 GitHub 客户端
        # GitHub Token 是用户级别的配置，必须通过参数传递
        if not github_token:
            error_msg = (
                "需要提供 GitHub Token。\n"
                "请在 Web 界面的 '🔑 GitHub Token 配置' 中保存您的 Token。\n"
                "获取 Token：https://github.com/settings/tokens\n"
                "权限设置：公开仓库无需勾选任何权限，私有仓库勾选 'repo'"
            )
            if show_progress:
                safe_print(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # 使用用户提供的 Token 创建客户端
        github_client = GithubClient(github_token=github_token, verbose=False)
        if show_progress:
            safe_print(f"✅ 使用用户的 GitHub Token（API 限额：5000次/小时）")
        
        # 如果未指定文件扩展名，使用默认的文本文件列表
        # 注意：根据官方文档，filter 参数格式为元组 (列表, FilterType)
        if filter_file_extensions is None:
            # 默认排除图片、二进制等文件
            filter_file_extensions = (
                ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.pdf', '.zip', '.tar', '.gz', 
                 '.exe', '.dll', '.so', '.dylib', '.bin', '.dat', '.pyc', '.pyo', '.lock'],
                GithubRepositoryReader.FilterType.EXCLUDE,
            )
        elif isinstance(filter_file_extensions, list):
            # 如果传入的是列表，转换为元组格式（默认为 INCLUDE）
            filter_file_extensions = (filter_file_extensions, GithubRepositoryReader.FilterType.INCLUDE)
        
        # filter_directories 同样需要元组格式
        if filter_directories is not None and isinstance(filter_directories, list):
            filter_directories = (filter_directories, GithubRepositoryReader.FilterType.INCLUDE)
        
        # 使用 GithubRepositoryReader 加载仓库
        reader = GithubRepositoryReader(
            github_client=github_client,
            owner=owner,
            repo=repo,
            use_parser=False,
            verbose=False,
            filter_directories=filter_directories,
            filter_file_extensions=filter_file_extensions,
        )
        
        # 尝试加载指定分支
        try:
            documents = reader.load_data(branch=branch)
        except Exception as e:
            error_str = str(e)
            # 如果是 main 分支不存在，尝试 master
            if "404" in error_str and branch == "main":
                logger.info("main 分支不存在，尝试 master 分支")
                if show_progress:
                    safe_print("⚠️  main 分支不存在，尝试 master 分支...")
                branch = "master"
                documents = reader.load_data(branch=branch)
            else:
                raise
        
        if not documents:
            logger.warning(f"仓库 {owner}/{repo} 没有文档")
            if show_progress:
                safe_print(f"⚠️  仓库为空或没有支持的文件类型")
            return []
        
        if show_progress:
            safe_print(f"找到 {len(documents)} 个文件")
        
        # 增强元数据并显示进度
        iterator = tqdm(documents, desc="处理文件", unit="个") if show_progress else documents
        
        processed_docs = []
        for doc in iterator:
            # 获取文件路径
            file_path = doc.metadata.get('file_path', '')
            file_name = doc.metadata.get('file_name', file_path.split('/')[-1] if file_path else 'unknown')
            
            # 增强元数据
            doc.metadata.update({
                "source_type": "github",
                "repository": f"{owner}/{repo}",
                "branch": branch,
                "url": f"https://github.com/{owner}/{repo}/blob/{branch}/{file_path}",
            })
            
            # 确保基础元数据存在
            if not doc.metadata.get('file_name'):
                doc.metadata['file_name'] = file_name
            
            processed_docs.append(doc)
        
        if show_progress:
            safe_print(f"✅ 成功加载 {len(processed_docs)} 个文件")
        
        logger.info(f"成功加载 {len(processed_docs)} 个文件从 {owner}/{repo}")
        
        # 可选的文本清理
        if clean:
            processor = DocumentProcessor()
            cleaned_documents = []
            for doc in processed_docs:
                cleaned_text = processor.clean_text(doc.text)
                cleaned_doc = LlamaDocument(
                    text=cleaned_text,
                    metadata=doc.metadata,
                    id_=doc.id_
                )
                cleaned_documents.append(cleaned_doc)
            return cleaned_documents
        
        return processed_docs
        
    except Exception as e:
        error_msg = _handle_github_error(e, owner, repo, show_progress)
        # 安全记录日志（处理 Unicode 编码问题）
        try:
            logger.error(f"加载失败 {owner}/{repo}: {error_msg}")
        except UnicodeEncodeError:
            # 如果编码失败，使用 ASCII 安全的格式
            safe_error_msg = error_msg.encode('ascii', 'replace').decode('ascii')
            logger.error(f"加载失败 {owner}/{repo}: {safe_error_msg}")
        return []


def sync_github_repository(
    owner: str,
    repo: str,
    branch: str,
    metadata_manager,
    github_token: Optional[str] = None,
    show_progress: bool = True,
    filter_directories: Optional[List[str]] = None,
    filter_file_extensions: Optional[List[str]] = None
) -> tuple:
    """增量同步 GitHub 仓库
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名称
        metadata_manager: 元数据管理器实例
        github_token: GitHub访问令牌（可选）
        show_progress: 是否显示进度
        filter_directories: 只加载指定目录（可选）
        filter_file_extensions: 只加载指定扩展名（可选）
        
    Returns:
        (所有文档列表, FileChange对象)
    """
    from src.metadata_manager import FileChange
    
    # 1. 加载当前仓库的所有文档
    documents = load_documents_from_github(
        owner=owner,
        repo=repo,
        branch=branch,
        github_token=github_token,
        clean=True,
        show_progress=show_progress,
        filter_directories=filter_directories,
        filter_file_extensions=filter_file_extensions
    )
    
    if not documents:
        logger.warning(f"未能加载任何文档从 {owner}/{repo}")
        return [], FileChange()
    
    # 2. 检测变更
    if show_progress:
        safe_print(f"\n🔍 正在检测变更...")
    
    changes = metadata_manager.detect_changes(owner, repo, branch, documents)
    
    if show_progress:
        if changes.has_changes():
            safe_print(f"📊 检测结果: {changes.summary()}")
        else:
            safe_print(f"✅ 没有检测到变更")
    
    return documents, changes


def _handle_github_error(error: Exception, owner: str, repo: str, show_progress: bool = True) -> str:
    """统一 GitHub 错误处理
    
    Args:
        error: 异常对象
        owner: 仓库所有者
        repo: 仓库名称
        show_progress: 是否显示详细错误提示
        
    Returns:
        错误描述字符串（ASCII 安全）
    """
    error_type = type(error).__name__
    error_str = str(error)
    
    # 处理 UnicodeEncodeError：安全转换错误消息
    try:
        # 尝试使用原始错误消息
        _ = error_str.encode('ascii')
    except UnicodeEncodeError:
        # 如果包含非 ASCII 字符，进行转换
        error_str = error_str.encode('ascii', 'replace').decode('ascii')
    
    if not show_progress:
        return f"{error_type}: {error_str}"
    
    # GitHub API 错误
    if "404" in error_str or "Not Found" in error_str:
        safe_print(f"❌ 仓库不存在: {owner}/{repo}")
        safe_print("   请检查：1) 仓库名拼写 2) 是否为私有仓库（需要Token）")
        return "仓库不存在(404)"
    
    elif "403" in error_str or "Forbidden" in error_str or "rate limit" in error_str.lower():
        safe_print(f"❌ 访问被拒绝: {owner}/{repo}")
        safe_print("   请检查：1) Token权限 2) API限流（GitHub限制：每小时60次，有Token为5000次）")
        safe_print("   建议：配置 GITHUB_TOKEN 环境变量以提高限额")
        return "访问被拒绝(403)"
    
    elif "401" in error_str or "Unauthorized" in error_str or "Bad credentials" in error_str:
        safe_print(f"❌ 认证失败")
        safe_print("   请检查：1) Token是否正确 2) Token是否过期")
        return "认证失败(401)"
    
    # 网络相关错误
    elif "timeout" in error_str.lower() or "timed out" in error_str.lower():
        safe_print(f"❌ 网络超时: {owner}/{repo}")
        safe_print("   建议：1) 检查网络连接 2) 稍后重试")
        return "网络超时"
    
    elif "connection" in error_str.lower():
        safe_print(f"❌ 网络连接失败")
        safe_print("   建议：1) 检查网络 2) 检查代理设置")
        return "网络连接失败"
    
    # 通用错误
    else:
        safe_print(f"❌ 加载失败: {error_type}: {error}")
        safe_print(f"   如果问题持续，请报告到项目 Issue")
        return f"{error_type}: {error_str}"


def parse_github_url(url: str) -> Optional[dict]:
    """解析 GitHub URL 获取仓库信息
    
    支持的格式：
    - https://github.com/owner/repo
    - github.com/owner/repo
    - http://github.com/owner/repo
    - https://github.com/owner/repo/tree/branch
    
    Args:
        url: GitHub URL
        
    Returns:
        包含 owner, repo, branch 的字典，解析失败返回 None
    """
    from urllib.parse import urlparse
    
    try:
        # 清理 URL
        url = url.strip()
        
        # 如果没有协议，自动添加 https://
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # 解析 URL
        parsed = urlparse(url)
        
        # 检查是否是 GitHub
        if 'github.com' not in parsed.netloc:
            logger.warning(f"不是有效的 GitHub URL: {url}")
            return None
        
        # 解析路径: /owner/repo 或 /owner/repo/tree/branch
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) < 2:
            logger.warning(f"URL 路径不完整: {url}")
            return None
        
        owner = path_parts[0]
        repo = path_parts[1]
        
        # 移除 .git 后缀（如果有）
        if repo.endswith('.git'):
            repo = repo[:-4]
        
        # 提取分支（如果 URL 中包含 /tree/branch）
        branch = None
        if len(path_parts) >= 4 and path_parts[2] == 'tree':
            branch = path_parts[3]
        
        result = {
            'owner': owner,
            'repo': repo,
            'branch': branch or 'main'  # 默认使用 main 分支
        }
        
        logger.info(f"解析 GitHub URL 成功: {result}")
        return result
        
    except Exception as e:
        logger.error(f"解析 GitHub URL 失败: {e}")
        return None


def load_documents_from_github_url(
    github_url: str,
    github_token: Optional[str] = None,
    clean: bool = True,
    show_progress: bool = True
) -> List[LlamaDocument]:
    """从 GitHub URL 加载文档（需要提供 Token）
    
    Args:
        github_url: GitHub 仓库 URL（如：https://github.com/owner/repo）
        github_token: GitHub Token（必需）
        clean: 是否清理文本
        show_progress: 是否显示进度条
        
    Returns:
        Document对象列表
        
    Examples:
        >>> docs = load_documents_from_github_url(
        ...     "https://github.com/microsoft/TypeScript",
        ...     github_token="ghp_xxxx"
        ... )
    
    Note:
        - GitHub Token 是必需的，无法使用匿名访问
        - 在 Web 界面中，Token 从用户数据中自动获取
        - 获取 Token：https://github.com/settings/tokens
    """
    # 解析 URL
    repo_info = parse_github_url(github_url)
    if not repo_info:
        logger.error(f"无法解析 GitHub URL: {github_url}")
        safe_print(f"❌ 无法解析 GitHub URL: {github_url}")
        return []
    
    # Token 必须提供
    if not github_token:
        error_msg = (
            "需要提供 GitHub Token。\n"
            "请在 Web 界面的 '🔑 GitHub Token 配置' 中保存您的 Token。\n"
            "获取 Token：https://github.com/settings/tokens"
        )
        if show_progress:
            safe_print(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    # 调用原有函数加载文档
    return load_documents_from_github(
        owner=repo_info['owner'],
        repo=repo_info['repo'],
        branch=repo_info['branch'],
        github_token=github_token,
        clean=clean,
        show_progress=show_progress
    )


def load_documents_from_wikipedia(
    pages: List[str],
    lang: str = "zh",
    auto_suggest: bool = True,
    clean: bool = True,
    show_progress: bool = True
) -> List[LlamaDocument]:
    """从维基百科加载文档（使用官方 WikipediaReader）
    
    Args:
        pages: 维基百科页面标题列表
        lang: 语言代码（zh=中文, en=英文）
        auto_suggest: 自动纠正页面标题拼写
        clean: 是否清理文本
        show_progress: 是否显示进度
        
    Returns:
        Document对象列表
        
    Examples:
        >>> docs = load_documents_from_wikipedia(["钱学森", "系统科学"], lang="zh")
        >>> docs = load_documents_from_wikipedia(["Systems science"], lang="en")
    """
    if WikipediaReader is None:
        safe_print("❌ 缺少依赖：llama-index-readers-wikipedia")
        safe_print("   安装：pip install llama-index-readers-wikipedia wikipedia")
        logger.error("WikipediaReader 未安装")
        return []
    
    if not pages:
        safe_print("⚠️  页面列表为空")
        return []
    
    try:
        if show_progress:
            safe_print(f"📖 正在从维基百科加载 {len(pages)} 个页面（语言: {lang}）...")
        
        logger.info(f"开始加载维基百科页面: {pages}, 语言: {lang}")
        
        # 使用 WikipediaReader 加载页面
        reader = WikipediaReader()
        
        # 批量加载页面
        documents = []
        iterator = tqdm(pages, desc="加载维基百科", unit="页") if show_progress else pages
        
        for page_title in iterator:
            try:
                page_docs = reader.load_data(
                    pages=[page_title],
                    lang=lang,
                    auto_suggest=auto_suggest
                )
                
                if page_docs:
                    documents.extend(page_docs)
                    if show_progress:
                        safe_print(f"✅ 已加载: {page_title}")
                else:
                    if show_progress:
                        safe_print(f"⚠️  未找到页面: {page_title}")
                    logger.warning(f"维基百科页面未找到: {page_title}")
                    
            except Exception as e:
                error_msg = str(e)
                if "does not match any pages" in error_msg or "Page id" in error_msg:
                    if show_progress:
                        safe_print(f"⚠️  页面不存在: {page_title}")
                    logger.warning(f"维基百科页面不存在: {page_title}")
                else:
                    if show_progress:
                        safe_print(f"❌ 加载失败: {page_title} - {error_msg}")
                    logger.error(f"加载维基百科页面失败 {page_title}: {e}")
        
        if not documents:
            if show_progress:
                safe_print("⚠️  未成功加载任何维基百科页面")
            logger.warning("没有成功加载任何维基百科页面")
            return []
        
        # 增强元数据：标识来源
        for doc in documents:
            # 获取页面标题（从元数据或文本中提取）
            page_title = doc.metadata.get('title', 'Unknown')
            
            # 构建维基百科 URL
            # 注意：URL 中的标题需要替换空格为下划线
            url_title = page_title.replace(' ', '_')
            wikipedia_url = f"https://{lang}.wikipedia.org/wiki/{url_title}"
            
            # 增强元数据
            doc.metadata.update({
                "source_type": "wikipedia",
                "language": lang,
                "wikipedia_url": wikipedia_url,
            })
            
            # 确保有标题
            if not doc.metadata.get('title'):
                doc.metadata['title'] = page_title
        
        if show_progress:
            safe_print(f"✅ 成功加载 {len(documents)} 个维基百科页面")
        
        logger.info(f"成功加载 {len(documents)} 个维基百科页面")
        
        # 可选的文本清理
        if clean:
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
        
    except Exception as e:
        safe_print(f"❌ 加载维基百科失败: {e}")
        logger.error(f"加载维基百科失败: {e}")
        return []


if __name__ == "__main__":
    # 测试代码
    from src.config import config
    
    safe_print("=== 测试文档加载器 ===")
    documents = load_documents_from_directory(config.RAW_DATA_PATH)
    safe_print(f"加载了 {len(documents)} 个文档")
    
    if documents:
        safe_print("\n第一个文档预览:")
        safe_print(f"标题: {documents[0].metadata.get('title')}")
        safe_print(f"内容长度: {len(documents[0].text)}")
        safe_print(f"内容预览: {documents[0].text[:200]}...")
