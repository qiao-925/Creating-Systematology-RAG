"""
网页数据源
从网络URL获取内容并保存为文件
"""

import tempfile
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse
from src.data_source.base import DataSource, SourceFile
from src.logger import setup_logger

try:
    from llama_index.readers.web import SimpleWebPageReader
except ImportError:
    SimpleWebPageReader = None

logger = setup_logger('web_source')


class WebSource(DataSource):
    """网页数据源"""
    
    def __init__(
        self,
        urls: List[str],
        temp_dir: Optional[Path] = None
    ):
        """初始化网页数据源
        
        Args:
            urls: URL列表
            temp_dir: 临时目录路径（用于保存下载的网页）
        """
        self.urls = urls
        self.temp_dir = temp_dir
        self._cleanup_temp = False
    
    def get_source_metadata(self) -> dict:
        """获取数据源的元数据"""
        return {
            'source_type': 'web',
            'url_count': len(self.urls),
            'urls': self.urls
        }
    
    def get_file_paths(self) -> List[SourceFile]:
        """获取网页文件的路径列表
        
        下载网页内容并保存为临时HTML文件
        
        Returns:
            文件路径列表
        """
        if SimpleWebPageReader is None:
            logger.error("SimpleWebPageReader 未安装")
            return []
        
        if not self.urls:
            logger.warning("URL 列表为空")
            return []
        
        try:
            # 创建临时目录
            if self.temp_dir is None:
                self.temp_dir = Path(tempfile.mkdtemp(prefix="rag_web_"))
                self._cleanup_temp = True
            
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            source_files = []
            source_metadata = self.get_source_metadata()
            
            # 使用 SimpleWebPageReader 下载网页内容
            reader = SimpleWebPageReader(html_to_text=False)  # 保留HTML以便保存
            
            for url in self.urls:
                try:
                    # 下载网页内容
                    documents = reader.load_data([url])
                    
                    if not documents:
                        logger.warning(f"未能加载网页: {url}")
                        continue
                    
                    # 生成文件名
                    parsed_url = urlparse(url)
                    filename = parsed_url.path.strip('/').replace('/', '_') or 'index'
                    if not filename.endswith('.html'):
                        filename += '.html'
                    
                    file_path = self.temp_dir / filename
                    
                    # 保存内容到文件
                    # SimpleWebPageReader返回的document可能包含HTML或文本
                    content = documents[0].text if documents else ""
                    
                    # 如果内容不是HTML格式，包装为HTML
                    if not content.strip().startswith('<'):
                        content = f"<html><body><h1>{url}</h1><div>{content}</div></body></html>"
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    source_files.append(SourceFile(
                        path=file_path,
                        source_type='web',
                        metadata={
                            **source_metadata,
                            'url': url,
                            'file_name': filename,
                            'domain': parsed_url.netloc
                        }
                    ))
                    
                    logger.info(f"已下载网页: {url} -> {file_path}")
                    
                except Exception as e:
                    logger.error(f"下载网页失败 {url}: {e}")
                    continue
            
            logger.info(f"找到 {len(source_files)} 个网页文件")
            return source_files
            
        except Exception as e:
            logger.error(f"获取网页文件路径失败: {e}")
            return []
    
    def cleanup(self):
        """清理临时文件"""
        if self._cleanup_temp and self.temp_dir and self.temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"已清理临时目录: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"清理临时目录失败: {e}")
    
    def __del__(self):
        """析构函数，自动清理临时文件"""
        self.cleanup()

