"""
文件查看工具函数
提供文件路径解析和文件内容显示的工具函数

主要功能：
- resolve_file_path()：解析文件路径，支持相对路径、绝对路径和仅文件名
- get_relative_path()：获取文件相对于项目根目录的相对路径
- display_file_info()：显示文件信息（文件名、路径、复制功能）
- display_markdown_file()：显示Markdown文件内容
- display_pdf_file()：显示PDF文件内容
- show_file_viewer_dialog()：显示文件查看弹窗（使用 @st.dialog 装饰器）

注意：页面版本 render_file_viewer_page() 已删除，所有文件查看功能通过弹窗实现
"""

import streamlit as st
from pathlib import Path
from typing import Optional
from src.infrastructure.config import config
from frontend.config import get_file_search_paths


def resolve_file_path(file_path_str: str) -> Optional[Path]:
    """解析文件路径，支持相对路径、绝对路径和仅文件名
    
    Args:
        file_path_str: 文件路径字符串（可能是相对路径、绝对路径或仅文件名）
        
    Returns:
        Path对象（绝对路径），如果文件不存在则返回None
    """
    if not file_path_str:
        return None
    
    # 转换为Path对象
    file_path = Path(file_path_str)
    
    # 如果是绝对路径，直接返回
    if file_path.is_absolute():
        if file_path.exists():
            return file_path
        return None
    
    # 如果是相对路径，尝试多个可能的根目录
    # 首先尝试直接路径匹配
    possible_roots = get_file_search_paths()
    for root in possible_roots:
        if not root.exists():
            continue
        full_path = root / file_path
        if full_path.exists():
            return full_path
    
    # 如果直接路径匹配失败，且路径看起来像文件名（没有路径分隔符），尝试递归搜索
    if '/' not in file_path_str and '\\' not in file_path_str:
        file_name = file_path.name
        for root in possible_roots:
            if not root.exists():
                continue
            # 递归搜索文件
            found_files = list(root.rglob(file_name))
            if found_files:
                # 返回第一个找到的文件
                return found_files[0]
    
    # 尝试直接相对于项目根目录
    full_path = config.PROJECT_ROOT / file_path
    if full_path.exists():
        return full_path
    
    return None


def get_relative_path(file_path: Path) -> Optional[str]:
    """获取文件相对于项目根目录的相对路径
    
    Args:
        file_path: 文件的绝对路径
        
    Returns:
        相对路径字符串，如果文件不在项目根目录下则返回绝对路径
    """
    try:
        # 尝试计算相对路径
        relative = file_path.relative_to(config.PROJECT_ROOT)
        return str(relative)
    except ValueError:
        # 如果文件不在项目根目录下，返回绝对路径
        return str(file_path)


def display_file_info(file_path: Path) -> None:
    """显示文件信息（文件名、路径、复制功能）
    
    Args:
        file_path: 文件路径对象
    """
    # 文件名
    st.markdown(f"### {file_path.name}")
    
    # 相对路径
    relative_path = get_relative_path(file_path)
    if relative_path and relative_path != str(file_path):
        st.caption(f"📁 {relative_path}")
    
    # 完整路径（可折叠）
    with st.expander("📋 查看完整路径", expanded=False):
        st.code(str(file_path), language=None)
        # Streamlit 的 st.code 自带复制功能


def display_markdown_file(file_path: Path) -> None:
    """显示Markdown文件内容
    
    Args:
        file_path: 文件路径对象
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        st.markdown(content)
    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
            st.markdown(content)
        except Exception as e:
            st.error(f"❌ 读取文件失败: {e}")
    except Exception as e:
        st.error(f"❌ 读取文件失败: {e}")


def display_pdf_file(file_path: Path) -> None:
    """显示PDF文件内容
    
    Args:
        file_path: 文件路径对象
    """
    try:
        # 读取PDF文件并转换为base64
        import base64
        
        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()
        
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # 使用iframe显示PDF（使用 Streamlit 原生样式）
        pdf_display = f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}" 
                width="100%" 
                height="800px" 
                style="border: 1px solid #E5E5E0; border-radius: 8px;">
        </iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        # 同时提供下载链接
        st.download_button(
            label="📥 下载PDF文件",
            data=pdf_bytes,
            file_name=file_path.name,
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"❌ 读取PDF文件失败: {e}")
        st.info("💡 提示：如果PDF文件较大，可能需要一些时间加载")


@st.dialog("📄 文件查看", width="large")
def show_file_viewer_dialog(file_path_str: str) -> None:
    """显示文件查看弹窗
    
    Args:
        file_path_str: 文件路径字符串
    """
    # 解析文件路径
    file_path = resolve_file_path(file_path_str)
    
    if not file_path:
        st.error(f"❌ 文件不存在: {file_path_str}")
        st.info("💡 提示：文件可能已被移动或删除")
        
        # 显示搜索路径信息（帮助调试）
        with st.expander("🔍 搜索路径信息", expanded=False):
            st.text("已搜索以下目录：")
            for root in get_file_search_paths():
                exists = "✅" if root.exists() else "❌"
                st.text(f"  {exists} {root}")
        return
    
    if not file_path.exists():
        st.error(f"❌ 文件不存在: {file_path}")
        return
    
    # 显示文件信息
    display_file_info(file_path)
    
    st.divider()
    
    # 根据文件类型显示内容
    file_ext = file_path.suffix.lower()
    
    if file_ext == '.md' or file_ext == '.markdown':
        # Markdown文件
        display_markdown_file(file_path)
    elif file_ext == '.pdf':
        # PDF文件
        display_pdf_file(file_path)
    else:
        # 其他文件类型，尝试作为文本显示
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            st.code(content, language='text')
        except:
            st.warning(f"⚠️  不支持的文件类型: {file_ext}")
            st.info("💡 当前仅支持Markdown和PDF文件查看")
            
            # 提供下载链接
            try:
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()
                st.download_button(
                    label="📥 下载文件",
                    data=file_bytes,
                    file_name=file_path.name,
                )
            except:
                pass



