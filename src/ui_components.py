"""
UI共用组件模块
提供Streamlit应用中可复用的UI组件和函数
"""

import streamlit as st
from pathlib import Path
from typing import Optional

from src.config import config
from src.indexer import IndexManager, get_embedding_model_status, get_global_embed_model, load_embedding_model
from src.chat_manager import ChatManager
from src.query_engine import HybridQueryEngine
from src.business.services import RAGService
from src.logger import setup_logger

logger = setup_logger('ui_components')


def preload_embedding_model():
    """预加载 Embedding 模型（仅加载一次）"""
    if 'embed_model' not in st.session_state:
        st.session_state.embed_model = None
    
    if 'embed_model_loaded' not in st.session_state:
        st.session_state.embed_model_loaded = False
    
    # 如果已经加载过，直接返回（检查session_state中的模型）
    if st.session_state.embed_model_loaded and st.session_state.embed_model is not None:
        # 确保全局变量也有模型引用
        from src.indexer import set_global_embed_model
        set_global_embed_model(st.session_state.embed_model)
        return
    
    # 检查是否已经有全局模型
    global_model = get_global_embed_model()
    
    if global_model is None:
        # 模型未加载，开始加载
        with st.spinner(f"🚀 正在预加载 Embedding 模型 ({config.EMBEDDING_MODEL})..."):
            try:
                model = load_embedding_model()
                # 同时存储到session_state和全局变量
                st.session_state.embed_model = model
                st.session_state.embed_model_loaded = True
                st.success("✅ Embedding 模型预加载完成")
            except Exception as e:
                st.error(f"❌ 模型加载失败: {e}")
                st.stop()
    else:
        # 模型已加载（存储到session_state）
        st.session_state.embed_model = global_model
        st.session_state.embed_model_loaded = True


def init_session_state():
    """初始化会话状态"""
    # 用户管理
    if 'user_manager' not in st.session_state:
        from src.user_manager import UserManager
        st.session_state.user_manager = UserManager()
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    
    if 'collection_name' not in st.session_state:
        st.session_state.collection_name = None
    
    # 索引和对话管理
    if 'index_manager' not in st.session_state:
        st.session_state.index_manager = None
    
    if 'chat_manager' not in st.session_state:
        st.session_state.chat_manager = None
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'index_built' not in st.session_state:
        st.session_state.index_built = False
    
    # 维基百科配置
    if 'enable_wikipedia' not in st.session_state:
        st.session_state.enable_wikipedia = config.ENABLE_WIKIPEDIA
    
    if 'wikipedia_threshold' not in st.session_state:
        st.session_state.wikipedia_threshold = config.WIKIPEDIA_THRESHOLD
    
    if 'hybrid_query_engine' not in st.session_state:
        st.session_state.hybrid_query_engine = None
    
    # 默认登录账号（方便测试）
    if 'login_email' not in st.session_state:
        st.session_state.login_email = "test@example.com"
    
    if 'login_password' not in st.session_state:
        st.session_state.login_password = "123456"
    
    # GitHub 增量更新相关
    if 'metadata_manager' not in st.session_state:
        from src.metadata_manager import MetadataManager
        st.session_state.metadata_manager = MetadataManager(config.GITHUB_METADATA_PATH)
    
    if 'github_repos' not in st.session_state:
        # 从元数据中加载已存在的仓库列表
        st.session_state.github_repos = st.session_state.metadata_manager.list_repositories()
    
    # 调试模式与可观测性（默认开启）
    if 'debug_mode_enabled' not in st.session_state:
        st.session_state.debug_mode_enabled = True
    
    if 'phoenix_enabled' not in st.session_state:
        st.session_state.phoenix_enabled = True
    
    if 'collect_trace' not in st.session_state:
        st.session_state.collect_trace = True
    
    # RAG服务（新架构）
    if 'rag_service' not in st.session_state:
        st.session_state.rag_service = None
    
    # 启动遮罩：首屏加载完成前为 False，完成后置 True
    if 'boot_ready' not in st.session_state:
        st.session_state.boot_ready = False


