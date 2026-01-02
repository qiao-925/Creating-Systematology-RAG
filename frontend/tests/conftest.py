"""
前端测试专用 fixtures
提供 Streamlit Mock 和前端测试所需的通用 fixtures
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 导入通用 fixtures（如果需要）
try:
    from tests.conftest import project_root, test_data_dir
except ImportError:
    # 如果无法导入，定义基础 fixtures
    @pytest.fixture(scope="session")
    def project_root():
        """项目根目录"""
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture(scope="session")
    def test_data_dir():
        """测试数据目录"""
        return Path(__file__).parent.parent / "tests" / "fixtures" / "sample_docs"


class SessionStateMock(dict):
    """支持属性访问的 session_state Mock"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self
    
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name, value):
        self[name] = value
    
    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit 模块"""
    with patch.dict('sys.modules', {
        'streamlit': MagicMock(),
        'streamlit.session_state': MagicMock(),
    }):
        import streamlit as st
        # 创建支持属性访问的 session_state
        st.session_state = SessionStateMock({
            'boot_ready': False,
            'messages': [],
            'current_sources_map': {},
            'current_reasoning_map': {},
        })
        
        # Mock 常用 Streamlit 组件
        st.sidebar = MagicMock()
        st.sidebar.__enter__ = MagicMock(return_value=st.sidebar)
        st.sidebar.__exit__ = MagicMock(return_value=False)
        st.title = MagicMock()
        st.caption = MagicMock()
        st.button = MagicMock(return_value=False)
        st.text_input = MagicMock(return_value="")
        st.text_area = MagicMock(return_value="")
        st.selectbox = MagicMock(return_value=None)
        st.checkbox = MagicMock(return_value=False)
        st.radio = MagicMock(return_value=None)
        st.slider = MagicMock(return_value=0)
        st.divider = MagicMock()
        st.markdown = MagicMock()
        st.write = MagicMock()
        st.info = MagicMock()
        st.error = MagicMock()
        st.success = MagicMock()
        st.warning = MagicMock()
        st.empty = MagicMock(return_value=MagicMock())
        mock_expander = MagicMock()
        mock_expander.__enter__ = MagicMock(return_value=mock_expander)
        mock_expander.__exit__ = MagicMock(return_value=False)
        st.expander = MagicMock(return_value=mock_expander)
        st.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
        st.tabs = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock()])
        st.metric = MagicMock()
        st.set_page_config = MagicMock()
        st.dialog = MagicMock(return_value=lambda func: func)
        mock_chat_msg = MagicMock()
        mock_chat_msg.__enter__ = MagicMock(return_value=mock_chat_msg)
        mock_chat_msg.__exit__ = MagicMock(return_value=False)
        st.chat_message = MagicMock(return_value=mock_chat_msg)
        st.chat_input = MagicMock(return_value=None)
        st.spinner = MagicMock(return_value=mock_expander)
        st.rerun = MagicMock()
        st.query_params = {}
        st.code = MagicMock()
        st.download_button = MagicMock()
        
        yield st


@pytest.fixture
def mock_session_state():
    """Mock Streamlit session_state"""
    return SessionStateMock({
        'boot_ready': False,
        'messages': [],
        'current_sources_map': {},
        'current_reasoning_map': {},
    })


@pytest.fixture
def mock_rag_service():
    """Mock RAGService"""
    service = MagicMock()
    service.query = MagicMock(return_value={
        'answer': 'Test answer',
        'sources': [],
        'reasoning_content': None,
    })
    service.stream_query = MagicMock(return_value=iter(['Test ', 'answer']))
    return service


@pytest.fixture
def mock_chat_manager():
    """Mock ChatManager"""
    manager = MagicMock()
    manager.current_session = None
    manager.get_session = MagicMock(return_value=None)
    manager.create_session = MagicMock(return_value='session_1')
    manager.load_session = MagicMock(return_value=None)
    manager.save_session = MagicMock()
    manager.list_sessions = MagicMock(return_value=[])
    return manager


@pytest.fixture
def mock_index_manager():
    """Mock IndexManager"""
    manager = MagicMock()
    manager.index = MagicMock()
    manager.is_ready = MagicMock(return_value=True)
    manager.close = MagicMock()
    return manager

