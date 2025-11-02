"""
设置页面主文件
整合所有设置模块
"""

import streamlit as st
from pathlib import Path
import sys

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import config
from src.ui_components import (
    init_session_state, 
    preload_embedding_model
)
from pages.settings.styles import CLAUDE_STYLE_CSS
from pages.settings.data_source import render_data_source_tab
from pages.settings.query_config import render_query_config_tab
from pages.settings.dev_tools import render_dev_tools_tab
from pages.settings.system_status import render_system_status_tab


# 页面配置
st.set_page_config(
    page_title="设置 - " + config.APP_TITLE,
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 应用CSS样式
st.markdown(CLAUDE_STYLE_CSS, unsafe_allow_html=True)

# 预加载模型和初始化状态
preload_embedding_model()
init_session_state()

# 检查登录状态
if not st.session_state.logged_in:
    st.warning("⚠️ 请先在主页登录")
    st.stop()

# 页面标题
st.title("⚙️ 系统状态")
st.caption(f"当前用户: {st.session_state.user_email}")

st.divider()

# 面包屑导航
st.markdown("📍 主页 > 设置")
st.divider()

# 创建标签页
tab1, tab2, tab3, tab4 = st.tabs([
    "📦 数据源管理",
    "🔧 查询配置",
    "🐛 开发者工具",
    "⚙️ 系统状态"
])

# 渲染各个标签页
with tab1:
    render_data_source_tab()

with tab2:
    render_query_config_tab()

with tab3:
    render_dev_tools_tab()

with tab4:
    render_system_status_tab()

