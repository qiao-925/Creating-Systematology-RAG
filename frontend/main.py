"""
Streamlit Web应用 - 主页入口
支持后台预加载，界面立即显示

设计说明：
- 启动时立即显示界面，后台异步初始化耗时模块
- 用户首次查询时，如果后台加载完成则正常响应
- 如果后台加载未完成，显示加载进度
"""

import streamlit as st

# 配置应用环境（必须在导入项目模块前）
from frontend.config import configure_all
configure_all()

# 导入项目模块
from frontend.components.sidebar import render_sidebar
from frontend.components.chat_display import render_chat_interface
from frontend.components.query_handler import handle_user_queries
from frontend.utils.state import init_session_state
from frontend.utils.preloader import (
    start_background_init,
    get_services,
    get_init_status,
    get_progress_message,
    get_detailed_progress,
    PreloadStatus
)


# 静态 CSS 样式（模块级别常量，避免重复创建字符串）
_CUSTOM_CSS = """
<style>
/* 全局样式优化 */
.stApp {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 聊天消息样式 */
.stChatMessage {
    padding: 12px 16px;
    border-radius: 12px;
    margin-bottom: 8px;
}

/* 折叠面板样式 */
.streamlit-expanderHeader {
    font-size: 14px;
    font-weight: 500;
    background-color: #f8fafc;
    border-radius: 8px;
}

/* 输入框样式 */
.stChatInput > div {
    border-radius: 24px;
    border: 2px solid #e2e8f0;
}
.stChatInput > div:focus-within {
    border-color: #6366f1;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

/* 按钮样式 */
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* 侧边栏样式 */
section[data-testid="stSidebar"] {
    background-color: #f8fafc;
}

/* 侧边栏组件样式（修复主题颜色警告） */
section[data-testid="stSidebar"] .stWidget {
    background-color: #ffffff;
    border-color: #e2e8f0;
}

section[data-testid="stSidebar"] .stSkeleton {
    background-color: #f1f5f9;
}

/* 成功/警告/错误提示样式 */
.stAlert {
    border-radius: 8px;
    border: none;
}

/* 代码块样式 */
.stCodeBlock {
    border-radius: 8px;
}

/* 隐藏 Streamlit 默认页脚 */
footer {visibility: hidden;}
</style>
<script>
// 错误处理：捕获并记录未捕获的异常，避免控制台错误
(function() {
    const originalError = console.error;
    const originalWarn = console.warn;
    
    // 过滤已知的 Streamlit 内部警告（不影响功能）
    const ignoredErrors = [
        'Invalid color passed for widgetBackgroundColor',
        'Invalid color passed for widgetBorderColor',
        'Invalid color passed for skeletonBackgroundColor',
        'preventOverflow modifier is required',
        'Element not found'
    ];
    
    console.error = function(...args) {
        const message = args.join(' ');
        // 如果是已知的 Streamlit 内部警告，静默处理
        if (ignoredErrors.some(err => message.includes(err))) {
            return;
        }
        // 其他错误正常输出
        originalError.apply(console, args);
    };
    
    console.warn = function(...args) {
        const message = args.join(' ');
        // 如果是已知的 Streamlit 内部警告，静默处理
        if (ignoredErrors.some(err => message.includes(err))) {
            return;
        }
        // 其他警告正常输出
        originalWarn.apply(console, args);
    };
    
    // 捕获未捕获的异常
    window.addEventListener('error', function(event) {
        const message = event.message || '';
        // 如果是已知的 Streamlit 内部错误，静默处理
        if (ignoredErrors.some(err => message.includes(err))) {
            event.preventDefault();
            return false;
        }
    }, true);
})();
</script>
"""


def _inject_custom_css():
    """注入自定义 CSS 样式（仅首次执行）"""
    # 使用 session_state 控制只注入一次，减少 DOM 操作
    if not st.session_state.get('_css_injected', False):
        st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)
        st.session_state._css_injected = True


