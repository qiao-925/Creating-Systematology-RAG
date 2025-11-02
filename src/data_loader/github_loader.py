"""
GitHub加载器模块
从GitHub仓库加载文档
"""

from typing import List, Optional

from tqdm import tqdm
from llama_index.core.schema import Document as LlamaDocument

try:
    from langchain_community.document_loaders import GitLoader
except ImportError:
    GitLoader = None

try:
    from src.git_repository_manager import GitRepositoryManager
except ImportError:
    GitRepositoryManager = None

from src.config import config
from src.data_source import GitHubSource
from src.data_loader.processor import DocumentProcessor, safe_print
from src.data_loader.source_loader import load_documents_from_source, NEW_ARCHITECTURE_AVAILABLE
from src.data_loader.github_utils import (
    build_file_filter,
    convert_langchain_to_llama_doc,
    handle_github_error
)
from src.logger import setup_logger

logger = setup_logger('data_loader')


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
    """
    # 使用新架构（如果可用）
    if NEW_ARCHITECTURE_AVAILABLE:
        try:
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
        file_filter = build_file_filter(filter_directories, filter_file_extensions)
        
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
                llama_doc = convert_langchain_to_llama_doc(lc_doc, owner, repo, branch)
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
        error_msg = handle_github_error(e, owner, repo, show_progress)
        # 安全记录日志（处理 Unicode 编码问题）
        try:
            logger.error(f"加载失败 {owner}/{repo}: {error_msg}")
        except UnicodeEncodeError:
            safe_error_msg = error_msg.encode('ascii', 'replace').decode('ascii')
            logger.error(f"加载失败 {owner}/{repo}: {safe_error_msg}")
        return []


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
    """
    from src.data_loader.github_url import parse_github_url
    
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

