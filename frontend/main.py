"""
Streamlit Web应用 - 主页入口
精简版，只负责初始化和路由
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


def main():
    """主函数 - 应用入口点"""
    # 初始化应用（如果尚未初始化）
    if not st.session_state.get('boot_ready', False):
        _initialize_application()
        return
    
    # 获取并验证服务
    rag_service, chat_manager = _get_services()
    if rag_service is None or chat_manager is None:
        return
    
    # 渲染UI和处理查询
    render_sidebar(chat_manager)
    render_chat_interface(rag_service, chat_manager)
    handle_user_queries(rag_service, chat_manager)


def _initialize_application() -> bool:
    """初始化应用
    
    Returns:
        bool: 初始化是否成功
    """
    with st.spinner("🚀 正在初始化应用..."):
        try:
            init_result = initialize_app(show_progress=True)
            
            if not init_result.all_required_ready:
                st.error("❌ 部分必需模块初始化失败，应用无法启动")
                st.error(f"失败模块: {', '.join(init_result.failed_modules)}")
                
                with st.expander("查看详细初始化报告"):
                    st.text(init_result.manager.generate_report())
                
                st.stop()
                return False
            
            # 保存初始化结果
            st.session_state.boot_ready = True
            st.session_state.init_result = init_result
            
            # 显示初始化摘要
            summary = init_result.summary
            st.success(
                f"✅ 初始化完成: "
                f"总计={summary['total']}, "
                f"成功={summary['success']}, "
                f"失败={summary['failed']}, "
                f"跳过={summary['skipped']}"
            )
            
            st.rerun()
            return True
            
        except Exception as e:
            st.error(f"❌ 初始化过程发生错误: {e}")
            st.exception(e)
            st.stop()
            return False


def _get_services():
    """获取并验证服务实例
    
    Returns:
        tuple: (rag_service, chat_manager) 或 (None, None) 如果失败
    """
    init_result = st.session_state.get('init_result')
    if init_result is None:
        st.error("❌ 初始化结果未找到，请刷新页面")
        st.stop()
        return None, None
    
    rag_service = init_result.instances.get('rag_service')
    chat_manager = init_result.instances.get('chat_manager')
    
    if not rag_service:
        st.error("❌ RAG服务未初始化")
        st.stop()
        return None, None
    
    if not chat_manager:
        st.error("❌ 对话管理器未初始化")
        st.stop()
        return None, None
    
    return rag_service, chat_manager


if __name__ == "__main__":
    main()

