"""
Agent 测试信息查询工具

查询测试文件的详细信息，帮助 Agent 理解测试的目的和覆盖范围。
"""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, List


class TestInfoQuery:
    """测试信息查询器"""
    
    def __init__(self, index_file: Path):
        """初始化"""
        self.index_file = index_file
        self.index_data: Optional[dict] = None
    
    def load_index(self):
        """加载测试索引"""
        if not self.index_file.exists():
            print(f"错误: 索引文件不存在: {self.index_file}", file=sys.stderr)
            print(f"请先运行: python tests/tools/generate_test_index.py", file=sys.stderr)
            sys.exit(1)
        
        with open(self.index_file, 'r', encoding='utf-8') as f:
            self.index_data = json.load(f)
    
    def find_test(self, test_path: str) -> Optional[Dict]:
        """查找测试文件信息"""
        if not self.index_data:
            self.load_index()
        
        # 标准化路径
        test_path_normalized = self._normalize_path(test_path)
        
        for test_file in self.index_data.get("test_files", []):
            file_path = self._normalize_path(test_file.get("file_path", ""))
            if test_path_normalized in file_path or file_path in test_path_normalized:
                return test_file
        
        return None
    
    def _normalize_path(self, path: str) -> str:
        """标准化路径"""
        return path.replace('\\', '/').lower()
    
    def print_test_info(self, test_path: str, format: str = "human"):
        """打印测试信息"""
        test_info = self.find_test(test_path)
        
        if not test_info:
            print(f"[ERROR] 未找到测试文件: {test_path}", file=sys.stderr)
            print(f"\n可用的测试文件:", file=sys.stderr)
            if self.index_data:
                for test_file in self.index_data.get("test_files", [])[:10]:
                    print(f"  - {test_file['file_path']}", file=sys.stderr)
            sys.exit(1)
        
        if format == "json":
            import json
            print(json.dumps(test_info, indent=2, ensure_ascii=False))
            return
        
        # 人类可读格式
        print(f"[INFO] 测试文件信息\n")
        print(f"文件路径: {test_info['file_path']}")
        print(f"分类: {test_info.get('category', 'unknown')}")
        print(f"测试数量: {test_info.get('test_count', 0)}")
        
        if test_info.get('description'):
            print(f"\n描述:")
            print(f"  {test_info['description']}")
        
        if test_info.get('target_module'):
            print(f"\n目标模块: {test_info['target_module']}")
        
        if test_info.get('target_class'):
            print(f"目标类: {test_info['target_class']}")
        
        if test_info.get('source_files'):
            print(f"\n对应的源文件:")
            for source_file in test_info['source_files']:
                print(f"  - {source_file}")
        
        if test_info.get('coverage'):
            print(f"\n覆盖的功能:")
            for func in test_info['coverage'][:10]:  # 只显示前10个
                print(f"  - {func}")
            if len(test_info['coverage']) > 10:
                print(f"  ... 还有 {len(test_info['coverage']) - 10} 个")
        
        if test_info.get('tags'):
            print(f"\n标签: {', '.join(test_info['tags'])}")
        
        if test_info.get('pytest_markers'):
            print(f"Pytest 标记: {', '.join(test_info['pytest_markers'])}")
        
        if test_info.get('fixtures_used'):
            print(f"\n使用的 Fixtures:")
            for fixture in test_info['fixtures_used'][:10]:
                print(f"  - {fixture}")
            if len(test_info['fixtures_used']) > 10:
                print(f"  ... 还有 {len(test_info['fixtures_used']) - 10} 个")
        
        if test_info.get('dependencies'):
            print(f"\n依赖:")
            for dep in test_info['dependencies']:
                print(f"  - {dep}")
        
        if test_info.get('related_tests'):
            print(f"\n相关测试:")
            for related in test_info['related_tests']:
                print(f"  - {related}")
        
        # 生成运行命令
        print(f"\n[CMD] 运行测试命令:")
        print(f"pytest {test_info['file_path']} -v")
    
    def list_tests_by_category(self, category: Optional[str] = None):
        """列出测试文件（可按分类筛选）"""
        if not self.index_data:
            self.load_index()
        
        tests = self.index_data.get("test_files", [])
        
        if category:
            tests = [t for t in tests if t.get('category') == category]
        
        if not tests:
            print(f"未找到 {'分类为 ' + category + ' 的' if category else ''}测试文件")
            return
        
        print(f"[INFO] 找到 {len(tests)} 个测试文件:\n")
        
        for test in sorted(tests, key=lambda x: x['file_path']):
            print(f"  {test['file_path']}")
            print(f"    分类: {test.get('category', 'unknown')}")
            print(f"    测试数: {test.get('test_count', 0)}")
            if test.get('target_module'):
                print(f"    目标: {test['target_module']}")
            print()
    
    def validate_index(self):
        """验证索引完整性"""
        if not self.index_data:
            self.load_index()
        
        issues = []
        
        for test_file in self.index_data.get("test_files", []):
            file_path = Path(self.index_file.parent.parent / test_file["file_path"])
            if not file_path.exists():
                issues.append(f"测试文件不存在: {test_file['file_path']}")
            
            # 检查源文件
            for source_file in test_file.get("source_files", []):
                source_path = Path(self.index_file.parent.parent / source_file)
                if not source_path.exists():
                    issues.append(f"源文件不存在: {source_file} (测试: {test_file['file_path']})")
        
        if issues:
            print("[WARN] 发现以下问题:\n")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("[OK] 索引验证通过")
            return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="查询测试文件详细信息",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查询测试文件信息
  python tests/tools/agent_test_info.py tests/unit/test_indexer.py

  # JSON 格式输出
  python tests/tools/agent_test_info.py tests/unit/test_indexer.py --format json

  # 列出所有单元测试
  python tests/tools/agent_test_info.py --list --category unit

  # 验证索引完整性
  python tests/tools/agent_test_info.py --validate
        """
    )
    parser.add_argument(
        "test_path",
        nargs="?",
        help="测试文件路径（相对于项目根目录）"
    )
    parser.add_argument(
        "-i", "--index",
        type=Path,
        default=Path(__file__).parent.parent / "test_index.json",
        help="测试索引文件路径（默认: tests/test_index.json）"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["human", "json"],
        default="human",
        help="输出格式（默认: human）"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有测试文件"
    )
    parser.add_argument(
        "--category",
        help="筛选分类（与 --list 一起使用）"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="验证索引完整性"
    )
    
    args = parser.parse_args()
    
    query = TestInfoQuery(args.index)
    
    if args.validate:
        success = query.validate_index()
        sys.exit(0 if success else 1)
    elif args.list:
        query.list_tests_by_category(args.category)
    elif args.test_path:
        query.print_test_info(args.test_path, format=args.format)
    else:
        parser.print_help()
        sys.exit(1)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

