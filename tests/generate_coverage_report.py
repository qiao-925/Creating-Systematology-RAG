"""
生成测试覆盖率报告
运行覆盖率测试并生成HTML和文本报告
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_coverage_tests():
    """运行覆盖率测试"""
    print("=" * 60)
    print("运行测试覆盖率分析")
    print("=" * 60)
    
    # 覆盖率报告目录
    reports_dir = Path(__file__).parent / "reports" / "coverage"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 运行覆盖率测试
    cmd = [
        "python", "-m", "pytest",
        "--cov=backend",
        "--cov=frontend",
        "--cov-report=html:" + str(reports_dir / "html"),
        "--cov-report=xml:" + str(reports_dir / f"coverage_{timestamp}.xml"),
        "--cov-report=term-missing",
        "--cov-report=json:" + str(reports_dir / f"coverage_{timestamp}.json"),
        "-v",
    ]
    
    # 添加所有测试路径（排除性能测试，因为可能耗时较长）
    test_dirs = [
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        "tests/ui",
        "tests/compatibility",
        "tests/regression",
    ]
    
    cmd.extend(test_dirs)
    
    print(f"\n执行命令: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(
            cmd,
            timeout=7200,  # 2小时超时
        )
        
        if result.returncode == 0:
            print("\n✅ 覆盖率测试完成")
            print(f"\nHTML报告: {reports_dir / 'html' / 'index.html'}")
            print(f"JSON报告: {reports_dir / f'coverage_{timestamp}.json'}")
            print(f"XML报告: {reports_dir / f'coverage_{timestamp}.xml'}")
        else:
            print(f"\n⚠️ 覆盖率测试返回码: {result.returncode}")
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("\n❌ 覆盖率测试超时")
        return 1
    except Exception as e:
        print(f"\n❌ 覆盖率测试出错: {e}")
        return 1


def generate_summary_report():
    """生成覆盖率摘要报告"""
    reports_dir = Path(__file__).parent / "reports" / "coverage"
    json_files = list(reports_dir.glob("coverage_*.json"))
    
    if not json_files:
        print("未找到覆盖率JSON报告")
        return
    
    # 读取最新的JSON报告
    latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
    
    try:
        import json
        with open(latest_json, 'r', encoding='utf-8') as f:
            coverage_data = json.load(f)
        
        print("\n" + "=" * 60)
        print("覆盖率摘要")
        print("=" * 60)
        
        totals = coverage_data.get("totals", {})
        print(f"\n总体覆盖率: {totals.get('percent_covered', 0):.2f}%")
        print(f"覆盖行数: {totals.get('covered_lines', 0)}")
        print(f"总行数: {totals.get('num_statements', 0)}")
        print(f"缺失行数: {totals.get('missing_lines', 0)}")
        
        # 按文件显示覆盖率
        files = coverage_data.get("files", {})
        if files:
            print("\n文件覆盖率（前10个最低）:")
            sorted_files = sorted(
                files.items(),
                key=lambda x: x[1].get("summary", {}).get("percent_covered", 0)
            )[:10]
            
            for filepath, file_data in sorted_files:
                summary = file_data.get("summary", {})
                coverage = summary.get("percent_covered", 0)
                print(f"  {filepath}: {coverage:.2f}%")
        
    except Exception as e:
        print(f"生成摘要报告失败: {e}")


def main():
    """主函数"""
    # 检查是否安装了coverage
    try:
        import coverage
    except ImportError:
        print("错误: 未安装coverage包")
        print("请运行: pip install pytest-cov")
        return 1
    
    # 运行覆盖率测试
    returncode = run_coverage_tests()
    
    # 生成摘要报告
    if returncode == 0:
        generate_summary_report()
    
    return returncode


if __name__ == "__main__":
    sys.exit(main())


