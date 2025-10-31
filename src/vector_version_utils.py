"""
向量库版本管理工具函数

提供版本自动检测和路径解析功能，集成到 IndexManager 中
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from src.logger import setup_logger

logger = setup_logger('vector_version')


def get_vector_store_path(
    base_dir: str = "vector_store",
    create_new_version: bool = False,
    version_timestamp: Optional[str] = None
) -> Path:
    """获取向量库存储路径（支持版本化）
    
    Args:
        base_dir: 向量库根目录
        create_new_version: 是否创建新版本（用于导入新数据时）
        version_timestamp: 指定版本时间戳（如果为None且create_new_version=True，则使用当前时间）
    
    Returns:
        Path: 向量库存储路径
        
    行为:
        - 如果 create_new_version=True: 创建新版本目录 version_YYYYMMDD_HHMMSS/
        - 如果 create_new_version=False: 
            1. 优先使用 current 符号链接指向的版本
            2. 如果没有符号链接，使用最新的 version_* 目录
            3. 如果没有任何版本，使用根目录（兼容旧格式）
    """
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)
    
    # 场景1：创建新版本
    if create_new_version:
        if version_timestamp is None:
            version_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        version_dir = base_path / f"version_{version_timestamp}"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 创建新版本: {version_dir}")
        print(f"📁 创建新版本: {version_dir.name}")
        
        # 更新 current 符号链接
        _update_current_link(base_path, version_dir)
        
        return version_dir
    
    # 场景2：加载现有版本
    # 优先级1：使用 current 符号链接
    current_link = base_path / "current"
    if current_link.exists() and current_link.is_symlink():
        target = current_link.resolve()
        if target.exists():
            logger.info(f"📂 使用 current 链接指向的版本: {target.name}")
            print(f"📂 加载版本: {target.name}")
            return target
        else:
            logger.warning(f"⚠️  current 链接指向不存在的目录: {target}")
    
    # 优先级2：查找最新的 version_* 目录
    versions = sorted(base_path.glob("version_*"))
    if versions:
        latest_version = versions[-1]
        logger.info(f"📂 使用最新版本: {latest_version.name}")
        print(f"📂 加载版本: {latest_version.name}")
        
        # 自动创建 current 符号链接
        _update_current_link(base_path, latest_version)
        
        return latest_version
    
    # 优先级3：兼容旧格式（直接使用根目录）
    logger.warning(f"⚠️  未找到版本化目录，使用根目录（旧格式）: {base_path}")
    print(f"⚠️  未找到版本化目录，使用根目录（建议运行 migrate 迁移到版本化格式）")
    return base_path


def _update_current_link(base_path: Path, target_dir: Path):
    """更新 current 符号链接
    
    Args:
        base_path: 向量库根目录
        target_dir: 目标版本目录
    """
    current_link = base_path / "current"
    
    try:
        # 删除旧的符号链接（如果存在）
        if current_link.exists() or current_link.is_symlink():
            current_link.unlink()
        
        # 创建新的符号链接（使用相对路径）
        relative_target = target_dir.relative_to(base_path)
        current_link.symlink_to(relative_target)
        
        logger.debug(f"✅ 已更新 current 链接 -> {relative_target}")
    except Exception as e:
        logger.warning(f"⚠️  无法更新 current 符号链接: {e}")


def list_versions(base_dir: str = "vector_store") -> list[dict]:
    """列出所有版本
    
    Args:
        base_dir: 向量库根目录
    
    Returns:
        版本列表: [{"name": "version_...", "path": Path, "size_mb": float, "is_current": bool}, ...]
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        return []
    
    # 获取 current 链接的目标
    current_link = base_path / "current"
    current_target = None
    if current_link.exists() and current_link.is_symlink():
        current_target = current_link.resolve()
    
    versions = []
    for version_dir in sorted(base_path.glob("version_*"), reverse=True):
        if not version_dir.is_dir():
            continue
        
        # 计算目录大小
        size_bytes = sum(
            f.stat().st_size 
            for f in version_dir.rglob('*') 
            if f.is_file()
        )
        size_mb = size_bytes / (1024 * 1024)
        
        is_current = (current_target and current_target.resolve() == version_dir.resolve())
        
        versions.append({
            "name": version_dir.name,
            "path": version_dir,
            "size_mb": size_mb,
            "is_current": is_current
        })
    
    return versions


