"""
聊天布局辅助函数

主要功能：
- 渲染标题 SVG/回退文本
- 返回设置/重置图标文本
- 注入按钮图标 CSS
- 注入首屏居中与隐藏脚本
"""

import streamlit as st

from backend.infrastructure.config import config
from frontend.config import (
    APP_TITLE_TEXT_SVG_HEIGHT_PX,
    SETTINGS_ICON_SIZE_PX,
    RESTART_ICON_SIZE_PX,
    get_restart_icon_svg_data_uri,
    get_settings_icon_svg_data_uri,
    get_title_text_svg_data_uri,
)


def render_title_text() -> None:
    """渲染标题文字：优先 SVG，缺失时回退普通标题文本。"""
    title_text_svg_data_uri = get_title_text_svg_data_uri()
    if title_text_svg_data_uri:
        st.markdown(
            (
                f"<img src='{title_text_svg_data_uri}' "
                f"height='{APP_TITLE_TEXT_SVG_HEIGHT_PX}' "
                "style='display:block;width:auto;max-width:100%;margin:.3rem 0 .25rem 0;' "
                "alt='title-text'/>"
            ),
            unsafe_allow_html=True,
        )
        return

    st.title(config.APP_TITLE, anchor=False, width="stretch")


def render_settings_icon() -> str:
    """返回设置按钮文本：SVG 可用时返回占位文本，否则回退符号。"""
    svg_data_uri = get_settings_icon_svg_data_uri()
    if svg_data_uri:
        return " "
    return "⚙︎"


def render_restart_icon() -> str:
    """返回重置按钮文本：SVG 可用时返回占位文本，否则回退符号。"""
    svg_data_uri = get_restart_icon_svg_data_uri()
    if svg_data_uri:
        return " "
    return "↻"


def inject_settings_button_icon_css() -> None:
    """为设置按钮注入 SVG 图标样式（仅视觉，不影响按钮行为）。"""
    svg_data_uri = get_settings_icon_svg_data_uri()
    if not svg_data_uri:
        return

    st.markdown(
        f"""
<style>
.st-key-settings_button_top button,
.st-key-settings_button_top [data-testid="stBaseButton-tertiary"] {{
    width: {SETTINGS_ICON_SIZE_PX + 10}px !important;
    min-width: {SETTINGS_ICON_SIZE_PX + 10}px !important;
    height: {SETTINGS_ICON_SIZE_PX + 10}px !important;
    padding: 0 !important;
    border: none !important;
    border-radius: 0 !important;
    background-color: transparent !important;
    color: #87E7A9 !important;
    font-size: 0 !important;
    line-height: 0 !important;
    box-shadow: none !important;
}}

.st-key-settings_button_top button::before,
.st-key-settings_button_top [data-testid="stBaseButton-tertiary"]::before {{
    content: "";
    display: block;
    width: {SETTINGS_ICON_SIZE_PX}px;
    height: {SETTINGS_ICON_SIZE_PX}px;
    margin: 0 auto;
    background-color: currentColor;
    -webkit-mask: url('{svg_data_uri}') center / contain no-repeat;
    mask: url('{svg_data_uri}') center / contain no-repeat;
}}

.st-key-settings_button_top button:hover,
.st-key-settings_button_top [data-testid="stBaseButton-tertiary"]:hover,
.st-key-settings_button_top button:focus-visible,
.st-key-settings_button_top [data-testid="stBaseButton-tertiary"]:focus-visible {{
    border: none !important;
    background-color: transparent !important;
    color: #B6F2C8 !important;
    box-shadow: none !important;
    outline: none !important;
    transform: none !important;
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def inject_restart_button_icon_css() -> None:
    """为重置按钮注入 SVG 图标样式（仅视觉，不影响按钮行为）。"""
    svg_data_uri = get_restart_icon_svg_data_uri()
    if not svg_data_uri:
        return

    st.markdown(
        f"""
<style>
.st-key-restart_button button,
.st-key-restart_button [data-testid="stBaseButton-secondary"] {{
    width: {RESTART_ICON_SIZE_PX + 10}px !important;
    min-width: {RESTART_ICON_SIZE_PX + 10}px !important;
    height: {RESTART_ICON_SIZE_PX + 10}px !important;
    padding: 0 !important;
    border: none !important;
    border-radius: 0 !important;
    background-color: transparent !important;
    color: #87E7A9 !important;
    font-size: 0 !important;
    line-height: 0 !important;
    box-shadow: none !important;
}}

.st-key-restart_button button::before,
.st-key-restart_button [data-testid="stBaseButton-secondary"]::before {{
    content: "";
    display: block;
    width: {RESTART_ICON_SIZE_PX}px;
    height: {RESTART_ICON_SIZE_PX}px;
    margin: 0 auto;
    background-color: currentColor;
    -webkit-mask: url('{svg_data_uri}') center / contain no-repeat;
    mask: url('{svg_data_uri}') center / contain no-repeat;
}}

.st-key-restart_button button:hover,
.st-key-restart_button [data-testid="stBaseButton-secondary"]:hover,
.st-key-restart_button button:focus-visible,
.st-key-restart_button [data-testid="stBaseButton-secondary"]:focus-visible {{
    border: none !important;
    background-color: transparent !important;
    color: #B6F2C8 !important;
    box-shadow: none !important;
    outline: none !important;
    transform: none !important;
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def inject_landing_center_css() -> None:
    """首屏状态下让标题+输入区块上下居中。"""
    st.markdown(
        """
<style>
.st-key-landing_center_shell {
    min-height: calc(100vh - 8.8rem) !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    width: 100% !important;
    padding-bottom: 6vh !important;
    transition: opacity 0.12s ease-out;
}

@media (max-width: 768px) {
    .st-key-landing_center_shell {
        min-height: calc(100vh - 7rem) !important;
        padding-bottom: 3.5vh !important;
    }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def inject_landing_hide_script() -> None:
    """在 landing 内容渲染完毕后注入即时隐藏脚本，消除 rerun 期间虚影。"""
    st.markdown(
        """
<script>
requestAnimationFrame(function(){
  var shell = document.querySelector('.st-key-landing_center_shell');
  if (!shell) return;
  function hide(){ shell.style.opacity='0'; shell.style.pointerEvents='none'; }
  var ta = shell.querySelector('textarea');
  if(ta) ta.addEventListener('keydown', function(e){
    if(e.key==='Enter' && !e.shiftKey && ta.value.trim()) hide();
  });
  var btn = shell.querySelector('[data-testid="stChatInputSubmitButton"]');
  if(btn) btn.addEventListener('click', function(){ if(ta && ta.value.trim()) hide(); });
  shell.querySelectorAll('[data-testid="stPills"] [role="radio"]').forEach(function(p){
    p.addEventListener('click', hide);
  });
});
</script>
        """,
        unsafe_allow_html=True,
    )