def main():
    """主函数 - 应用入口点"""
    # 注入自定义 CSS
    _inject_custom_css()
    
    # 初始化 UI 状态
    init_session_state()
    
    # 优化：使用 session_state 存储服务实例，避免依赖 preloader 单例状态
    # 这样即使 preloader 因热重载丢失状态，也能正常运行
    if st.session_state.get('_services_cached'):
        _render_main_app_from_cache()
        return
    
    # 启动后台预加载（如果尚未开始）
    start_background_init()
    
    # 检查初始化状态
    status = get_init_status()
    
    if status == PreloadStatus.COMPLETED:
        # 初始化完成，缓存服务并正常运行
        _cache_services_and_render()
    elif status == PreloadStatus.IN_PROGRESS:
        # 正在初始化，显示界面但禁用查询
        _render_loading_app()
    elif status == PreloadStatus.FAILED:
        # 初始化失败
        _render_error_app()
    else:
        # 未开始（不应该到这里）
        _render_loading_app()


def _cache_services_and_render():
    """缓存服务到 session_state 并渲染应用"""
    services = get_services()
    if services is None:
        st.error("❌ 服务获取失败")
        st.stop()
        return
    
    init_result, rag_service, chat_manager = services
    
    # 缓存到 session_state（关键：确保热重载后仍可用）
    st.session_state.init_result = init_result
    st.session_state._cached_rag_service = rag_service
    st.session_state._cached_chat_manager = chat_manager
    st.session_state._services_cached = True
    
    _render_main_app_impl(init_result, rag_service, chat_manager)


def _render_main_app_from_cache():
    """从 session_state 缓存渲染应用（热重载后使用）"""
    init_result = st.session_state.get('init_result')
    rag_service = st.session_state.get('_cached_rag_service')
    chat_manager = st.session_state.get('_cached_chat_manager')
    
    if not all([init_result, rag_service, chat_manager]):
        # 缓存丢失，清除标志并重新初始化
        st.session_state._services_cached = False
        st.rerun()
        return
    
    _render_main_app_impl(init_result, rag_service, chat_manager)


def _render_main_app_impl(init_result, rag_service, chat_manager):
    """渲染完整应用的实际实现"""    
    # 渲染UI和处理查询
    render_sidebar(chat_manager)
    render_chat_interface(rag_service, chat_manager)
    handle_user_queries(rag_service, chat_manager)


def _render_loading_app():
    """渲染加载中界面（初始化进行中）
    
    注意：此函数仅在首次启动时执行。一旦初始化完成并设置了 _services_cached，
    后续的用户交互（如"开启新对话"）不会再进入此函数。
    """
    import time
    
    # 获取详细进度
    progress_msg = get_progress_message()
    detailed = get_detailed_progress()
    
    # 主容器
    st.markdown("### 💬 Creating Systematology RAG")
    
    # 加载状态指示
    st.info(f"🚀 {progress_msg}")
    st.caption("首次启动需要加载模型和连接数据库，请耐心等待...")
    
    # 进度条
    module_count = detailed.get('module_count', 0)
    progress_value = min(module_count / 10, 0.95) if module_count > 0 else 0.05
    st.progress(progress_value, text=f"已完成 {module_count} 个模块")
    
    # 显示日志样式的初始化记录
    logs = detailed.get('logs', [])
    if logs:
        log_text = "\n".join(logs[-15:])
        st.code(log_text, language=None)
    
    # 当前阶段
    stage = detailed.get('stage', '')
    if stage and '完成' not in stage:
        st.markdown(f"⏳ **{stage}...**")
    
    # 禁用的输入框
    st.chat_input("正在初始化，请稍候...", disabled=True)
    
    # 短间隔轮询，检查初始化状态
    time.sleep(0.5)
    st.rerun()


def _on_retry_click():
    """重试按钮回调"""
    from frontend.utils.preloader import get_preloader
    get_preloader().reset()


def _render_error_app():
    """渲染错误界面（初始化失败）"""
    from frontend.utils.preloader import get_preloader
    
    st.error("❌ 应用初始化失败")
    
    error = get_preloader().get_error()
    if error:
        st.code(error)
    
    st.info("💡 提示：请检查配置和网络连接，然后刷新页面重试")
    
    # 使用 on_click 回调，避免手动 rerun
    st.button("🔄 重试", on_click=_on_retry_click)


if __name__ == "__main__":
    main()
