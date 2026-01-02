"""
测试 frontend/components/file_viewer.py
对应源文件：frontend/components/file_viewer.py
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path
from frontend.components.file_viewer import (
    resolve_file_path,
    get_relative_path,
    display_file_info,
    display_markdown_file,
    display_pdf_file,
)


class TestFileViewer:
    """测试文件查看组件"""
    
    @patch('frontend.components.file_viewer.config')
    def test_resolve_file_path_empty(self, mock_config):
        """测试空路径"""
        result = resolve_file_path("")
        assert result is None
    
    @patch('frontend.components.file_viewer.config')
    def test_resolve_file_path_absolute_exists(self, mock_config, tmp_path):
        """测试绝对路径存在"""
        test_file = tmp_path / "test.md"
        test_file.write_text("test")
        
        result = resolve_file_path(str(test_file))
        assert result == test_file
    
    @patch('frontend.components.file_viewer.config')
    def test_resolve_file_path_absolute_not_exists(self, mock_config):
        """测试绝对路径不存在"""
        result = resolve_file_path("/nonexistent/path/file.md")
        assert result is None
    
    @patch('frontend.components.file_viewer.config')
    def test_resolve_file_path_relative(self, mock_config, tmp_path):
        """测试相对路径解析"""
        mock_config.PROJECT_ROOT = tmp_path
        mock_config.RAW_DATA_PATH = tmp_path / "raw"
        mock_config.PROCESSED_DATA_PATH = tmp_path / "processed"
        
        # 创建测试文件
        test_file = tmp_path / "test.md"
        test_file.write_text("test")
        
        result = resolve_file_path("test.md")
        assert result == test_file
    
    @patch('frontend.components.file_viewer.config')
    def test_get_relative_path_in_project(self, mock_config, tmp_path):
        """测试获取项目内的相对路径"""
        mock_config.PROJECT_ROOT = tmp_path
        test_file = tmp_path / "subdir" / "test.md"
        test_file.parent.mkdir()
        test_file.write_text("test")
        
        result = get_relative_path(test_file)
        assert result == "subdir/test.md"
    
    @patch('frontend.components.file_viewer.config')
    def test_get_relative_path_outside_project(self, mock_config, tmp_path):
        """测试获取项目外的路径（返回绝对路径）"""
        mock_config.PROJECT_ROOT = tmp_path
        outside_file = Path("/outside/path/test.md")
        
        result = get_relative_path(outside_file)
        assert result == str(outside_file)
    
    @patch('frontend.components.file_viewer.st')
    @patch('frontend.components.file_viewer.get_relative_path')
    def test_display_file_info(self, mock_get_relative, mock_st, tmp_path):
        """测试显示文件信息"""
        test_file = tmp_path / "test.md"
        test_file.write_text("test")
        mock_get_relative.return_value = "test.md"
        
        mock_expander = MagicMock()
        mock_st.expander.return_value.__enter__ = MagicMock(return_value=mock_expander)
        mock_st.expander.return_value.__exit__ = MagicMock(return_value=False)
        
        display_file_info(test_file)
        
        # 验证基本组件被调用
        mock_st.markdown.assert_called()
        mock_st.caption.assert_called()
        mock_st.expander.assert_called_once()
    
    @patch('frontend.components.file_viewer.st')
    def test_display_markdown_file_success(self, mock_st, tmp_path):
        """测试成功显示Markdown文件"""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Markdown")
        
        display_markdown_file(test_file)
        
        # 验证 markdown 被调用
        mock_st.markdown.assert_called_once_with("# Test Markdown")
    
    @patch('frontend.components.file_viewer.st')
    def test_display_markdown_file_encoding_error(self, mock_st, tmp_path):
        """测试Markdown文件编码错误处理"""
        test_file = tmp_path / "test.md"
        # 创建一个会导致编码错误的文件（模拟）
        with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'error')):
            with patch('frontend.components.file_viewer.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'error')):
                display_markdown_file(test_file)
                # 应该尝试其他编码或显示错误
                mock_st.error.assert_called()
    
    @patch('frontend.components.file_viewer.st')
    @patch('base64.b64encode')
    def test_display_pdf_file_success(self, mock_b64encode, mock_st, tmp_path):
        """测试成功显示PDF文件"""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"fake pdf content")
        mock_b64encode.return_value.decode.return_value = "base64_content"
        
        display_pdf_file(test_file)
        
        # 验证 markdown 和 download_button 被调用
        mock_st.markdown.assert_called_once()
        mock_st.download_button.assert_called_once()
    