def load_rag_service() -> Optional[RAGService]:
    """加载或创建RAG服务（新架构推荐）
    
    Returns:
        Optional[RAGService]: RAG服务实例，失败返回None
    """
    try:
        if st.session_state.rag_service is None:
            # 使用用户专属的 collection
            if not st.session_state.collection_name:
                raise ValueError("未登录或 collection_name 未设置，请先登录")
            collection_name = st.session_state.collection_name
            
            with st.spinner("🔧 初始化RAG服务..."):
                st.session_state.rag_service = RAGService(
                    collection_name=collection_name,
                    enable_debug=st.session_state.get('debug_mode_enabled', False),
                    enable_markdown_formatting=True,
                )
                st.success("✅ RAG服务已初始化")
        
        return st.session_state.rag_service
    except Exception as e:
        st.error(f"❌ RAG服务初始化失败: {e}")
        logger.error(f"RAG服务初始化失败: {e}", exc_info=True)
        return None


def load_index():
    """加载或创建索引（向后兼容）"""
    try:
        if st.session_state.index_manager is None:
            # 使用用户专属的 collection（登录后必须有 collection_name）
            if not st.session_state.collection_name:
                raise ValueError("未登录或 collection_name 未设置，请先登录")
            collection_name = st.session_state.collection_name
            
            # 获取预加载的模型实例
            embed_model = get_global_embed_model()
            
            with st.spinner("🔧 初始化索引管理器..."):
                # 传递预加载的模型实例，避免重复加载
                st.session_state.index_manager = IndexManager(
                    collection_name=collection_name,
                    embed_model_instance=embed_model
                )
                st.success("✅ 索引管理器已初始化")
        
        return st.session_state.index_manager
    except Exception as e:
        st.error(f"❌ 索引初始化失败: {e}")
        return None


def load_chat_manager():
    """加载或创建对话管理器"""
    try:
        # 尝试加载索引管理器（可能为空）
        index_manager = load_index() if st.session_state.index_built else None
        
        if st.session_state.chat_manager is None:
            mode_desc = "RAG增强模式" if index_manager else "纯对话模式（无知识库）"
            with st.spinner(f"🤖 初始化对话管理器 ({mode_desc})..."):
                st.session_state.chat_manager = ChatManager(
                    index_manager,
                    enable_debug=st.session_state.debug_mode_enabled,
                    user_email=st.session_state.user_email
                )
                # 不在这里创建会话，等第一次提问时再创建
                st.success(f"✅ 对话管理器已初始化 ({mode_desc})")
        
        return st.session_state.chat_manager
    except ValueError as e:
        st.error(f"❌ 请先设置DEEPSEEK_API_KEY环境变量")
        st.info("💡 提示：在项目根目录创建.env文件，添加：DEEPSEEK_API_KEY=your_api_key")
        return None
    except Exception as e:
        st.error(f"❌ 对话管理器初始化失败: {e}")
        return None




def format_answer_with_citation_links(answer: str, sources: list, message_id: str = None) -> str:
    """将答案中的引用标签[1][2][3]转换为可点击的超链接（锚定到右侧引用来源）
    
    Args:
        answer: 包含引用标签的答案文本
        sources: 引用来源列表
        message_id: 消息唯一ID（用于生成锚点）
        
    Returns:
        处理后的HTML字符串（包含可点击的引用链接）
    """
    import re
    import uuid
    
    if not message_id:
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
    
    # 提取所有引用标签 [1], [2], [3] 等
    citation_pattern = r'\[(\d+)\]'
    
    def replace_citation(match):
        citation_num = int(match.group(1))
        citation_id = f"citation_{message_id}_{citation_num}"
        
        # 检查该引用是否存在
        if citation_num <= len(sources):
            # 创建可点击的链接，锚定到右侧引用来源面板
            return f'<a href="#{citation_id}" onclick="event.preventDefault(); scrollToCitation(\'{citation_id}\'); return false;" style="color: #2563EB; text-decoration: none; font-weight: 500; cursor: pointer;" title="点击查看引用来源 {citation_num}">[{citation_num}]</a>'
        else:
            # 引用不存在，保持原样
            return match.group(0)
    
    # 替换所有引用标签
    formatted_answer = re.sub(citation_pattern, replace_citation, answer)
    
    # 添加JavaScript代码用于滚动到右侧引用来源
    js_code = f"""
    <script>
    function scrollToCitation(citationId) {{
        // 滚动到右侧引用来源面板中对应的引用位置
        const element = document.getElementById(citationId);
        if (element) {{
            // 滚动到引用位置（右侧面板）
            element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            // 高亮效果
            element.style.backgroundColor = '#FFF9C4';
            element.style.border = '2px solid #2563EB';
            setTimeout(() => {{
                element.style.backgroundColor = '';
                element.style.border = '';
            }}, 2000);
        }} else {{
            // 如果找不到元素，等待一下再试（可能DOM还没渲染完成）
            setTimeout(() => {{
                const targetElement = document.getElementById(citationId);
                if (targetElement) {{
                    targetElement.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    targetElement.style.backgroundColor = '#FFF9C4';
                    targetElement.style.border = '2px solid #2563EB';
                    setTimeout(() => {{
                        targetElement.style.backgroundColor = '';
                        targetElement.style.border = '';
                    }}, 2000);
                }}
            }}, 100);
        }}
    }}
    </script>
    """
    
    return formatted_answer + js_code


