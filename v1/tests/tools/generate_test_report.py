"""
生成综合测试报告
整合测试执行结果和覆盖率数据，生成综合报告

改进内容:
- 更清晰的分组和可视化
- 测试质量评分
- 测试执行建议
- Agent 友好的格式
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple


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


def calculate_test_quality_score(
    test_results: Dict[str, Any],
    coverage_data: Dict[str, Any]
) -> Tuple[float, str]:
    """计算测试质量评分 (0-100)"""
    score = 100.0
    reasons = []
    
    if test_results:
        total_stages = len(test_results.get("stages", []))
        failed_stages = sum(
            1 for s in test_results.get("stages", [])
            if s.get("returncode", 0) != 0
        )
        
        if total_stages > 0:
            pass_rate = (total_stages - failed_stages) / total_stages
            score *= pass_rate
            if failed_stages > 0:
                reasons.append(f"有 {failed_stages} 个测试阶段失败")
    
    if coverage_data:
        coverage_percent = coverage_data.get("totals", {}).get("percent_covered", 0)
        if coverage_percent < 90:
            coverage_factor = max(0, coverage_percent / 90)
            score *= coverage_factor
            if coverage_percent < 80:
                reasons.append(f"覆盖率 {coverage_percent:.1f}% 低于目标 90%")
    
    return round(score, 1), "; ".join(reasons) if reasons else "所有指标达标"


def generate_coverage_visualization(coverage_percent: float) -> str:
    """生成覆盖率可视化（文本图表）"""
    bar_length = 30
    filled = int(coverage_percent / 100 * bar_length)
    empty = bar_length - filled
    
    bar = "█" * filled + "░" * empty
    
    if coverage_percent >= 90:
        status = "✅ 优秀"
    elif coverage_percent >= 80:
        status = "⚠️  良好"
    elif coverage_percent >= 60:
        status = "⚠️  一般"
    else:
        status = "❌ 不足"
    
    return f"{bar} {coverage_percent:.1f}% {status}"


def generate_test_recommendations(
    test_results: Dict[str, Any],
    coverage_data: Dict[str, Any]
) -> List[str]:
    """生成测试执行建议"""
    recommendations = []
    
    if test_results:
        failed_stages = [
            s for s in test_results.get("stages", [])
            if s.get("returncode", 0) != 0
        ]
        
        if failed_stages:
            recommendations.append(f"🔴 **高优先级**: 修复 {len(failed_stages)} 个失败的测试阶段")
            recommendations.append("   1. 查看失败测试的详细错误信息")
            recommendations.append("   2. 运行单个失败的测试进行调试")
            recommendations.append("   3. 检查相关代码修改是否引入问题")
            
            # 识别失败最多的阶段
            if failed_stages:
                worst_stage = max(
                    failed_stages,
                    key=lambda s: len(s.get("failed_tests", []))
                )
                recommendations.append(f"   4. 重点关注: {worst_stage.get('stage', 'Unknown')}")
    
    if coverage_data:
        coverage_percent = coverage_data.get("totals", {}).get("percent_covered", 0)
        if coverage_percent < 80:
            recommendations.append(f"🟡 **中优先级**: 提升代码覆盖率至 80% 以上（当前: {coverage_percent:.1f}%）")
            recommendations.append("   1. 识别覆盖率较低的文件（见下方列表）")
            recommendations.append("   2. 为核心功能添加单元测试")
            recommendations.append("   3. 补充边界条件和异常情况的测试")
        elif coverage_percent < 90:
            recommendations.append(f"🟢 **低优先级**: 持续提升代码覆盖率至 90% 以上（当前: {coverage_percent:.1f}%）")
    
    if not recommendations:
        recommendations.append("✅ 测试质量良好，继续保持")
        recommendations.append("   - 新功能开发时同步添加测试")
        recommendations.append("   - 修复 Bug 时添加回归测试")
    
    return recommendations


def group_stages_by_category(stages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """按分类分组测试阶段"""
    categories = {
        "基础设施": [],
        "核心功能": [],
        "集成测试": [],
        "端到端": [],
        "其他": []
    }
    
    category_keywords = {
        "基础设施": ["配置", "数据源", "Embedding", "基础设施"],
        "核心功能": ["索引", "查询", "检索", "路由", "重排序"],
        "集成测试": ["集成", "服务", "流水线"],
        "端到端": ["E2E", "工作流", "端到端"]
    }
    
    for stage in stages:
        stage_name = stage.get("stage", "").lower()
        categorized = False
        
        for category, keywords in category_keywords.items():
            if any(kw in stage_name for kw in keywords):
                categories[category].append(stage)
                categorized = True
                break
        
        if not categorized:
            categories["其他"].append(stage)
    
    return {k: v for k, v in categories.items() if v}


def generate_markdown_report(
    test_results: Dict[str, Any],
    coverage_data: Dict[str, Any],
    output_file: Path
):
    """生成Markdown格式的综合报告（改进版）"""
    lines = [
        "# 📊 模块化RAG项目测试报告",
        "",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
    ]
    
    # 计算质量评分
    quality_score, score_reason = calculate_test_quality_score(test_results, coverage_data)
    
    # 质量评分摘要
    lines.extend([
        "## 🎯 测试质量评分",
        "",
        f"### 总体评分: **{quality_score}/100**",
        "",
    ])
    
    if score_reason:
        lines.append(f"*{score_reason}*")
    else:
        lines.append("*所有测试指标达标*")
    
    lines.append("")
    
    # 评分明细
    lines.append("#### 评分明细:")
    if test_results:
        total_stages = len(test_results.get("stages", []))
        failed_stages = sum(
            1 for s in test_results.get("stages", [])
            if s.get("returncode", 0) != 0
        )
        pass_rate = ((total_stages - failed_stages) / total_stages * 100) if total_stages > 0 else 0
        lines.append(f"- 测试通过率: {pass_rate:.1f}% ({total_stages - failed_stages}/{total_stages})")
    
    if coverage_data:
        coverage_percent = coverage_data.get("totals", {}).get("percent_covered", 0)
        lines.append(f"- 代码覆盖率: {coverage_percent:.1f}%")
    
    lines.extend(["", "---", "", "## 📊 测试执行摘要", ""])
    
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
        
        # 按分类分组显示
        stages = test_results.get("stages", [])
        grouped_stages = group_stages_by_category(stages)
        
        for category, category_stages in grouped_stages.items():
            lines.append(f"### {category} ({len(category_stages)} 个阶段)")
            lines.append("")
            
            for stage in category_stages:
                status = "✅ 通过" if stage.get("returncode", 0) == 0 else "❌ 失败"
                lines.append(f"#### {stage.get('stage', 'Unknown')} {status}")
                
                test_paths = stage.get('test_paths', [])
                if test_paths:
                    if len(test_paths) <= 3:
                        lines.append(f"- **测试路径**: {', '.join(test_paths)}")
                    else:
                        lines.append(f"- **测试路径**: {', '.join(test_paths[:3])} ... (共{len(test_paths)}个)")
                
                tests_run = stage.get('tests_run', 0)
                if tests_run > 0:
                    lines.append(f"- **执行测试数**: {tests_run}")
                
                failed_tests = stage.get('failed_tests', [])
                if failed_tests:
                    lines.append(f"- **失败测试数**: {len(failed_tests)}")
                    lines.append(f"- **失败测试列表**:")
                    for failed_test in failed_tests[:5]:  # 只显示前5个
                        lines.append(f"  - `{failed_test}`")
                    if len(failed_tests) > 5:
                        lines.append(f"  - ... 还有 {len(failed_tests) - 5} 个失败的测试")
                
                if stage.get('error'):
                    lines.append(f"- **错误**: {stage['error']}")
                
                lines.append("")
            
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
            "### 覆盖率概览",
            "",
            generate_coverage_visualization(coverage_percent),
            "",
            f"- **覆盖行数**: {totals.get('covered_lines', 0):,}",
            f"- **总行数**: {totals.get('num_statements', 0):,}",
            f"- **缺失行数**: {totals.get('missing_lines', 0):,}",
            "",
        ])
        
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
    
    # 执行建议
    lines.extend([
        "---",
        "",
        "## 💡 执行建议",
        "",
    ])
    
    recommendations = generate_test_recommendations(test_results, coverage_data)
    for rec in recommendations:
        lines.append(rec)
    
    lines.append("")
    
    # Agent 使用提示
    lines.extend([
        "---",
        "",
        "## 🤖 Agent 使用提示",
        "",
        "Agent 可以使用以下工具进一步分析测试结果:",
        "",
        "- **测试选择**: `python tests/tools/agent_test_selector.py <源文件>` - 根据修改的文件选择相关测试",
        "- **测试信息**: `python tests/tools/agent_test_info.py <测试文件>` - 查看测试详细信息",
        "- **测试摘要**: `python tests/tools/agent_test_summary.py` - 生成测试执行摘要",
        "- **测试索引**: 查看 `tests/AGENTS-TESTING-INDEX.md` 了解测试体系结构",
        "",
    ])
    
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


