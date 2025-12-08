"""
本地文件数据源：从本地目录或上传的文件获取文件路径

主要功能：
- LocalFileSource类：本地文件数据源，实现DataSource接口
- get_file_paths()：从本地目录或上传文件获取文件路径列表

执行流程：
1. 初始化本地数据源（目录路径或上传文件）
2. 处理上传文件（保存到临时目录）
3. 扫描文件路径
4. 构建SourceFile列表
5. 返回文件路径列表

特性：
- 支持本地目录
- 支持Streamlit上传文件
- 临时目录管理
- 递归扫描支持
"""

import tempfile
from pathlib import Path
from typing import List, Union, Optional
from src.infrastructure.data_loader.source.base import DataSource, SourceFile
from src.infrastructure.logger import get_logger

logger = get_logger('local_source')


class LocalFileSource(DataSource):
    """本地文件数据源"""
    
    def __init__(
        self,
        source: Union[str, Path, List, None],
        recursive: bool = True,
        temp_dir: Optional[Path] = None
    ):
        """初始化本地文件数据源
        
        Args:
            source: 数据源，可以是：
                - 目录路径（字符串或Path）
                - Streamlit UploadedFile 对象列表
                - None（用于临时目录）
            recursive: 是否递归遍历目录（仅当source是目录时有效）
            temp_dir: 临时目录路径（用于保存上传的文件）
        """
        self.source = source
        self.recursive = recursive
        self.temp_dir = temp_dir
        self._cleanup_temp = False
    
    def get_source_metadata(self) -> dict:
        """获取数据源的元数据"""
        if isinstance(self.source, (str, Path)):
            return {
                'source_path': str(self.source),
                'source_type': 'local_directory'
            }
        elif isinstance(self.source, list):
            return {
                'source_type': 'local_upload',
                'file_count': len(self.source)
            }
        else:
            return {'source_type': 'local'}
    
    def get_file_paths(self) -> List[SourceFile]:
        """获取本地文件路径列表
        
        Returns:
            文件路径列表
        """
        try:
            source_files = []
            source_metadata = self.get_source_metadata()
            
            if isinstance(self.source, (str, Path)):
                # 目录路径
                directory_path = Path(self.source)
                if not directory_path.exists() or not directory_path.is_dir():
                    logger.error(f"[阶段1.2] 目录不存在或不是有效目录: {directory_path}")
                    return []
                
                # 遍历目录获取文件
                pattern = "**/*" if self.recursive else "*"
                for file_path in directory_path.rglob(pattern) if self.recursive else directory_path.glob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(directory_path)
                        source_files.append(SourceFile(
                            path=file_path,
                            source_type='local',
                            metadata={
                                **source_metadata,
                                'file_path': str(relative_path),
                                'file_name': file_path.name
                            }
                        ))
            
            elif isinstance(self.source, list):
                # Streamlit UploadedFile 对象列表
                # 需要先保存到临时目录
                if self.temp_dir is None:
                    self.temp_dir = Path(tempfile.mkdtemp(prefix="rag_upload_"))
                    self._cleanup_temp = True
                
                self.temp_dir.mkdir(parents=True, exist_ok=True)
                
                for uploaded_file in self.source:
                    # 保存上传的文件到临时目录
                    file_path = self.temp_dir / uploaded_file.name
                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.getvalue())
                    
                    source_files.append(SourceFile(
                        path=file_path,
                        source_type='local',
                        metadata={
                            **source_metadata,
                            'file_name': uploaded_file.name,
                            'original_name': uploaded_file.name
                        }
                    ))
            
            logger.info(f"[阶段1.2] 找到 {len(source_files)} 个本地文件")
            return source_files
            
        except Exception as e:
            logger.error(f"[阶段1.2] 获取本地文件路径失败: {e}")
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
