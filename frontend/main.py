"""
Streamlit Web应用 - 主页入口
精简版，只负责初始化和路由

设计说明：
- 使用 @st.cache_resource 缓存初始化结果和服务实例
- 页面刷新不会清空缓存，只有应用重启才会重新初始化
- UI状态（messages等）存储在 session_state，页面刷新后清空
"""

import streamlit as st

# 配置应用环境（必须在导入项目模块前）
from frontend.config import configure_all
configure_all()

# 导入项目模块
from backend.infrastructure.config import config
from backend.infrastructure.initialization.bootstrap import initialize_app
from frontend.components.sidebar import render_sidebar
from frontend.components.chat_display import render_chat_interface
from frontend.components.query_handler import handle_user_queries
from frontend.utils.state import init_session_state


@st.cache_resource
def _initialize_app_services():
    """初始化应用服务（使用缓存，页面刷新不会重新初始化）
    
    Returns:
        tuple: (init_result, rag_service, chat_manager) 或 None 如果失败
    """
    try:
        init_result = initialize_app(show_progress=False)
        
        if not init_result.all_required_ready:
            return None
        
        # 获取服务实例
        rag_service = init_result.instances.get('rag_service')
        chat_manager = init_result.instances.get('chat_manager')
        
        # 如果不存在，尝试延迟初始化
        if not rag_service:
            success = init_result.manager.execute_init('rag_service')
            if success:
                rag_service = init_result.manager.instances.get('rag_service')
        
        if not chat_manager:
            success = init_result.manager.execute_init('chat_manager')
            if success:
                chat_manager = init_result.manager.instances.get('chat_manager')
        
        if not rag_service or not chat_manager:
            return None
        
        return init_result, rag_service, chat_manager
        
    except Exception as e:
        from backend.infrastructure.logger import get_logger
        logger = get_logger('frontend.main')
        logger.error(f"初始化失败: {e}", exc_info=True)
        return None


def main():
    """主函数 - 应用入口点"""
    # 初始化 UI 状态（每次页面加载都需要初始化，页面刷新后会清空）
    init_session_state()
    
    # 初始化应用服务（使用缓存，首次调用时初始化，后续直接返回缓存）
    init_data = _initialize_app_services()
    
    if init_data is None:
        with st.spinner("🚀 正在初始化应用..."):
            st.error("❌ 应用初始化失败")
            st.info("💡 提示：请检查配置和依赖，或刷新页面重试")
            st.stop()
        return
    
    init_result, rag_service, chat_manager = init_data
    
    # 首次初始化时显示摘要（使用 session_state 标记）
    if not st.session_state.get('init_summary_shown', False):
        summary = init_result.summary
        st.success(
            f"✅ 应用已就绪: "
            f"总计={summary['total']}, "
            f"成功={summary['success']}, "
            f"失败={summary['failed']}, "
            f"跳过={summary['skipped']}"
        )
        st.session_state.init_summary_shown = True
    
    # 渲染UI和处理查询
    render_sidebar(chat_manager)
    render_chat_interface(rag_service, chat_manager)
    handle_user_queries(rag_service, chat_manager)


if __name__ == "__main__":
    main()