def display_sources_with_anchors(sources: list, message_id: str = None, expanded: bool = True):
    """显示引用来源，每个来源都有唯一的锚点ID
    
    Args:
        sources: 引用来源列表
        message_id: 消息唯一ID（用于生成锚点）
        expanded: 是否默认展开
    """
    import uuid
    import urllib.parse
    
    if not message_id:
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
    
    if sources:
        with st.expander("📚 查看引用来源", expanded=expanded):
            for source in sources:
                citation_num = source.get('index', 0)
                citation_id = f"citation_{message_id}_{citation_num}"
                
                # 获取文件路径和标题（改进：尝试多种metadata字段）
                metadata = source.get('metadata', {})
                
                # 尝试多种方式获取文件路径
                file_path = (
                    metadata.get('file_path') or 
                    metadata.get('file_name') or 
                    metadata.get('source') or 
                    metadata.get('url') or
                    metadata.get('filename') or
                    ''
                )
                
                # 提取标题（优先使用title，否则使用文件名）
                title = (
                    metadata.get('title') or 
                    metadata.get('file_name') or 
                    metadata.get('filename') or
                    'Unknown'
                )
                
                # 如果title是路径，提取文件名作为显示标题
                if '/' in title or '\\' in title:
                    title = Path(title).name if title else 'Unknown'
                
                # 生成文件查看链接（只要file_path不为空就尝试生成）
                file_url = None
                if file_path:
                    file_url = get_file_viewer_url(file_path)
                
                # 构建标题HTML（如果文件路径存在，添加更明显的链接样式）
                if file_url:
                    # Streamlit pages路径：不编码页面名称，让浏览器自动处理；只编码查询参数
                    page_name = "2_📄_文件查看"  # Streamlit pages 目录下的文件名（不含.py）
                    encoded_path = urllib.parse.quote(str(file_path), safe='')
                    # 构建URL：页面路径不编码，查询参数编码
                    full_url = f"/{page_name}?path={encoded_path}"
                    title_html = (
                        f'<div id="{citation_id}" style="padding-top: 0.5rem; padding-bottom: 0.5rem;">'
                        f'<strong>'
                        f'<a href="{full_url}" '
                        f'style="'
                        f'color: var(--color-accent); '
                        f'text-decoration: underline; '
                        f'text-decoration-color: var(--color-accent); '
                        f'text-underline-offset: 3px; '
                        f'font-weight: 600; '
                        f'cursor: pointer; '
                        f'transition: all 0.2s ease;'
                        f'" '
                        f'onmouseover="this.style.color=\'var(--color-accent-hover)\'; this.style.textDecorationColor=\'var(--color-accent-hover)\';" '
                        f'onmouseout="this.style.color=\'var(--color-accent)\'; this.style.textDecorationColor=\'var(--color-accent)\';" '
                        f'title="点击查看完整文件">'
                        f'[{citation_num}] {title} 🔗'
                        f'</a>'
                        f'</strong>'
                        f'</div>'
                    )
                else:
                    title_html = (
                        f'<div id="{citation_id}" style="padding-top: 0.5rem; padding-bottom: 0.5rem;">'
                        f'<strong>[{citation_num}] {title}</strong>'
                        f'</div>'
                    )
                
                st.markdown(title_html, unsafe_allow_html=True)
                
                if source['score']:
                    st.caption(f"相似度: {source['score']:.2f}")
                
                st.text(source['text'])
                st.divider()


