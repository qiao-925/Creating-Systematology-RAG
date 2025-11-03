"""
Agent 测试摘要生成工具

生成简明的测试执行摘要报告，便于 Agent 快速理解测试结果。
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class TestSummaryGenerator:
    """测试摘要生成器"""
    
    def __init__(self, index_file: Path):
        """初始化"""
        self.index_file = index_file
        self.index_data: Optional[dict] = None
    
    def load_index(self):
        """加载测试索引"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self.index_data = json.load(f)
    
    def parse_pytest_output(self, output: str) -> Dict:
        """解析 pytest 输出"""
        result = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0,
            "failed_tests": [],
            "duration": 0.0
        }
        
        lines = output.split('\n')
        for line in lines:
            # 解析统计信息
            if "passed" in line.lower() and "failed" in line.lower():
                # 尝试提取数字
                import re
                numbers = re.findall(r'\d+', line)
                if len(numbers) >= 2:
                    result["passed"] = int(numbers[0]) if len(numbers) > 0 else 0
                    result["failed"] = int(numbers[1]) if len(numbers) > 1 else 0
                    if len(numbers) >= 3:
                        result["skipped"] = int(numbers[2]) if len(numbers) > 2 else 0
                result["total"] = result["passed"] + result["failed"] + result["skipped"]
            
            # 解析失败的测试
            if "FAILED" in line:
                # 提取测试路径
                parts = line.split()
                for part in parts:
                    if "test_" in part and "::" in part:
                        result["failed_tests"].append(part)
            
            # 解析耗时
            if "seconds" in line:
                import re
                duration_match = re.search(r'(\d+\.?\d*)\s+seconds', line)
                if duration_match:
                    result["duration"] = float(duration_match.group(1))
        
        return result
    
    def generate_summary(
        self,
        pytest_output: Optional[str] = None,
        test_files: Optional[List[str]] = None,
        verbose: bool = False
    ) -> str:
        """生成测试摘要"""
        summary_lines = []
        
        summary_lines.append("=" * 60)
        summary_lines.append("测试执行摘要")
        summary_lines.append("=" * 60)
        summary_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append("")
        
        # 如果有 pytest 输出，解析它
        if pytest_output:
            result = self.parse_pytest_output(pytest_output)
            
            summary_lines.append("[STATS] 执行统计:")
            summary_lines.append(f"  总测试数: {result['total']}")
            summary_lines.append(f"  通过: [OK] {result['passed']}")
            summary_lines.append(f"  失败: [FAIL] {result['failed']}")
            summary_lines.append(f"  跳过: [SKIP] {result['skipped']}")
            summary_lines.append(f"  耗时: {result['duration']:.2f} 秒")
            summary_lines.append("")
            
            if result['failed'] > 0:
                summary_lines.append("[FAIL] 失败的测试:")
                for failed_test in result['failed_tests'][:10]:  # 只显示前10个
                    summary_lines.append(f"  - {failed_test}")
                if len(result['failed_tests']) > 10:
                    summary_lines.append(f"  ... 还有 {len(result['failed_tests']) - 10} 个失败的测试")
                summary_lines.append("")
        
        # 如果指定了测试文件，显示文件信息
        if test_files and self.index_data:
            summary_lines.append("[FILES] 执行的测试文件:")
            for test_file in test_files:
                # 查找测试文件信息
                test_info = None
                for t in self.index_data.get("test_files", []):
                    if test_file in t.get("file_path", "") or t.get("file_path", "") in test_file:
                        test_info = t
                        break
                
                if test_info:
                    summary_lines.append(f"  - {test_info['file_path']}")
                    if verbose:
                        summary_lines.append(f"    分类: {test_info.get('category', 'unknown')}")
                        summary_lines.append(f"    测试数: {test_info.get('test_count', 0)}")
                else:
                    summary_lines.append(f"  - {test_file}")
            summary_lines.append("")
        
        # 生成建议
        summary_lines.append("[TIP] 建议:")
        if pytest_output:
            result = self.parse_pytest_output(pytest_output)
            if result['failed'] == 0:
                summary_lines.append("  [OK] 所有测试通过，可以继续开发")
            else:
                summary_lines.append(f"  [WARN] 有 {result['failed']} 个测试失败，需要修复")
                summary_lines.append("  [TIP] 建议:")
                summary_lines.append("     1. 查看失败的测试详情")
                summary_lines.append("     2. 运行单个失败的测试进行调试")
                summary_lines.append("     3. 检查相关代码修改")
        else:
            summary_lines.append("  [INFO] 运行测试后查看详细摘要")
        
        return "\n".join(summary_lines)
    
    def run_tests_and_summarize(
        self,
        test_files: List[str],
        verbose: bool = False
    ) -> str:
        """运行测试并生成摘要"""
        print(f"运行测试: {' '.join(test_files)}")
        
        try:
            result = subprocess.run(
                ["pytest"] + test_files + ["-v"],
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            output = result.stdout + result.stderr
            
            summary = self.generate_summary(
                pytest_output=output,
                test_files=test_files,
                verbose=verbose
            )
            
            return summary
            
        except subprocess.TimeoutExpired:
            return "[ERROR] 测试执行超时（超过1小时）"
        except Exception as e:
            return f"[ERROR] 测试执行出错: {e}"


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="生成测试执行摘要报告",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从 pytest 输出生成摘要
  pytest tests/unit/test_indexer.py -v | python tests/tools/agent_test_summary.py

  # 指定测试文件生成摘要
  python tests/tools/agent_test_summary.py tests/unit/test_indexer.py

  # 运行测试并生成摘要
  python tests/tools/agent_test_summary.py tests/unit/test_indexer.py --run

  # 详细输出
  python tests/tools/agent_test_summary.py tests/unit/test_indexer.py -v
        """
    )
    parser.add_argument(
        "test_files",
        nargs="*",
        help="测试文件路径（如果提供，将显示文件信息）"
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
        "--run",
        action="store_true",
        help="运行测试并生成摘要"
    )
    
    args = parser.parse_args()
    
    generator = TestSummaryGenerator(args.index)
    
    if args.run and args.test_files:
        summary = generator.run_tests_and_summarize(args.test_files, verbose=args.verbose)
        print(summary)
    elif args.test_files:
        summary = generator.generate_summary(
            test_files=args.test_files,
            verbose=args.verbose
        )
        print(summary)
    else:
        # 从标准输入读取 pytest 输出
        pytest_output = sys.stdin.read()
        if pytest_output:
            summary = generator.generate_summary(pytest_output=pytest_output, verbose=args.verbose)
            print(summary)
        else:
            parser.print_help()
            sys.exit(1)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

