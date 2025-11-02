"""
数据加载器模块
使用 LlamaIndex 官方 Reader 组件，支持从多种数据源加载文档

架构：
- 数据来源层（data_source/）：从不同数据源获取文件路径
- 数据解析层（data_parser/）：统一使用 SimpleDirectoryReader 解析文件
- 兼容层（本模块）：提供向后兼容的函数接口
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
    from langchain_community.document_loaders import GitLoader
except ImportError:
    GitLoader = None

try:
    from src.git_repository_manager import GitRepositoryManager
except ImportError:
    GitRepositoryManager = None

# 新架构导入
from src.data_source import DataSource, GitHubSource, LocalFileSource, WebSource
from src.data_parser import DocumentParser

from src.logger import setup_logger
from src.config import config

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


def load_documents_from_source(
    source: DataSource,
    clean: bool = True,
    show_progress: bool = True,
    cache_manager=None,
    task_id: Optional[str] = None
) -> List[LlamaDocument]:
    """从数据源加载文档（统一入口函数）
    
    新架构的统一入口，整合数据来源层和解析层
    
    Args:
        source: 数据源对象（GitHubSource, LocalFileSource, WebSource等）
        clean: 是否清理文本
        show_progress: 是否显示进度
        cache_manager: 缓存管理器实例（可选）
        task_id: 任务ID（可选，用于缓存）
        
    Returns:
        文档列表
    """
    if not NEW_ARCHITECTURE_AVAILABLE:
        logger.error("新架构未可用")
        return []
    
    try:
        import time
        total_start_time = time.time()
        
        # 步骤1: 从数据源获取文件路径
        logger.info(f"开始从数据源获取文件路径 (source_type: {type(source).__name__})")
        if show_progress:
            safe_print(f"📂 正在获取文件路径...")
        
        source_start_time = time.time()
        # 如果是 GitHubSource，传递缓存管理器
        if isinstance(source, GitHubSource):
            source_files = source.get_file_paths(cache_manager=cache_manager, task_id=task_id)
        else:
            source_files = source.get_file_paths()
        source_elapsed = time.time() - source_start_time
        
        if not source_files:
            logger.warning("数据源未返回任何文件")
            if show_progress:
                safe_print("⚠️  未找到任何文件")
            return []
        
        logger.info(f"数据源返回 {len(source_files)} 个文件 (耗时: {source_elapsed:.2f}s)")
        if show_progress:
            safe_print(f"✅ 找到 {len(source_files)} 个文件")
        
        # 步骤2: 构建文件路径列表和元数据映射
        logger.debug("构建文件路径列表和元数据映射")
        file_paths = [sf.path for sf in source_files]
        # 构建元数据映射，确保包含 source_type（它是 SourceFile 的属性，不是 metadata 的一部分）
        metadata_map = {}
        for sf in source_files:
            metadata_map[sf.path] = {
                **sf.metadata,
                'source_type': sf.source_type  # 确保 source_type 包含在元数据中
            }
        logger.debug(f"元数据映射包含 {len(metadata_map)} 个条目")
        
        # 步骤3: 使用解析器解析文件
        if show_progress:
            safe_print(f"📄 正在解析文件...")
        
        parser_start_time = time.time()
        parser = DocumentParser()
        documents = parser.parse_files(
            file_paths, 
            metadata_map, 
            clean=clean,
            cache_manager=cache_manager,
            task_id=task_id
        )
        parser_elapsed = time.time() - parser_start_time
        
        if not documents:
            logger.warning(f"解析器未返回任何文档 (输入文件数: {len(file_paths)})")
            if show_progress:
                safe_print("⚠️  未能解析任何文档")
            return []
        
        logger.info(f"解析器返回 {len(documents)} 个文档 (耗时: {parser_elapsed:.2f}s)")
        
        # 步骤4: 可选的文本清理
        clean_elapsed = 0.0
        if clean:
            logger.debug("开始文本清理")
            clean_start_time = time.time()
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
            documents = cleaned_documents
            clean_elapsed = time.time() - clean_start_time
            logger.debug(f"文本清理完成 (耗时: {clean_elapsed:.2f}s)")
        else:
            logger.debug("跳过文本清理")
        
        total_elapsed = time.time() - total_start_time
        
        if show_progress:
            safe_print(f"✅ 成功加载 {len(documents)} 个文档")
        
        success_rate = (len(documents) / len(source_files) * 100) if source_files else 0
        logger.info(
            f"文档加载完成: "
            f"源文件数={len(source_files)}, "
            f"解析文档数={len(documents)}, "
            f"成功率={success_rate:.1f}%, "
            f"总耗时={total_elapsed:.2f}s "
            f"(获取路径={source_elapsed:.2f}s, "
            f"解析={parser_elapsed:.2f}s, "
            f"清理={clean_elapsed:.2f}s)"
        )
        
        return documents
        
    except Exception as e:
        logger.error(f"从数据源加载文档失败: {e}")
        if show_progress:
            safe_print(f"❌ 加载失败: {e}")
        return []


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
    # 使用新架构（如果可用）
    if NEW_ARCHITECTURE_AVAILABLE:
        try:
            source = LocalFileSource(
                source=directory_path,
                recursive=recursive
            )
            documents = load_documents_from_source(source, clean=clean, show_progress=True)
            
            # 应用扩展名过滤（如果需要）
            if required_exts and documents:
                filtered_docs = []
                for doc in documents:
                    file_path = doc.metadata.get('file_path', '')
                    if any(file_path.endswith(ext) for ext in required_exts):
                        filtered_docs.append(doc)
                documents = filtered_docs
            
            # 为 Markdown 文件提取标题（保持原有行为）
            for doc in documents:
                file_name = doc.metadata.get('file_name', '')
                if any(file_name.endswith(ext) for ext in ['.md', '.markdown']):
                    title = DocumentProcessor.extract_title_from_markdown(doc.text)
                    if not title:
                        title = Path(file_name).stem if file_name else "未命名"
                    doc.metadata.update({
                        "title": title,
                        "source_type": doc.metadata.get("source_type", "markdown"),
                    })
            
            return documents
        except Exception as e:
            logger.warning(f"新架构加载失败，回退到旧实现: {e}")
    
    # 回退到旧实现
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
    
    # 使用新架构（如果可用）
    if NEW_ARCHITECTURE_AVAILABLE:
        try:
            source = WebSource(urls=urls)
            documents = load_documents_from_source(source, clean=clean, show_progress=True)
            
            # 清理临时文件
            source.cleanup()
            
            return documents
        except Exception as e:
            logger.warning(f"新架构加载失败，回退到旧实现: {e}")
    
    # 回退到旧实现
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


def _build_file_filter(
    filter_directories: Optional[List[str]] = None,
    filter_file_extensions: Optional[List[str]] = None
):
    """构建文件过滤器函数
    
    将用户友好的参数格式转换为 LangChain GitLoader 需要的 lambda 函数
    
    Args:
        filter_directories: 只包含指定目录的文件（例如: ["docs", "examples"]）
        filter_file_extensions: 只包含指定扩展名的文件（例如: [".md", ".py"]）
        
    Returns:
        文件过滤器函数 file_filter(file_path: str) -> bool
    """
    def file_filter(file_path: str) -> bool:
        """判断文件是否应该被加载
        
        Args:
            file_path: 相对于仓库根目录的文件路径
            
        Returns:
            是否加载该文件
        """
        # 默认排除的目录和文件
        excluded_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.pytest_cache'}
        excluded_exts = {'.pyc', '.pyo', '.lock', '.log'}
        
        # 检查是否在排除目录中
        path_parts = file_path.split('/')
        if any(part in excluded_dirs for part in path_parts):
            return False
        
        # 检查是否是排除的扩展名
        if any(file_path.endswith(ext) for ext in excluded_exts):
            return False
        
        # 如果指定了目录过滤
        if filter_directories:
            if not any(file_path.startswith(d.rstrip('/') + '/') or file_path.startswith(d.rstrip('/')) 
                      for d in filter_directories):
                return False
        
        # 如果指定了扩展名过滤
        if filter_file_extensions:
            if not any(file_path.endswith(ext) for ext in filter_file_extensions):
                return False
        
        return True
    
    return file_filter


def _convert_langchain_to_llama_doc(
    lc_doc,
    owner: str,
    repo: str,
    branch: str
) -> LlamaDocument:
    """将 LangChain Document 转换为 LlamaIndex LlamaDocument
    
    Args:
        lc_doc: LangChain Document 对象
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名称
        
    Returns:
        LlamaDocument 对象
    """
    # 从 LangChain Document 提取信息
    file_path = lc_doc.metadata.get('file_path', lc_doc.metadata.get('source', ''))
    file_name = lc_doc.metadata.get('file_name', '')
    
    # 如果没有 file_name，从 file_path 中提取
    if not file_name and file_path:
        file_name = file_path.split('/')[-1]
    
    # 构建 LlamaDocument
    return LlamaDocument(
        text=lc_doc.page_content,
        metadata={
            'file_path': file_path,
            'file_name': file_name,
            'source': lc_doc.metadata.get('source', ''),
            'source_type': 'github',
            'repository': f"{owner}/{repo}",
            'branch': branch,
            'url': f"https://github.com/{owner}/{repo}/blob/{branch}/{file_path}",
        },
        id_=f"github_{owner}_{repo}_{branch}_{file_path}"
    )


def load_documents_from_github(owner: str,
                               repo: str,
                               branch: Optional[str] = None,
                               clean: bool = True,
                               show_progress: bool = True,
                               filter_directories: Optional[List[str]] = None,
                               filter_file_extensions: Optional[List[str]] = None) -> List[LlamaDocument]:
    """从GitHub仓库加载文档（使用 LangChain GitLoader + 本地 Git 克隆）
    
    仅支持公开仓库。
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名称（可选，默认 main）
        clean: 是否清理文本
        show_progress: 是否显示进度条
        filter_directories: 只加载指定目录（列表格式，如 ["docs", "examples"]）
        filter_file_extensions: 只加载指定扩展名（列表格式，如 [".md", ".py"]）
        
    Returns:
        Document对象列表
        
    Notes:
        - 首次加载会克隆仓库到本地（data/github_repos/），后续使用 git pull 增量更新
        - 仅支持公开仓库，不支持私有仓库
        - 默认会过滤掉 .git/, __pycache__, .pyc 等文件
    """
    # 使用新架构（如果可用）
    if NEW_ARCHITECTURE_AVAILABLE:
        try:
            # 初始化缓存管理器（如果启用缓存）
            cache_manager = None
            task_id = None
            from src.config import config
            if config.ENABLE_CACHE:
                try:
                    from src.cache_manager import CacheManager
                    cache_manager = CacheManager(config.CACHE_STATE_PATH)
                    task_id = cache_manager.get_task_id(
                        owner=owner,
                        repo=repo,
                        branch=branch or "main",
                        filter_directories=filter_directories,
                        filter_file_extensions=filter_file_extensions
                    )
                    task_key = cache_manager.get_task_key(owner, repo, branch or "main")
                    cache_manager.init_task(task_id, task_key)
                    logger.info(f"初始化缓存任务: {task_id} ({task_key})")
                except Exception as e:
                    logger.warning(f"初始化缓存管理器失败，继续不使用缓存: {e}")
            
            source = GitHubSource(
                owner=owner,
                repo=repo,
                branch=branch,
                filter_directories=filter_directories,
                filter_file_extensions=filter_file_extensions,
                show_progress=show_progress
            )
            documents = load_documents_from_source(
                source, 
                clean=clean, 
                show_progress=show_progress,
                cache_manager=cache_manager,
                task_id=task_id
            )
            return documents
        except Exception as e:
            logger.warning(f"新架构加载失败，回退到旧实现: {e}")
    
    # 回退到旧实现
    if GitLoader is None:
        safe_print("❌ 缺少依赖：langchain-community")
        safe_print("   安装：pip install langchain-community")
        logger.error("GitLoader 未安装")
        return []
    
    if GitRepositoryManager is None:
        safe_print("❌ GitRepositoryManager 未安装")
        logger.error("GitRepositoryManager 未安装")
        return []
    
    try:
        branch = branch or "main"
        logger.info(f"开始加载 GitHub 仓库: {owner}/{repo}, 分支: {branch}")
        
        if show_progress:
            safe_print(f"📦 正在从 GitHub 加载 {owner}/{repo} (分支: {branch})...")
        
        # 步骤 1: 使用 GitRepositoryManager 克隆或更新仓库
        git_manager = GitRepositoryManager(config.GITHUB_REPOS_PATH)
        
        if show_progress:
            safe_print(f"🔄 正在克隆/更新仓库到本地...")
        
        try:
            repo_path, commit_sha = git_manager.clone_or_update(
                owner=owner,
                repo=repo,
                branch=branch
            )
            logger.info(f"仓库路径: {repo_path}, Commit: {commit_sha[:8]}")
            
            if show_progress:
                safe_print(f"✅ 仓库已同步 (Commit: {commit_sha[:8]})")
                
        except RuntimeError as e:
            error_msg = str(e)
            if show_progress:
                safe_print(f"❌ Git 操作失败: {error_msg}")
            logger.error(f"Git 操作失败: {error_msg}")
            return []
        
        # 步骤 2: 构建文件过滤器
        file_filter = _build_file_filter(filter_directories, filter_file_extensions)
        
        # 步骤 3: 使用 LangChain GitLoader 加载文档
        if show_progress:
            safe_print(f"📄 正在加载文档...")
        
        try:
            loader = GitLoader(
                repo_path=str(repo_path),
                branch=branch,
                file_filter=file_filter
            )
            
            lc_documents = loader.load()
            
        except Exception as e:
            error_msg = str(e)
            if show_progress:
                safe_print(f"❌ 加载文档失败: {error_msg}")
            logger.error(f"GitLoader 加载失败: {error_msg}")
            return []
        
        if not lc_documents:
            logger.warning(f"仓库 {owner}/{repo} 没有文档")
            if show_progress:
                safe_print(f"⚠️  仓库为空或没有符合过滤条件的文件")
            return []
        
        if show_progress:
            safe_print(f"找到 {len(lc_documents)} 个文件")
        
        # 步骤 4: 转换 LangChain Document -> LlamaIndex LlamaDocument
        iterator = tqdm(lc_documents, desc="转换文档", unit="个") if show_progress else lc_documents
        
        processed_docs = []
        for lc_doc in iterator:
            try:
                llama_doc = _convert_langchain_to_llama_doc(lc_doc, owner, repo, branch)
                processed_docs.append(llama_doc)
            except Exception as e:
                logger.warning(f"转换文档失败: {e}, 跳过该文档")
                continue
        
        if show_progress:
            safe_print(f"✅ 成功加载 {len(processed_docs)} 个文件")
        
        logger.info(f"成功加载 {len(processed_docs)} 个文件从 {owner}/{repo}")
        
        # 步骤 5: 可选的文本清理
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
    show_progress: bool = True,
    filter_directories: Optional[List[str]] = None,
    filter_file_extensions: Optional[List[str]] = None
) -> tuple:
    """增量同步 GitHub 仓库（仅支持公开仓库）
    
    使用两级检测机制：
    1. 快速检测：比较 commit SHA，无变化直接跳过
    2. 精细检测：文件级哈希比对，只索引变更文件
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名称
        metadata_manager: 元数据管理器实例
        show_progress: 是否显示进度
        filter_directories: 只加载指定目录（可选）
        filter_file_extensions: 只加载指定扩展名（可选）
        
    Returns:
        (所有文档列表, FileChange对象, commit_sha, cache_manager, task_id)
    """
    from src.metadata_manager import FileChange
    
    # 初始化缓存管理器（如果启用缓存）
    cache_manager = None
    task_id = None
    if config.ENABLE_CACHE:
        try:
            from src.cache_manager import CacheManager
            cache_manager = CacheManager(config.CACHE_STATE_PATH)
            task_id = cache_manager.get_task_id(
                owner=owner,
                repo=repo,
                branch=branch,
                filter_directories=filter_directories,
                filter_file_extensions=filter_file_extensions
            )
            task_key = cache_manager.get_task_key(owner, repo, branch)
            cache_manager.init_task(task_id, task_key)
            logger.info(f"初始化缓存任务: {task_id} ({task_key})")
        except Exception as e:
            logger.warning(f"初始化缓存管理器失败，继续不使用缓存: {e}")
    
    # 步骤 1: 克隆/更新仓库，获取最新 commit SHA
    if GitRepositoryManager is None:
        logger.error("GitRepositoryManager 未安装")
        return [], FileChange(), None, cache_manager, task_id
    
    try:
        git_manager = GitRepositoryManager(config.GITHUB_REPOS_PATH)
        repo_path, commit_sha = git_manager.clone_or_update(
            owner=owner,
            repo=repo,
            branch=branch,
            cache_manager=cache_manager,
            task_id=task_id
        )
        
        if show_progress:
            safe_print(f"✅ 仓库已同步 (Commit: {commit_sha[:8]})")
        
    except RuntimeError as e:
        logger.error(f"Git 操作失败: {e}")
        if show_progress:
            safe_print(f"❌ Git 操作失败: {e}")
        return [], FileChange(), None, cache_manager, task_id
    
    # 步骤 2: 快速检测 - 检查 commit SHA 是否变化
    old_metadata = metadata_manager.get_repository_metadata(owner, repo, branch)
    
    if old_metadata:
        old_commit_sha = old_metadata.get('last_commit_sha', '')
        if old_commit_sha == commit_sha:
            # Commit 未变化，跳过加载
            if show_progress:
                safe_print(f"✅ 仓库无新提交，跳过加载")
            logger.info(f"仓库 {owner}/{repo}@{branch} 无新提交 (Commit: {commit_sha[:8]})")
            return [], FileChange(), commit_sha, cache_manager, task_id
    
    # 步骤 3: 有新提交，加载文档
    if show_progress:
        safe_print(f"\n📄 检测到新提交，正在加载文档...")
    
    documents = load_documents_from_github(
        owner=owner,
        repo=repo,
        branch=branch,
        clean=True,
        show_progress=show_progress,
        filter_directories=filter_directories,
        filter_file_extensions=filter_file_extensions
    )
    
    if not documents:
        logger.warning(f"未能加载任何文档从 {owner}/{repo}")
        return [], FileChange(), commit_sha, cache_manager, task_id
    
    # 步骤 4: 精细检测 - 文件级变更
    if show_progress:
        safe_print(f"\n🔍 正在检测文件变更...")
    
    changes = metadata_manager.detect_changes(owner, repo, branch, documents)
    
    if show_progress:
        if changes.has_changes():
            safe_print(f"📊 检测结果: {changes.summary()}")
        else:
            safe_print(f"✅ 没有检测到文件变更")
    
    return documents, changes, commit_sha, cache_manager, task_id


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
    clean: bool = True,
    show_progress: bool = True
) -> List[LlamaDocument]:
    """从 GitHub URL 加载文档（仅支持公开仓库）
    
    Args:
        github_url: GitHub 仓库 URL（如：https://github.com/owner/repo）
        clean: 是否清理文本
        show_progress: 是否显示进度条
        
    Returns:
        Document对象列表
        
    Examples:
        >>> docs = load_documents_from_github_url(
        ...     "https://github.com/microsoft/TypeScript"
        ... )
    
    Note:
        - 仅支持公开仓库
        - 私有仓库将无法访问
    """
    # 解析 URL
    repo_info = parse_github_url(github_url)
    if not repo_info:
        logger.error(f"无法解析 GitHub URL: {github_url}")
        safe_print(f"❌ 无法解析 GitHub URL: {github_url}")
        return []
    
    # 调用原有函数加载文档
    return load_documents_from_github(
        owner=repo_info['owner'],
        repo=repo_info['repo'],
        branch=repo_info['branch'],
        clean=clean,
        show_progress=show_progress
    )


"""
数据加载器模块 - 向后兼容层
已模块化拆分，此文件保持向后兼容
"""

# 从新模块导入所有公开接口
from src.data_loader import (
    DocumentProcessor,
    safe_print,
    load_documents_from_source,
    load_documents_from_directory,
    load_documents_from_urls,
    load_documents_from_github,
    load_documents_from_github_url,
    sync_github_repository,
    parse_github_url,
)

__all__ = [
    'DocumentProcessor',
    'safe_print',
    'load_documents_from_source',
    'load_documents_from_directory',
    'load_documents_from_urls',
    'load_documents_from_github',
    'load_documents_from_github_url',
    'sync_github_repository',
    'parse_github_url',
]