def get_file_viewer_url(file_path: str) -> str:
    """生成文件查看页面的URL
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件查看页面的URL（包含路径参数）
    """
    import urllib.parse
    
    if not file_path:
        return None
    
    # URL编码文件路径参数
    encoded_path = urllib.parse.quote(str(file_path), safe='')
    
    # Streamlit pages 目录下的文件路径格式
    # 文件名：2_📄_文件查看.py -> URL路径：/2_📄_文件查看
    # Streamlit 会自动处理 emoji 字符，浏览器也会自动编码
    # 但我们也可以手动编码以确保兼容性
    page_name = "2_📄_文件查看"
    # 对页面名称进行URL编码（包括emoji）
    encoded_page = urllib.parse.quote(page_name, safe='')
    
    return f"/{encoded_page}?path={encoded_path}"


def display_sources_right_panel(sources: list, message_id: str = None, container=None):
    """在右侧面板显示引用来源（固定位置，每个来源都有唯一的锚点ID）
    
    Args:
        sources: 引用来源列表
        message_id: 消息唯一ID（用于生成锚点）
        container: Streamlit容器对象（如column），如果为None则使用当前上下文
    """
    import uuid
    import urllib.parse
    
    if not message_id:
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
    
    if not sources:
        if container:
            with container:
                st.info("💡 暂无引用来源")
        else:
            st.info("💡 暂无引用来源")
        return
    
    # 使用传入的container或当前上下文
    context = container if container else st
    
    with context:
        # 使用st.container确保内容在右侧固定位置
        for source in sources:
            citation_num = source.get('index', 0)
            citation_id = f"citation_{message_id}_{citation_num}"
            
            # 获取文件路径和标题（改进：尝试多种metadata字段）
            metadata = source.get('metadata', {})
            
            # 尝试多种方式获取文件路径
            file_path = (
                metadata.get('file_path') or 
                metadata.get('file_name') or 
                metadata.get('source') or 
                metadata.get('url') or
                metadata.get('filename') or
                ''
            )
            
            # 提取标题（优先使用title，否则使用文件名）
            title = (
                metadata.get('title') or 
                metadata.get('file_name') or 
                metadata.get('filename') or
                'Unknown'
            )
            
            # 如果title是路径，提取文件名作为显示标题
            if '/' in title or '\\' in title:
                title = Path(title).name if title else 'Unknown'
            
            # 生成文件查看链接（只要file_path不为空就尝试生成）
            file_url = None
            if file_path:
                file_url = get_file_viewer_url(file_path)
            
            # 构建标题HTML（如果文件路径存在，添加更明显的链接样式）
            if file_url:
                # Streamlit pages路径：不编码页面名称，让浏览器自动处理；只编码查询参数
                page_name = "2_📄_文件查看"  # Streamlit pages 目录下的文件名（不含.py）
                encoded_path = urllib.parse.quote(str(file_path), safe='')
                # 构建URL：页面路径不编码，查询参数编码
                full_url = f"/{page_name}?path={encoded_path}"
                title_html = (
                    f'<a href="{full_url}" '
                    f'style="'
                    f'color: var(--color-accent); '
                    f'text-decoration: underline; '
                    f'text-decoration-color: var(--color-accent); '
                    f'text-underline-offset: 3px; '
                    f'font-weight: 600; '
                    f'font-size: 1rem; '
                    f'cursor: pointer; '
                    f'transition: all 0.2s ease;'
                    f'" '
                    f'onmouseover="this.style.color=\'var(--color-accent-hover)\'; this.style.textDecorationColor=\'var(--color-accent-hover)\';" '
                    f'onmouseout="this.style.color=\'var(--color-accent)\'; this.style.textDecorationColor=\'var(--color-accent)\';" '
                    f'title="点击查看完整文件">'
                    f'[{citation_num}] {title} 🔗'
                    f'</a>'
                )
            else:
                # 无链接时，仍显示标题但不加链接样式
                title_html = f'<span style="font-weight: 600; font-size: 1rem; color: var(--color-accent);">[{citation_num}] {title}</span>'
            
            # 使用卡片样式显示
            st.markdown(
                f'<div id="{citation_id}" style="'
                f'padding: 1rem; '
                f'margin-bottom: 1rem; '
                f'border: 1px solid var(--color-border); '
                f'border-radius: 8px; '
                f'background-color: var(--color-bg-card); '
                f'transition: all 0.3s ease;'
                f'">'
                f'<div style="margin-bottom: 0.5rem;">'
                f'{title_html}'
                f'</div>',
                unsafe_allow_html=True
            )
            
            # 显示元数据
            metadata_parts = []
            if source['score'] is not None:
                metadata_parts.append(f"相似度: {source['score']:.2f}")
            if 'file_name' in source['metadata']:
                metadata_parts.append(f"📁 {source['metadata']['file_name']}")
            
            if metadata_parts:
                st.caption(" | ".join(metadata_parts))
            
            # 显示文本内容（限制长度，可展开）
            text = source['text']
            if len(text) > 300:
                with st.expander("查看完整内容", expanded=False):
                    st.text(text)
                st.text(text[:300] + "...")
            else:
                st.text(text)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            if source != sources[-1]:
                st.divider()


