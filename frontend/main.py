"""
Streamlit Web应用 - 主页入口
支持后台预加载，界面立即显示

设计说明：
- 启动时立即显示界面，后台异步初始化耗时模块
- 用户首次查询时，如果后台加载完成则正常响应
- 如果后台加载未完成，显示加载进度
"""

import json
import time
from pathlib import Path

import streamlit as st

# 配置应用环境（必须在导入项目模块前）
from frontend.config import configure_all
configure_all()

# 导入项目模块
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


# 静态 CSS 样式（单列居中布局，参考 Streamlit AI Assistant）
_CUSTOM_CSS = """
<style>
/* 全局样式 */
.stApp {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 16px;
}

/* 主内容区居中，最大宽度限制 */
.block-container {
    max-width: clamp(320px, 35vw, 1600px);
    padding-left: 1.25rem;
    padding-right: 1.25rem;
}

/* 标题保持单行显示 */
.stApp h1 {
    white-space: nowrap;
}

/* 标题区：图标单行 + 文案单行 */
/* 折叠面板样式 */
.streamlit-expanderHeader {
    font-size: 1rem;
    font-weight: 500;
    border-radius: 8px;
}

/* Chat input styling: align quick-start and bottom input */
:root {
    --chat-input-height: 48px;
    --chat-input-radius: 999px;
    --chat-input-pad-y: 0.6rem;
    --chat-input-pad-x: 1.25rem;
    --chat-input-pad-right: 3.5rem;
    --chat-input-bg: var(--secondary-background-color);
    --chat-input-border: rgba(255, 255, 255, 0.08);
    --chat-input-text: var(--text-color);
    --chat-input-placeholder: rgba(220, 220, 224, 0.6);
}
.stChatInput > div {
    border-radius: var(--chat-input-radius);
}
.stChatInput > div > div {
    border-radius: var(--chat-input-radius);
}
.stChatInput textarea,
.stChatInput [data-baseweb="textarea"] {
    border-radius: var(--chat-input-radius);
    height: var(--chat-input-height);
    min-height: var(--chat-input-height);
    max-height: var(--chat-input-height);
    padding: var(--chat-input-pad-y) var(--chat-input-pad-right) var(--chat-input-pad-y) var(--chat-input-pad-x);
    background: var(--chat-input-bg);
    border: 1px solid var(--chat-input-border);
    color: var(--chat-input-text);
}
.stChatInput textarea::placeholder,
.stChatInput [data-baseweb="textarea"]::placeholder {
    color: var(--chat-input-placeholder);
}

/* 按钮样式 */
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
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

/* 观察器摘要样式 */
.obs-summary {
    font-size: 0.85rem;
    color: #888888;
    margin: 4px 0 8px 0;
    padding: 0;
}

/* 引用来源样式 */
.source-title {
    font-size: 0.9rem;
    font-weight: 500;
}
.source-preview {
    font-size: 0.8rem;
    color: #888888;
    margin: 2px 0 12px 16px;
    line-height: 1.4;
}

/* st-chat 延续块：与助手气泡视觉统一 */
.message-continuation-anchor {
    margin: 0;
    padding: 0;
    height: 0;
    line-height: 0;
    overflow: hidden;
    display: block;
}
[data-testid="stMarkdown"]:has(.message-continuation-anchor) {
    margin-bottom: -8px;
}
[data-testid="stMarkdown"]:has(.message-continuation-anchor) + div .stChatMessage,
[data-testid="stMarkdown"]:has(.message-continuation-anchor) + div [data-testid="stChatMessage"] {
    margin-top: -8px;
    border-top-left-radius: 0;
    border-top-right-radius: 0;
}
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

// Ctrl+Enter / Cmd+Enter 快捷键发送
(function() {
    document.addEventListener('keydown', function(e) {
        // Ctrl+Enter (Windows/Linux) 或 Cmd+Enter (Mac)
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            // 精确查找发送按钮：通过文本内容和按钮类型匹配
            // 查找所有 primary 类型的按钮，筛选出文本为"发送"的
            const primaryButtons = document.querySelectorAll('[data-testid="stBaseButton-primary"]');
            for (const btn of primaryButtons) {
                const text = btn.textContent?.trim() || '';
                // 精确匹配"发送"文本，确保不会误触其他按钮
                if (text === '发送' && !btn.disabled) {
                    e.preventDefault();
                    btn.click();
                    return; // 找到后立即返回，避免重复点击
                }
            }
        }
    });
})();
</script>
"""


def _inject_custom_css():
    """注入自定义 CSS 样式（每次渲染确保样式生效）"""
    st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)


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
        _cache_services_and_render()
    elif status == PreloadStatus.IN_PROGRESS:
        _render_loading_app()
    elif status == PreloadStatus.FAILED:
        _render_error_app()
    else:
        _render_loading_app()


def _cache_services_and_render():
    """缓存服务到 session_state 并渲染应用"""
    services = get_services()
    if services is None:
        st.error("❌ 服务获取失败")
        st.stop()
        return
    
    init_result, _, _ = services
    rag_service, chat_manager = _build_session_services(init_result)
    
    # 缓存到 session_state（关键：确保热重载后仍可用）
    st.session_state.init_result = init_result
    st.session_state._cached_rag_service = rag_service
    st.session_state._cached_chat_manager = chat_manager
    st.session_state._services_cached = True
    
    _render_main_app_impl(init_result, rag_service, chat_manager)


