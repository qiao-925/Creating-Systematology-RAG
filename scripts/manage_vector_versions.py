#!/usr/bin/env python3
"""
向量库版本管理工具

功能：
1. 列出所有版本
2. 切换到指定版本
3. 清理旧版本
4. 迁移现有向量库到版本化格式
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class VectorVersionManager:
    """向量库版本管理器"""
    
    def __init__(self, base_dir: str = "vector_store"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.current_link = self.base_dir / "current"
    
    def list_versions(self) -> List[tuple]:
        """列出所有版本
        
        Returns:
            [(version_name, path, size_mb, is_current), ...]
        """
        versions = []
        version_dirs = sorted(self.base_dir.glob("version_*"), reverse=True)
        
        current_target = None
        if self.current_link.exists():
            current_target = self.current_link.resolve()
        
        for version_dir in version_dirs:
            size_mb = self._get_dir_size(version_dir) / (1024 * 1024)
            is_current = (current_target == version_dir.resolve())
            versions.append((
                version_dir.name,
                str(version_dir),
                size_mb,
                is_current
            ))
        
        return versions
    
    def _get_dir_size(self, path: Path) -> int:
        """计算目录大小（字节）"""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception:
            pass
        return total
    
    def get_latest_version(self) -> Optional[Path]:
        """获取最新版本"""
        versions = sorted(self.base_dir.glob("version_*"))
        return versions[-1] if versions else None
    
    def create_version(self, timestamp: Optional[str] = None) -> Path:
        """创建新版本目录
        
        Args:
            timestamp: 时间戳字符串（YYYYMMDD_HHMMSS），None 则使用当前时间
        
        Returns:
            新版本目录路径
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        version_dir = self.base_dir / f"version_{timestamp}"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ 创建新版本: {version_dir.name}")
        return version_dir
    
    def set_current(self, version_name: str):
        """设置当前使用的版本
        
        Args:
            version_name: 版本名称（如 version_20251031_143022）
        """
        version_dir = self.base_dir / version_name
        
        if not version_dir.exists():
            print(f"❌ 版本不存在: {version_name}")
            return False
        
        # 删除旧的符号链接
        if self.current_link.exists() or self.current_link.is_symlink():
            self.current_link.unlink()
        
        # 创建新的符号链接
        try:
            self.current_link.symlink_to(version_dir.name)
            print(f"✅ 已切换到版本: {version_name}")
            return True
        except Exception as e:
            print(f"❌ 切换失败: {e}")
            return False
    
    def cleanup_old_versions(self, keep: int = 3):
        """清理旧版本，保留最近N个
        
        Args:
            keep: 保留的版本数量
        """
        versions = sorted(self.base_dir.glob("version_*"))
        
        if len(versions) <= keep:
            print(f"ℹ️  当前版本数({len(versions)}) <= 保留数({keep})，无需清理")
            return
        
        to_remove = versions[:-keep]
        
        print(f"🗑️  将删除 {len(to_remove)} 个旧版本:")
        for version_dir in to_remove:
            size_mb = self._get_dir_size(version_dir) / (1024 * 1024)
            print(f"   - {version_dir.name} ({size_mb:.1f} MB)")
        
        confirm = input("\n确认删除？(y/N): ")
        if confirm.lower() != 'y':
            print("❌ 已取消")
            return
        
        for version_dir in to_remove:
            try:
                shutil.rmtree(version_dir)
                print(f"✅ 已删除: {version_dir.name}")
            except Exception as e:
                print(f"❌ 删除失败 {version_dir.name}: {e}")
    
    def migrate_existing(self):
        """迁移现有的向量库到版本化格式"""
        # 检查是否有旧格式的文件
        old_sqlite = self.base_dir / "chroma.sqlite3"
        
        if not old_sqlite.exists():
            print("ℹ️  未找到旧格式的向量库")
            return
        
        print("📦 检测到旧格式的向量库，开始迁移...")
        
        # 创建新版本（使用文件修改时间作为时间戳）
        mtime = datetime.fromtimestamp(old_sqlite.stat().st_mtime)
        timestamp = mtime.strftime("%Y%m%d_%H%M%S")
        new_version = self.create_version(timestamp)
        
        # 移动文件
        moved_files = []
        for item in self.base_dir.iterdir():
            if item.is_file() or (item.is_dir() and item.name != new_version.name and not item.name.startswith('.')):
                dest = new_version / item.name
                print(f"   移动: {item.name}")
                shutil.move(str(item), str(dest))
                moved_files.append(item.name)
        
        if moved_files:
            print(f"✅ 已迁移 {len(moved_files)} 个文件/目录到: {new_version.name}")
            self.set_current(new_version.name)
        else:
            print("⚠️  没有文件需要迁移")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="向量库版本管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 列出所有版本
  python scripts/manage_vector_versions.py list
  
  # 切换到指定版本
  python scripts/manage_vector_versions.py switch version_20251031_143022
  
  # 清理旧版本（保留最近3个）
  python scripts/manage_vector_versions.py cleanup --keep 3
  
  # 迁移现有向量库到版本化格式
  python scripts/manage_vector_versions.py migrate
        """
    )
    
    parser.add_argument(
        'action',
        choices=['list', 'switch', 'cleanup', 'migrate'],
        help='操作类型'
    )
    parser.add_argument(
        'version',
        nargs='?',
        help='版本名称（用于 switch）'
    )
    parser.add_argument(
        '--keep',
        type=int,
        default=3,
        help='保留的版本数量（用于 cleanup，默认3）'
    )
    parser.add_argument(
        '--base-dir',
        default='vector_store',
        help='向量库根目录（默认 vector_store）'
    )
    
    args = parser.parse_args()
    
    manager = VectorVersionManager(args.base_dir)
    
    if args.action == 'list':
        versions = manager.list_versions()
        
        if not versions:
            print("📭 未找到任何版本")
            return
        
        print(f"\n📚 找到 {len(versions)} 个版本:\n")
        print(f"{'版本名称':<30} {'大小':<12} {'状态':<10}")
        print("-" * 55)
        
        for name, path, size_mb, is_current in versions:
            status = "✓ 当前" if is_current else ""
            print(f"{name:<30} {size_mb:>8.1f} MB  {status}")
        
        print()
    
    elif args.action == 'switch':
        if not args.version:
            print("❌ 请指定版本名称")
            return
        
        manager.set_current(args.version)
    
    elif args.action == 'cleanup':
        manager.cleanup_old_versions(keep=args.keep)
    
    elif args.action == 'migrate':
        manager.migrate_existing()


if __name__ == "__main__":
    main()

