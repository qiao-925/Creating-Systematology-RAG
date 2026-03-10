"""文件查看工具：路径解析 + Markdown/PDF 预览弹窗。"""

import streamlit as st
from pathlib import Path
from functools import lru_cache
from typing import Optional
from backend.infrastructure.config import config
from frontend.config import get_file_search_paths


def _iter_fallback_roots(possible_roots: list[Path]) -> list[Path]:
    """构造回退搜索根目录列表（去重，保持顺序）"""
    roots = list(possible_roots)
    roots.append(config.PROJECT_ROOT.parent)
    unique_roots: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        root_str = str(root.resolve()) if root.exists() else str(root)
        if root_str in seen:
            continue
        seen.add(root_str)
        unique_roots.append(root)
    return unique_roots


@lru_cache(maxsize=128)
def _search_filename_under_root(root_str: str, file_name: str) -> tuple[str, ...]:
    """在给定根目录下递归搜索文件名（带缓存）"""
    root = Path(root_str)
    if not root.exists():
        return ()
    try:
        return tuple(
            str(path)
            for path in root.rglob(file_name)
            if path.is_file()
        )
    except (OSError, PermissionError):
        return ()


def _suffix_match_score(candidate: Path, requested_parts: list[str]) -> int:
    """计算候选路径与请求路径从尾部开始的匹配段数"""
    candidate_parts = [part.lower() for part in candidate.parts if part]
    target_parts = [part.lower() for part in requested_parts if part]
    if not candidate_parts or not target_parts:
        return 0

    score = 0
    max_len = min(len(candidate_parts), len(target_parts))
    while score < max_len:
        if candidate_parts[-(score + 1)] != target_parts[-(score + 1)]:
            break
        score += 1
    return score


def resolve_file_path(file_path_str: str) -> Optional[Path]:
    """解析文件路径，支持相对路径、绝对路径和仅文件名
    
    Args:
        file_path_str: 文件路径字符串（可能是相对路径、绝对路径或仅文件名）
        
    Returns:
        Path对象（绝对路径），如果文件不存在则返回None
    """
    if not file_path_str:
        return None
    
    file_path = Path(file_path_str)
    if file_path.is_absolute():
        if file_path.exists():
            return file_path
        return None

    possible_roots = get_file_search_paths()
    for root in possible_roots:
        if not root.exists():
            continue
        full_path = root / file_path
        if full_path.exists():
            return full_path

    if '/' not in file_path_str and '\\' not in file_path_str:
        file_name = file_path.name
        for root in possible_roots:
            if not root.exists():
                continue
            found_files = list(root.rglob(file_name))
            if found_files:
                return found_files[0]

    full_path = config.PROJECT_ROOT / file_path
    if full_path.exists():
        return full_path

    # 兜底：按文件名递归搜索，优先匹配请求路径后缀
    file_name = file_path.name
    if file_name:
        requested_parts = [part for part in Path(file_path_str).parts if part not in (".",)]
        matched_files: list[Path] = []
        for root in _iter_fallback_roots(possible_roots):
            found = _search_filename_under_root(str(root), file_name)
            matched_files.extend(Path(path_str) for path_str in found)

        if matched_files:
            dedup: dict[str, Path] = {}
            for path in matched_files:
                dedup[str(path)] = path
            unique_matches = list(dedup.values())
            if len(unique_matches) == 1:
                return unique_matches[0]
            ranked = sorted(
                unique_matches,
                key=lambda p: (-_suffix_match_score(p, requested_parts), len(str(p))),
            )
            best = ranked[0]
            best_score = _suffix_match_score(best, requested_parts)
            if best_score > 0:
                return best
            return ranked[0]
    
    return None


def get_relative_path(file_path: Path) -> Optional[str]:
    """获取文件相对于项目根目录的相对路径
    
    Args:
        file_path: 文件的绝对路径
    """
    try:
        relative = file_path.relative_to(config.PROJECT_ROOT)
        return str(relative)
    except ValueError:
        return str(file_path)


def display_file_info(file_path: Path) -> None:
    """显示文件信息（文件名、路径、复制功能）
    
    Args:
        file_path: 文件路径对象
    """
    st.markdown(f"### {file_path.name}")
    relative_path = get_relative_path(file_path)
    if relative_path and relative_path != str(file_path):
        st.caption(f"📁 {relative_path}")
    with st.expander("📋 查看完整路径", expanded=False):
        st.code(str(file_path), language=None)


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
        import base64
        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}" 
                width="100%" 
                height="800px" 
                style="border: 1px solid #4A4A4A; border-radius: 8px;">
        </iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
        st.download_button(
            label="📥 下载PDF文件",
            data=pdf_bytes,
            file_name=file_path.name,
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"❌ 读取PDF文件失败: {e}")
        st.info("💡 提示：如果PDF文件较大，可能需要一些时间加载")


@st.dialog("文件查看", width="large", icon="📄")
def show_file_viewer_dialog(file_path_str: str) -> None:
    """显示文件查看弹窗
    
    Args:
        file_path_str: 文件路径字符串
    """
    file_path = resolve_file_path(file_path_str)
    if not file_path:
        st.error(f"❌ 文件不存在: {file_path_str}")
        st.info("💡 提示：文件可能已被移动或删除")
        with st.expander("🔍 搜索路径信息", expanded=False):
            st.text("已搜索以下目录：")
            for root in get_file_search_paths():
                exists = "✅" if root.exists() else "❌"
                st.text(f"  {exists} {root}")
        return
    if not file_path.exists():
        st.error(f"❌ 文件不存在: {file_path}")
        return
    display_file_info(file_path)
    st.divider()
    file_ext = file_path.suffix.lower()
    if file_ext == '.md' or file_ext == '.markdown':
        display_markdown_file(file_path)
    elif file_ext == '.pdf':
        display_pdf_file(file_path)
    else:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            st.code(content, language='text')
        except:
            st.warning(f"⚠️  不支持的文件类型: {file_ext}")
            st.info("💡 当前仅支持Markdown和PDF文件查看")
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