def display_hybrid_sources(local_sources, wikipedia_sources):
    """分区展示混合查询的来源
    
    Args:
        local_sources: 本地知识库来源列表
        wikipedia_sources: 维基百科来源列表
    """
    import urllib.parse
    
    # 本地知识库来源
    if local_sources:
        with st.expander(f"📚 本地知识库来源 ({len(local_sources)})", expanded=True):
            for i, source in enumerate(local_sources, 1):
                metadata = source.get('metadata', {})
                
                # 尝试多种方式获取文件路径
                file_path = (
                    metadata.get('file_path') or 
                    metadata.get('file_name') or 
                    metadata.get('source') or 
                    metadata.get('url') or
                    metadata.get('filename') or
                    ''
                )
                
                # 提取标题（优先使用title，否则使用文件名）
                title = (
                    metadata.get('title') or 
                    metadata.get('file_name') or 
                    metadata.get('filename') or
                    'Unknown'
                )
                
                # 如果title是路径，提取文件名作为显示标题
                if '/' in title or '\\' in title:
                    title = Path(title).name if title else 'Unknown'
                
                # 生成文件查看链接
                file_url = None
                if file_path:
                    file_url = get_file_viewer_url(file_path)
                
                # 构建标题HTML（如果文件路径存在，添加链接）
                if file_url:
                    # Streamlit pages路径：不编码页面名称，让浏览器自动处理；只编码查询参数
                    page_name = "2_📄_文件查看"  # Streamlit pages 目录下的文件名（不含.py）
                    encoded_path = urllib.parse.quote(str(file_path), safe='')
                    # 构建URL：页面路径不编码，查询参数编码
                    full_url = f"/{page_name}?path={encoded_path}"
                    title_html = (
                        f'<strong>'
                        f'<a href="{full_url}" '
                        f'style="'
                        f'color: var(--color-accent); '
                        f'text-decoration: underline; '
                        f'text-decoration-color: var(--color-accent); '
                        f'text-underline-offset: 3px; '
                        f'font-weight: 600; '
                        f'cursor: pointer; '
                        f'transition: all 0.2s ease;'
                        f'" '
                        f'onmouseover="this.style.color=\'var(--color-accent-hover)\'; this.style.textDecorationColor=\'var(--color-accent-hover)\';" '
                        f'onmouseout="this.style.color=\'var(--color-accent)\'; this.style.textDecorationColor=\'var(--color-accent)\';" '
                        f'title="点击查看完整文件">'
                        f'[{i}] {title} 🔗'
                        f'</a>'
                        f'</strong>'
                    )
                    st.markdown(title_html, unsafe_allow_html=True)
                else:
                    st.markdown(f"**[{i}] {title}**")
                
                # 显示元数据
                metadata_parts = []
                if 'file_name' in source['metadata']:
                    metadata_parts.append(f"📁 {source['metadata']['file_name']}")
                if source.get('score') is not None:
                    metadata_parts.append(f"相似度: {source['score']:.2f}")
                if metadata_parts:
                    st.caption(" | ".join(metadata_parts))
                
                # 显示完整内容，不截断
                st.text(source['text'])
                
                if i < len(local_sources):
                    st.divider()
    
    # 维基百科来源
    if wikipedia_sources:
        with st.expander(f"🌐 维基百科补充 ({len(wikipedia_sources)})", expanded=False):
            for i, source in enumerate(wikipedia_sources, 1):
                title = source['metadata'].get('title', 'Unknown')
                st.markdown(f"**[W{i}] {title}**")
                
                # 显示维基百科链接和相似度
                wiki_url = source['metadata'].get('wikipedia_url', '#')
                metadata_parts = [f"🔗 [{wiki_url}]({wiki_url})"]
                if source.get('score') is not None:
                    metadata_parts.append(f"相似度: {source['score']:.2f}")
                st.caption(" | ".join(metadata_parts))
                
                # 显示完整内容，不截断
                st.text(source['text'])
                
                if i < len(wikipedia_sources):
                    st.divider()


