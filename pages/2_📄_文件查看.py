"""
文件查看页面
支持查看Markdown和PDF文件的完整内容
"""

import streamlit as st
from pathlib import Path
import sys
import urllib.parse

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config

# 页面配置
st.set_page_config(
    page_title="文件查看",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def resolve_file_path(file_path_str: str) -> Path:
    """解析文件路径，支持相对路径和绝对路径
    
    Args:
        file_path_str: 文件路径字符串（可能是相对路径或绝对路径）
        
    Returns:
        Path对象（绝对路径）
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
    possible_roots = [
        config.PROJECT_ROOT,
        config.RAW_DATA_PATH,
        config.PROCESSED_DATA_PATH,
        config.PROJECT_ROOT / "data" / "github_repos",
        config.PROJECT_ROOT / "data" / "raw",
    ]
    
    for root in possible_roots:
        full_path = root / file_path
        if full_path.exists():
            return full_path
    
    # 尝试直接相对于项目根目录
    full_path = config.PROJECT_ROOT / file_path
    if full_path.exists():
        return full_path
    
    return None

def display_markdown_file(file_path: Path):
    """显示Markdown文件内容"""
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

def display_pdf_file(file_path: Path):
    """显示PDF文件内容"""
    try:
        # 读取PDF文件并转换为base64
        import base64
        
        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()
        
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # 使用iframe显示PDF
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

def main():
    """主函数"""
    st.title("📄 文件查看")
    
    # 从URL参数获取文件路径
    query_params = st.query_params
    file_path_str = query_params.get("path", None)
    
    if not file_path_str:
        st.info("💡 请从引用来源中点击文件标题链接访问此页面")
        st.markdown("---")
        st.markdown("### 使用说明")
        st.markdown("""
        1. 在聊天界面查看回答时，右侧会显示引用来源
        2. 点击引用来源的标题，即可查看完整文件内容
        3. 支持的文件格式：
           - Markdown (.md)
           - PDF (.pdf)
        """)
        return
    
    # 解码URL编码的文件路径
    try:
        file_path_str = urllib.parse.unquote(file_path_str)
    except:
        pass
    
    # 解析文件路径
    file_path = resolve_file_path(file_path_str)
    
    if not file_path:
        st.error(f"❌ 文件不存在: {file_path_str}")
        st.info("💡 提示：文件可能已被移动或删除")
        return
    
    if not file_path.exists():
        st.error(f"❌ 文件不存在: {file_path}")
        return
    
    # 显示文件信息
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {file_path.name}")
    with col2:
        st.caption(f"📁 {file_path.parent}")
    
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

# Streamlit多页面应用直接调用main()
main()

