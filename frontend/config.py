"""
前端配置模块
统一管理前端应用的配置设置

主要功能：
- configure_paths()：配置 Python 路径
- configure_encoding()：配置 UTF-8 编码
- configure_exit_hooks()：注册退出钩子
- configure_streamlit()：配置 Streamlit 页面
- configure_all()：统一调用所有配置函数
- get_file_search_paths()：获取文件搜索路径列表
- DEFAULT_QUESTIONS：快速开始默认问题列表
"""

import sys
import os
import atexit
from pathlib import Path
import streamlit as st

from frontend.utils.cleanup import cleanup_resources


def configure_paths() -> None:
    """配置 Python 路径
    
    将项目根目录添加到 sys.path，确保可以导入项目模块。
    必须在导入项目模块（如 backend.*）之前执行。
    """
    sys.path.insert(0, str(Path(__file__).parent.parent))


def configure_encoding() -> None:
    """配置 UTF-8 编码
    
    确保 emoji 和中文正确显示。
    优先使用 backend.infrastructure.encoding.setup_utf8_encoding()，
    如果导入失败，则手动设置环境变量。
    """
    try:
        from backend.infrastructure.encoding import setup_utf8_encoding
        setup_utf8_encoding()
    except ImportError:
        # 如果 encoding 模块尚未加载，手动设置基础编码
        os.environ["PYTHONIOENCODING"] = "utf-8"


def configure_exit_hooks() -> None:
    """配置退出钩子
    
    注册应用退出时的资源清理函数。
    确保 Chroma 客户端和后台线程被正确终止。
    """
    atexit.register(cleanup_resources)


def configure_streamlit() -> None:
    """配置 Streamlit 页面
    
    设置页面标题、图标、布局等参数。
    必须在任何 Streamlit 调用前执行，且只能执行一次。
    """
    st.set_page_config(
        page_title="Creating Systematology RAG",
        page_icon="✨",
    )


def get_file_search_paths() -> list[Path]:
    """获取文件搜索路径列表
    
    返回用于文件搜索的所有可能根目录列表。
    用于文件查看器等组件中解析文件路径。
    
    Returns:
        文件搜索路径列表
    """
    from backend.infrastructure.config import config
    return [
        config.PROJECT_ROOT,
        config.RAW_DATA_PATH,
        config.PROCESSED_DATA_PATH,
        config.PROJECT_ROOT / "data" / "github_repos",
        config.PROJECT_ROOT / "data" / "raw",
        config.GITHUB_REPOS_PATH,
    ]


# 建议问题配置（用于 st.pills 显示）
# 格式：{显示标签: 实际问题}
USER_AVATAR = "🙂"
ASSISTANT_AVATAR = "🤖"

SUGGESTION_QUESTIONS = {
    "📚 什么是系统科学？": "什么是系统科学？它的核心思想是什么？",
    "👤 钱学森的贡献": "钱学森对系统科学有哪些贡献？",
    "🧩 综合集成法": "从定性到定量的综合集成法如何与马克思主义哲学结合起来理解？",
    "🛠️ 系统工程应用": "系统工程在现代科学中的应用有哪些？",
}
def configure_all() -> None:
    """配置所有应用设置
    
    按照正确的顺序执行所有配置：
    1. 路径配置（必须在导入项目模块前）
    2. 编码配置
    3. 退出钩子配置
    4. Streamlit 页面配置（必须在任何 Streamlit 调用前）
    
    注意：此函数必须在导入项目模块（如 backend.infrastructure.*）之前调用。
    """
    configure_paths()
    configure_encoding()
    configure_exit_hooks()
    configure_streamlit()