def display_model_status():
    """在页面底部显示 Embedding 模型状态"""
    st.markdown("---")
    
    try:
        status = get_embedding_model_status()
        
        # 使用 expander 默认收起
        with st.expander("🔧 Embedding 模型状态", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**模型信息**")
                st.text(f"名称: {status['model_name']}")
                if status['loaded']:
                    st.success("✅ 已加载到内存")
                else:
                    st.info("💤 未加载（首次使用时加载）")
            
            with col2:
                st.markdown("**缓存状态**")
                if status['cache_exists']:
                    st.success("✅ 本地缓存存在")
                    st.caption("后续使用无需联网")
                else:
                    st.warning("⚠️  本地无缓存")
                    st.caption("首次使用将从镜像下载")
            
            with col3:
                st.markdown("**网络配置**")
                if status['offline_mode']:
                    st.info("📴 离线模式")
                    st.caption("仅使用本地缓存")
                else:
                    st.info(f"🌐 在线模式")
                    st.caption(f"镜像: {status['mirror']}")
            
            # 详细信息（可折叠）
            with st.expander("查看详细信息", expanded=False):
                st.json(status)
    
    except Exception as e:
        st.error(f"获取模型状态失败: {e}")


def group_sessions_by_time(sessions_metadata):
    """按时间分组会话
    
    Args:
        sessions_metadata: 会话元数据列表
        
    Returns:
        分组后的字典: {'今天': [...], '7天内': [...], '30天内': [...]}
    """
    from datetime import datetime, timedelta
    
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    
    groups = {
        '📅 今天': [],
        '📅 7天内': [],
        '📅 30天内': []
    }
    
    for session in sessions_metadata:
        try:
            # 解析更新时间
            updated_at = datetime.fromisoformat(session['updated_at'])
            
            if updated_at >= today_start:
                groups['📅 今天'].append(session)
            elif updated_at >= seven_days_ago:
                groups['📅 7天内'].append(session)
            elif updated_at >= thirty_days_ago:
                groups['📅 30天内'].append(session)
        except Exception as e:
            logger.warning(f"解析时间失败: {e}")
            continue
    
    return groups


def display_session_history(user_email: str, current_session_id: Optional[str] = None):
    """显示历史会话列表（按时间分组）
    
    Args:
        user_email: 用户邮箱
        current_session_id: 当前会话ID（用于高亮显示）
    """
    from src.chat_manager import get_user_sessions_metadata
    
    # 调试信息
    logger.debug(f"正在查找用户会话: {user_email}")
    
    # 获取所有会话元数据
    sessions_metadata = get_user_sessions_metadata(user_email)
    
    logger.debug(f"找到 {len(sessions_metadata)} 个会话")
    
    if not sessions_metadata:
        st.caption("暂无历史会话")
        return
    
    # 按时间分组
    grouped_sessions = group_sessions_by_time(sessions_metadata)
    
    # 显示各分组
    for group_name, sessions in grouped_sessions.items():
        if sessions:
            st.markdown(f"**{group_name}**")
            
            for session in sessions:
                # 判断是否为当前会话
                is_current = session['session_id'] == current_session_id
                
                # 创建会话按钮（去掉左侧图标；单行省略；右侧小图标）
                session_title = session['title'] or "新对话"
                max_len = 28
                if len(session_title) > max_len:
                    session_title_display = session_title[:max_len - 1] + "…"
                else:
                    session_title_display = session_title
                # 右侧使用小箭头符号，视觉更轻
                button_label = f"{session_title_display}  ›"
                
                # 使用容器来实现悬停效果和点击
                if st.button(
                    button_label,
                    key=f"session_{session['session_id']}",
                    use_container_width=True,
                    type="primary" if is_current else "secondary"
                ):
                    # 点击后加载该会话
                    if not is_current:
                        st.session_state.load_session_id = session['session_id']
                        st.session_state.load_session_path = session['file_path']
                        st.rerun()
                
                # 移除消息数量等冗余信息，保持列表简洁
            
            st.divider()

