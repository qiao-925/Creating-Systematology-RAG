"""
Streamlit Web应用 - 主页入口
精简版，只负责初始化和路由
"""

import streamlit as st
from pathlib import Path
import sys
import atexit

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 抑制OpenTelemetry导出器的错误日志（避免连接失败时的噪音）
import logging
logging.getLogger('opentelemetry.sdk.trace.export').setLevel(logging.WARNING)
logging.getLogger('opentelemetry.exporter.otlp').setLevel(logging.WARNING)
logging.getLogger('opentelemetry.exporter.otlp.proto.grpc').setLevel(logging.WARNING)

# 优先设置 UTF-8 编码（确保 emoji 正确显示）
try:
    from src.infrastructure.encoding import setup_utf8_encoding
    setup_utf8_encoding()
except ImportError:
    # 如果 encoding 模块尚未加载，手动设置基础编码
    import os
    os.environ["PYTHONIOENCODING"] = "utf-8"

from src.infrastructure.config import config
from frontend.utils.state import init_session_state
from frontend.utils.services import load_rag_service, load_chat_manager
from frontend.utils.styles import CLAUDE_STYLE_CSS
from frontend.utils.cleanup import cleanup_resources
from frontend.components.sidebar import render_sidebar
from frontend.components.chat_display import render_chat_interface
from frontend.components.query_handler import handle_user_queries
from frontend.utils.state import initialize_app_state

# 注册退出钩子
atexit.register(cleanup_resources)

# 页面配置
st.set_page_config(
    page_title="主页",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """主函数"""
    # 应用样式
    st.markdown(CLAUDE_STYLE_CSS, unsafe_allow_html=True)
    
    # 初始化状态
    init_session_state()
    initialize_app_state()
    
    # 启动初始化
    if not st.session_state.boot_ready:
        # 启动阶段：简化初始化流程（延迟加载，不预加载模型）
        # 模型和 Phoenix 将在首次使用时按需加载
        st.session_state.boot_ready = True
        st.rerun()
        return
    
    # 显示侧边栏
    # 初始化RAG服务（新架构推荐）
    rag_service = load_rag_service()
    if not rag_service:
        st.error("❌ RAG服务初始化失败")
        return
    
    # 初始化对话管理器（用于会话管理和历史记录）
    chat_manager = load_chat_manager()
    if not chat_manager:
        st.error("❌ 对话管理器初始化失败")
        return
    
    # 渲染侧边栏
    render_sidebar(chat_manager)
    
    # 渲染对话界面
    render_chat_interface(rag_service, chat_manager)
    
    # 处理用户查询
    handle_user_queries(rag_service, chat_manager)


if __name__ == "__main__":
    main()