def cleanup_old_versions(base_dir: str = "vector_store", keep: int = 3, dry_run: bool = False):
    """清理旧版本，保留最近N个
    
    Args:
        base_dir: 向量库根目录
        keep: 保留的版本数量
        dry_run: 是否仅模拟（不实际删除）
    
    Returns:
        删除的版本列表
    """
    import shutil
    
    base_path = Path(base_dir)
    versions = sorted(base_path.glob("version_*"))
    
    if len(versions) <= keep:
        logger.info(f"ℹ️  当前版本数({len(versions)}) <= 保留数({keep})，无需清理")
        return []
    
    to_remove = versions[:-keep]
    removed = []
    
    for version_dir in to_remove:
        if dry_run:
            logger.info(f"[模拟] 将删除: {version_dir.name}")
            print(f"[模拟] 将删除: {version_dir.name}")
        else:
            try:
                shutil.rmtree(version_dir)
                logger.info(f"🗑️  已删除: {version_dir.name}")
                print(f"🗑️  已删除: {version_dir.name}")
                removed.append(str(version_dir))
            except Exception as e:
                logger.error(f"❌ 删除失败 {version_dir.name}: {e}")
                print(f"❌ 删除失败 {version_dir.name}: {e}")
    
    return removed


def migrate_existing_to_versioned(base_dir: str = "vector_store"):
    """迁移现有的向量库到版本化格式
    
    Args:
        base_dir: 向量库根目录
    
    Returns:
        是否成功迁移
    """
    import shutil
    
    base_path = Path(base_dir)
    
    if not base_path.exists():
        logger.info("ℹ️  向量库目录不存在，无需迁移")
        return False
    
    # 检查是否有旧格式的文件
    old_sqlite = base_path / "chroma.sqlite3"
    
    if not old_sqlite.exists():
        logger.info("ℹ️  未找到旧格式的向量库（chroma.sqlite3）")
        return False
    
    print("📦 检测到旧格式的向量库，开始迁移到版本化格式...")
    logger.info("开始迁移旧格式向量库")
    
    # 创建新版本（使用文件修改时间作为时间戳）
    mtime = datetime.fromtimestamp(old_sqlite.stat().st_mtime)
    timestamp = mtime.strftime("%Y%m%d_%H%M%S")
    
    new_version = get_vector_store_path(
        base_dir=base_dir,
        create_new_version=True,
        version_timestamp=timestamp
    )
    
    # 移动文件
    moved_files = []
    for item in base_path.iterdir():
        # 跳过版本目录、符号链接和隐藏文件
        if item.name.startswith('version_') or item.name == 'current' or item.name.startswith('.'):
            continue
        
        if item.is_file() or item.is_dir():
            dest = new_version / item.name
            try:
                print(f"   移动: {item.name}")
                shutil.move(str(item), str(dest))
                moved_files.append(item.name)
                logger.info(f"已移动: {item.name} -> {new_version.name}")
            except Exception as e:
                logger.error(f"移动失败 {item.name}: {e}")
                print(f"❌ 移动失败 {item.name}: {e}")
    
    if moved_files:
        print(f"✅ 已迁移 {len(moved_files)} 个文件/目录到: {new_version.name}")
        logger.info(f"迁移完成: {len(moved_files)} 个文件/目录 -> {new_version.name}")
        return True
    else:
        print("⚠️  没有文件需要迁移")
        logger.warning("没有文件需要迁移")
        return False

