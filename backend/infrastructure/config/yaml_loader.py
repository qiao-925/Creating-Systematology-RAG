"""
YAML配置加载器 - 从 application.yml 加载配置

主要功能：
- load_yaml_config()：加载并解析 application.yml 文件
"""

from pathlib import Path
from typing import Dict, Any

import yaml


def load_yaml_config(project_root: Path) -> Dict[str, Any]:
    """加载 YAML 配置文件
    
    Args:
        project_root: 项目根目录路径
        
    Returns:
        配置字典，如果文件不存在或加载失败返回空字典
    """
    config_file = project_root / "application.yml"
    
    if not config_file.exists():
        return {}
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        return config
    except Exception as e:
        # 延迟导入避免循环依赖
        try:
            from backend.infrastructure.logger import get_logger
            logger = get_logger('config')
            logger.warning("加载 YAML 配置失败，回退到环境变量模式", error=str(e))
        except Exception:
            pass  # 如果logger不可用，静默失败
        return {}