def _ensure_shared_index_manager(init_result, create_if_missing: bool = True):
    """Get or initialize a shared IndexManager from init_result."""
    from backend.infrastructure.logger import get_logger
    logger = get_logger('frontend.services')

    index_manager = init_result.instances.get('index_manager')
    if index_manager is not None or not create_if_missing:
        return index_manager

    manager = getattr(init_result, 'manager', None)
    if manager is None:
        return None

    try:
        if 'index_manager' in manager.modules and manager.execute_init('index_manager'):
            index_manager = manager.instances.get('index_manager')
            if index_manager is not None:
                init_result.instances['index_manager'] = index_manager
    except Exception as e:
        logger.warning(f"IndexManager init failed: {e}")
        return None

    return index_manager


def _build_session_services(init_result):
    """Create per-session RAGService/ChatManager while sharing IndexManager."""
    from backend.infrastructure.config import config
    from backend.business.rag_api import RAGService
    from backend.business.chat import ChatManager
    from frontend.components.config_panel.models import AppConfig

    app_config = AppConfig.from_session_state()
    index_manager = _ensure_shared_index_manager(init_result, create_if_missing=False)
    index_manager_provider = lambda: _ensure_shared_index_manager(init_result, create_if_missing=True)

    collection_name = st.session_state.get('collection_name', config.CHROMA_COLLECTION_NAME)
    temperature = app_config.get_llm_temperature()
    max_tokens = app_config.get_llm_max_tokens()

    chat_manager = ChatManager(
        index_manager=index_manager,
        index_manager_provider=index_manager_provider,
        enable_debug=app_config.debug_mode,
        enable_markdown_formatting=True,
        use_agentic_rag=app_config.use_agentic_rag,
        model_id=app_config.selected_model,
        retrieval_strategy=app_config.retrieval_strategy,
        similarity_top_k=app_config.similarity_top_k,
        similarity_threshold=app_config.similarity_threshold,
        enable_rerank=app_config.enable_rerank,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    rag_service = RAGService(
        collection_name=collection_name,
        enable_debug=app_config.debug_mode,
        enable_markdown_formatting=True,
        use_agentic_rag=app_config.use_agentic_rag,
        model_id=app_config.selected_model,
        retrieval_strategy=app_config.retrieval_strategy,
        similarity_top_k=app_config.similarity_top_k,
        similarity_threshold=app_config.similarity_threshold,
        enable_rerank=app_config.enable_rerank,
        index_manager=index_manager,
        chat_manager=chat_manager,
        index_manager_provider=index_manager_provider,
    )

    return rag_service, chat_manager


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


def _debug_log(location: str, message: str, data: dict | None = None, hypothesis_id: str = "D") -> None:
    # #region agent log
    try:
        log_path = Path(__file__).resolve().parent.parent / ".cursor" / "debug.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": hypothesis_id, "location": location, "message": message, "data": data or {}, "timestamp": __import__("time").time() * 1000}, ensure_ascii=False) + "\n")
    except Exception:  # noqa: S110
        pass
    # #endregion


def _render_main_app_impl(init_result, rag_service, chat_manager):
    """渲染完整应用的实际实现"""    
    # #region agent log
    _debug_log("main.py:_render_main_app_impl", "entry", hypothesis_id="D")
    # #endregion
    # 渲染UI和处理查询（单列居中布局，无侧边栏）
    render_chat_interface(rag_service, chat_manager)
    # #region agent log
    _debug_log("main.py:before_handle_user_queries", "before handle_user_queries", hypothesis_id="D")
    # #endregion
    handle_user_queries(rag_service, chat_manager)


def _render_loading_app():
    """Render loading screen while initialization is in progress."""
    # Title
    st.markdown("### ??Creating Systematology")

    # Placeholders to avoid full-page flash
    info_ph = st.empty()
    caption_ph = st.empty()
    progress_ph = st.empty()
    logs_ph = st.empty()
    stage_ph = st.empty()
    input_ph = st.empty()

    refresh_interval = 0.6  # seconds

    # Disabled input (render once to avoid duplicate element IDs)
    input_ph.chat_input("??????????????..", key="init_chat_input", disabled=True)

    # Fetch progress
    progress_msg = get_progress_message()
    detailed = get_detailed_progress()

    # Status
    info_ph.info(f"??{progress_msg}")
    caption_ph.caption("??????????????????????????????????...")

    # Progress bar
    module_count = detailed.get('module_count', 0)
    progress_value = min(module_count / 10, 0.95) if module_count > 0 else 0.05
    progress_ph.progress(progress_value, text=f"?????{module_count} ?????")

    # Logs
    logs = detailed.get('logs', [])
    if logs:
        log_text = "\n".join(logs[-15:])
        logs_ph.code(log_text, language=None)
    else:
        logs_ph.empty()

    # Current stage
    stage = detailed.get('stage', '')
    if stage and '???' not in stage:
        stage_ph.markdown(f"??**{stage}...**")
    else:
        stage_ph.empty()

    # If done or failed, immediately rerun to swap UI
    status = get_init_status()
    if status in (PreloadStatus.COMPLETED, PreloadStatus.FAILED):
        _debug_log("main.py:_render_loading_app", "before st.rerun (loading->final)", hypothesis_id="C")
        st.rerun()
        return

    # Short sleep to throttle polling without long blocking
    time.sleep(refresh_interval)

    # Auto rerun to poll status
    # #region agent log
    _debug_log("main.py:_render_loading_app", "before st.rerun (loading)", hypothesis_id="C")
    # #endregion
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
