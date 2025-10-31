#!/usr/bin/env python3
"""
向量库版本管理演示

展示如何使用版本化向量库功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.vector_version_utils import (
    get_vector_store_path,
    list_versions,
    cleanup_old_versions,
    migrate_existing_to_versioned
)


def demo_list_versions():
    """演示：列出所有版本"""
    print("\n" + "="*60)
    print("📚 演示 1: 列出所有版本")
    print("="*60)
    
    versions = list_versions()
    
    if not versions:
        print("📭 当前没有任何版本")
        print("💡 提示：使用 migrate 命令迁移现有向量库")
        return
    
    print(f"\n找到 {len(versions)} 个版本:\n")
    print(f"{'版本名称':<30} {'大小':<12} {'状态':<10}")
    print("-" * 55)
    
    for v in versions:
        status = "✓ 当前" if v["is_current"] else ""
        print(f"{v['name']:<30} {v['size_mb']:>8.1f} MB  {status}")


def demo_get_latest_version():
    """演示：获取最新版本路径"""
    print("\n" + "="*60)
    print("📂 演示 2: 获取最新版本路径")
    print("="*60)
    
    latest_path = get_vector_store_path(create_new_version=False)
    print(f"\n当前使用的版本路径: {latest_path}")


def demo_create_new_version():
    """演示：创建新版本（仅演示，不实际创建）"""
    print("\n" + "="*60)
    print("📁 演示 3: 创建新版本")
    print("="*60)
    
    print("\n如果要创建新版本，可以使用:")
    print("```python")
    print("from src.vector_version_utils import get_vector_store_path")
    print("new_version = get_vector_store_path(create_new_version=True)")
    print("print(f'新版本路径: {new_version}')")
    print("```")
    
    print("\n⚠️  注意：此演示不会实际创建新版本")


def demo_migrate():
    """演示：迁移现有向量库"""
    print("\n" + "="*60)
    print("📦 演示 4: 迁移现有向量库到版本化格式")
    print("="*60)
    
    print("\n检查是否有旧格式的向量库...")
    
    base_path = Path("vector_store")
    old_sqlite = base_path / "chroma.sqlite3"
    
    if old_sqlite.exists():
        print("✅ 检测到旧格式的向量库")
        print("\n可以运行以下命令进行迁移:")
        print("```bash")
        print("python scripts/manage_vector_versions.py migrate")
        print("```")
    else:
        print("ℹ️  未检测到旧格式的向量库（chroma.sqlite3）")
        print("   可能已经是版本化格式，或者尚未创建向量库")


def demo_cleanup():
    """演示：清理旧版本"""
    print("\n" + "="*60)
    print("🗑️  演示 5: 清理旧版本")
    print("="*60)
    
    versions = list_versions()
    
    if len(versions) <= 3:
        print(f"\nℹ️  当前版本数({len(versions)}) <= 3，无需清理")
        print("💡 提示：清理功能会保留最近 N 个版本，删除更旧的版本")
    else:
        print(f"\n当前有 {len(versions)} 个版本")
        print("如果要清理旧版本（保留最近3个），可以运行:")
        print("```bash")
        print("python scripts/manage_vector_versions.py cleanup --keep 3")
        print("```")


def demo_usage_workflow():
    """演示：完整的使用工作流"""
    print("\n" + "="*60)
    print("🔧 演示 6: 完整的使用工作流")
    print("="*60)
    
    print("\n【场景】：显卡机器生成向量，轻量机器使用")
    print("\n1️⃣  显卡机器（生产者）:")
    print("   ```bash")
    print("   # 导入新文档（会自动使用版本化路径）")
    print("   python main.py import-docs --directory data/new_docs/")
    print("   ")
    print("   # 提交到 Git")
    print("   git add vector_store/version_*")
    print("   git add data/")
    print("   git commit -m '导入新文档并生成向量'")
    print("   git push")
    print("   ```")
    
    print("\n2️⃣  轻量机器（消费者）:")
    print("   ```bash")
    print("   # 拉取最新代码和向量库")
    print("   git pull")
    print("   ")
    print("   # 启动应用（自动使用最新版本）")
    print("   make run")
    print("   ```")
    
    print("\n💡 核心优势：")
    print("   - 显卡机器：生成向量约 5 分钟")
    print("   - 轻量机器：Git 拉取约 10 秒")
    print("   - 节省时间：99.4% ⭐")


def main():
    """主函数"""
    print("\n" + "🎯 " * 20)
    print("       向量库版本管理功能演示")
    print("🎯 " * 20)
    
    # 运行所有演示
    demo_list_versions()
    demo_get_latest_version()
    demo_create_new_version()
    demo_migrate()
    demo_cleanup()
    demo_usage_workflow()
    
    print("\n" + "="*60)
    print("✅ 演示完成！")
    print("="*60)
    
    print("\n📚 更多信息：")
    print("   - 详细文档: docs/VECTOR_VERSION_GUIDE.md")
    print("   - 管理工具: scripts/manage_vector_versions.py")
    print("   - 快速入门: README.md")
    
    print("\n💡 常用命令：")
    print("   python scripts/manage_vector_versions.py list       # 列出版本")
    print("   python scripts/manage_vector_versions.py migrate    # 迁移现有库")
    print("   python scripts/manage_vector_versions.py cleanup    # 清理旧版本")
    
    print()


if __name__ == "__main__":
    main()

