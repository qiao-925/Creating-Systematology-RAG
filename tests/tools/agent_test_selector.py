"""
Agent 测试智能选择工具

根据修改的源文件，自动选择相关的测试文件。
"""

import json
import sys
from pathlib import Path
from typing import List, Set, Optional


class TestSelector:
    """测试选择器"""
    
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
    
    def find_tests_for_source_files(self, source_files: List[str]) -> List[dict]:
        """查找源文件对应的测试"""
        if not self.index_data:
            self.load_index()
        
        matched_tests = []
        source_files_normalized = {self._normalize_path(f) for f in source_files}
        
        for test_file in self.index_data.get("test_files", []):
            # 检查直接映射
            test_source_files = {
                self._normalize_path(f) for f in test_file.get("source_files", [])
            }
            
            if source_files_normalized & test_source_files:
                matched_tests.append(test_file)
                continue
            
            # 检查目标模块映射
            target_module = test_file.get("target_module", "")
            if target_module:
                module_path = target_module.replace('.', '/') + '.py'
                if self._normalize_path(module_path) in source_files_normalized:
                    matched_tests.append(test_file)
        
        return matched_tests
    
    def _normalize_path(self, path: str) -> str:
        """标准化路径（处理 Windows/Unix 差异）"""
        return path.replace('\\', '/').lower()
    
    def select_tests(self, source_files: List[str], include_related: bool = True) -> List[str]:
        """选择测试文件路径"""
        matched_tests = self.find_tests_for_source_files(source_files)
        
        test_paths = [test["file_path"] for test in matched_tests]
        
        if include_related:
            # 添加相关测试
            related_tests = set()
            for test in matched_tests:
                related_tests.update(test.get("related_tests", []))
            test_paths.extend(list(related_tests))
        
        # 去重并排序
        return sorted(set(test_paths))
    
    def print_recommendations(self, source_files: List[str], verbose: bool = False):
        """打印测试推荐"""
        matched_tests = self.find_tests_for_source_files(source_files)
        
        if not matched_tests:
            print(f"[WARN] 未找到与以下文件相关的测试:")
            for f in source_files:
                print(f"  - {f}")
            print(f"\n提示: 可能需要运行完整的测试套件")
            return
        
        print(f"[INFO] 找到 {len(matched_tests)} 个相关测试文件:\n")
        
        for test in matched_tests:
            print(f"[OK] {test['file_path']}")
            if verbose:
                print(f"   分类: {test.get('category', 'unknown')}")
                print(f"   目标模块: {test.get('target_module', 'N/A')}")
                print(f"   测试数量: {test.get('test_count', 0)}")
                if test.get('description'):
                    print(f"   说明: {test['description']}")
                print()
        
        # 生成 pytest 命令
        test_paths = [test["file_path"] for test in matched_tests]
        print(f"\n[CMD] 推荐的 pytest 命令:")
        print(f"pytest {' '.join(test_paths)} -v")
        
        # 按分类分组
        by_category = {}
        for test in matched_tests:
            category = test.get('category', 'unknown')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(test['file_path'])
        
        if len(by_category) > 1:
            print(f"\n[STATS] 按分类分组:")
            for category, paths in by_category.items():
                print(f"\n  {category.upper()}:")
                for path in paths:
                    print(f"    - {path}")
    
    def get_pytest_command(self, source_files: List[str]) -> str:
        """生成 pytest 命令"""
        test_paths = self.select_tests(source_files)
        if not test_paths:
            return ""
        return f"pytest {' '.join(test_paths)} -v"


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="根据修改的源文件选择相关测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 选择单个文件相关的测试
  python tests/tools/agent_test_selector.py src/indexer.py

  # 选择多个文件相关的测试
  python tests/tools/agent_test_selector.py src/indexer.py src/query_engine.py

  # 仅输出 pytest 命令（用于脚本）
  python tests/tools/agent_test_selector.py src/indexer.py --command-only

  # 详细输出
  python tests/tools/agent_test_selector.py src/indexer.py -v
        """
    )
    parser.add_argument(
        "source_files",
        nargs="+",
        help="修改的源文件路径（相对于项目根目录）"
    )
    parser.add_argument(
        "-i", "--index",
        type=Path,
        default=Path(__file__).parent.parent / "test_index.json",
        help="测试索引文件路径（默认: tests/test_index.json）"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细信息"
    )
    parser.add_argument(
        "--command-only",
        action="store_true",
        help="仅输出 pytest 命令（用于脚本集成）"
    )
    
    args = parser.parse_args()
    
    selector = TestSelector(args.index)
    
    if args.command_only:
        command = selector.get_pytest_command(args.source_files)
        if command:
            print(command)
        else:
            sys.exit(1)
    else:
        selector.print_recommendations(args.source_files, verbose=args.verbose)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

