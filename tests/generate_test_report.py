"""
生成综合测试报告
整合测试执行结果和覆盖率数据，生成综合报告
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def load_test_results(reports_dir: Path) -> Dict[str, Any]:
    """加载测试执行结果"""
    json_files = list(reports_dir.glob("test_report_*.json"))
    
    if not json_files:
        return {}
    
    # 读取最新的报告
    latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest_json, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_coverage_data(reports_dir: Path) -> Dict[str, Any]:
    """加载覆盖率数据"""
    coverage_dir = reports_dir / "coverage"
    json_files = list(coverage_dir.glob("coverage_*.json"))
    
    if not json_files:
        return {}
    
    # 读取最新的覆盖率报告
    latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest_json, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_markdown_report(
    test_results: Dict[str, Any],
    coverage_data: Dict[str, Any],
    output_file: Path
):
    """生成Markdown格式的综合报告"""
    lines = [
        "# 模块化RAG项目测试报告",
        "",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## 📊 测试执行摘要",
        "",
    ]
    
    # 测试结果摘要
    if test_results:
        total_stages = len(test_results.get("stages", []))
        failed_stages = sum(
            1 for s in test_results.get("stages", [])
            if s.get("returncode", 0) != 0
        )
        
        lines.extend([
            f"- **总测试阶段**: {total_stages}",
            f"- **通过阶段**: {total_stages - failed_stages}",
            f"- **失败阶段**: {failed_stages}",
            "",
            "### 各阶段详情",
            "",
        ])
        
        for stage in test_results.get("stages", []):
            status = "✅ 通过" if stage.get("returncode", 0) == 0 else "❌ 失败"
            lines.append(f"#### {stage.get('stage', 'Unknown')} {status}")
            lines.append(f"- 测试路径: {', '.join(stage.get('test_paths', []))}")
            lines.append(f"- 执行测试数: {stage.get('tests_run', 0)}")
            
            if stage.get('failed_tests'):
                lines.append(f"- 失败测试: {len(stage['failed_tests'])}")
                for failed_test in stage['failed_tests'][:5]:  # 只显示前5个
                    lines.append(f"  - {failed_test}")
            if stage.get('error'):
                lines.append(f"- 错误: {stage['error']}")
            
            lines.append("")
    
    # 覆盖率摘要
    lines.extend([
        "---",
        "",
        "## 📈 代码覆盖率",
        "",
    ])
    
    if coverage_data:
        totals = coverage_data.get("totals", {})
        coverage_percent = totals.get("percent_covered", 0)
        
        lines.extend([
            f"- **总体覆盖率**: {coverage_percent:.2f}%",
            f"- **覆盖行数**: {totals.get('covered_lines', 0)}",
            f"- **总行数**: {totals.get('num_statements', 0)}",
            f"- **缺失行数**: {totals.get('missing_lines', 0)}",
            "",
        ])
        
        # 覆盖率评估
        if coverage_percent >= 80:
            lines.append("✅ **覆盖率达标** (≥80%)")
        elif coverage_percent >= 60:
            lines.append("⚠️ **覆盖率一般** (60-80%)")
        else:
            lines.append("❌ **覆盖率不足** (<60%)")
        
        lines.append("")
        
        # 文件覆盖率详情
        files = coverage_data.get("files", {})
        if files:
            lines.extend([
                "### 文件覆盖率详情",
                "",
                "#### 覆盖率较低的文件 (前10个):",
                "",
                "| 文件路径 | 覆盖率 | 覆盖行数 | 总行数 |",
                "|---------|--------|----------|--------|",
            ])
            
            sorted_files = sorted(
                files.items(),
                key=lambda x: x[1].get("summary", {}).get("percent_covered", 0)
            )[:10]
            
            for filepath, file_data in sorted_files:
                summary = file_data.get("summary", {})
                coverage = summary.get("percent_covered", 0)
                covered_lines = summary.get("covered_lines", 0)
                num_statements = summary.get("num_statements", 0)
                lines.append(
                    f"| {filepath} | {coverage:.2f}% | {covered_lines} | {num_statements} |"
                )
    else:
        lines.append("⚠️ 未找到覆盖率数据")
    
    # 结论和建议
    lines.extend([
        "---",
        "",
        "## 📝 结论和建议",
        "",
    ])
    
    if test_results and coverage_data:
        failed_stages = sum(
            1 for s in test_results.get("stages", [])
            if s.get("returncode", 0) != 0
        )
        coverage_percent = coverage_data.get("totals", {}).get("percent_covered", 0)
        
        if failed_stages == 0 and coverage_percent >= 80:
            lines.append("✅ **测试通过，覆盖率达标**")
            lines.append("")
            lines.append("项目测试质量良好，可以继续开发。")
        else:
            lines.append("⚠️ **需要改进**")
            lines.append("")
            
            if failed_stages > 0:
                lines.append(f"- 有 {failed_stages} 个测试阶段失败，需要修复")
            
            if coverage_percent < 80:
                lines.append(f"- 代码覆盖率 {coverage_percent:.2f}% 低于目标 80%，需要补充测试")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*报告由测试自动化工具生成*")
    
    # 写入文件
    report_text = "\n".join(lines)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"\n综合测试报告已生成: {output_file}")
    return report_text


def main():
    """主函数"""
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = reports_dir / f"test_report_{timestamp}.md"
    
    # 加载数据
    print("加载测试结果...")
    test_results = load_test_results(reports_dir)
    
    print("加载覆盖率数据...")
    coverage_data = load_coverage_data(reports_dir)
    
    # 生成报告
    print("生成综合报告...")
    generate_markdown_report(test_results, coverage_data, output_file)
    
    print("\n✅ 报告生成完成")


if __name__ == "__main__":
    main()


