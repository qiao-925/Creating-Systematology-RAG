#!/usr/bin/env python3
"""Bug 分析工具 - 从 agent-task-log 中提取 bug 统计信息

核心功能：
- extract_bug_info(): 从日志文件中提取 bug 信息
- analyze_bug_patterns(): 分析 bug 模式和趋势
- generate_report(): 生成自我审视报告

使用方式：
    python scripts/analyze_bugs.py [--month YYYY-MM]
"""

import re
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Optional
import argparse


class BugInfo:
    """Bug 信息数据类"""
    
    def __init__(
        self,
        date: str,
        title: str,
        root_cause: str = "",
        affected_modules: List[str] = None,
        fix_strategy: str = "",
        file_path: str = "",
    ):
        self.date = date
        self.title = title
        self.root_cause = root_cause
        self.affected_modules = affected_modules or []
        self.fix_strategy = fix_strategy
        self.file_path = file_path


def extract_bug_info(log_file: Path) -> Optional[BugInfo]:
    """从日志文件中提取 bug 信息"""
    try:
        content = log_file.read_text(encoding='utf-8')
        
        # 提取日期和标题
        title_match = re.search(r'# (\d{4}-\d{2}-\d{2}) 【bugfix】(.+)', content)
        if not title_match:
            return None
        
        date = title_match.group(1)
        title = title_match.group(2).strip()
        
        # 提取涉及模块
        modules = []
        modules_section = re.search(r'涉及模块[：:]\s*\n(.*?)(?=\n##|\n###|$)', content, re.DOTALL)
        if modules_section:
            module_lines = modules_section.group(1).strip().split('\n')
            for line in module_lines:
                if line.strip().startswith('-'):
                    # 提取模块路径（去掉注释）
                    module = re.sub(r'[（(].*?[)）]', '', line).strip('- `').strip()
                    if module:
                        modules.append(module)
        
        # 提取根本原因
        root_cause = ""
        cause_patterns = [
            r'问题根源[：:]\s*\n(.*?)(?=\n##|\n###)',
            r'根本原因[：:]\s*\n(.*?)(?=\n##|\n###)',
            r'问题分析[：:]\s*\n(.*?)(?=\n##|\n###)',
        ]
        for pattern in cause_patterns:
            cause_match = re.search(pattern, content, re.DOTALL)
            if cause_match:
                root_cause = cause_match.group(1).strip()[:200]  # 限制长度
                break
        
        # 提取修复策略
        fix_strategy = ""
        fix_patterns = [
            r'修复方案[：:]\s*\n(.*?)(?=\n##|\n###)',
            r'解决方案[：:]\s*\n(.*?)(?=\n##|\n###)',
        ]
        for pattern in fix_patterns:
            fix_match = re.search(pattern, content, re.DOTALL)
            if fix_match:
                fix_strategy = fix_match.group(1).strip()[:200]  # 限制长度
                break
        
        return BugInfo(
            date=date,
            title=title,
            root_cause=root_cause,
            affected_modules=modules,
            fix_strategy=fix_strategy,
            file_path=str(log_file),
        )
    
    except Exception as e:
        print(f"⚠️ 解析文件失败 {log_file}: {e}")
        return None


def analyze_bug_patterns(bugs: List[BugInfo]) -> Dict:
    """分析 bug 模式"""
    # 按月份统计
    monthly_count = Counter()
    for bug in bugs:
        month = bug.date[:7]  # YYYY-MM
        monthly_count[month] += 1
    
    # 高频模块
    module_count = Counter()
    for bug in bugs:
        for module in bug.affected_modules:
            # 提取顶层模块
            top_module = module.split('/')[0] if '/' in module else module
            module_count[top_module] += 1
    
    # 根因分类（简单关键词匹配）
    cause_categories = {
        '导入错误': ['导入', 'import', 'NameError', 'ModuleNotFoundError'],
        '类型错误': ['类型', 'TypeError', 'type hint', '类型提示'],
        '配置问题': ['配置', 'config', '路径', 'path'],
        '兼容性': ['兼容', '参数', 'kwargs', '方法签名'],
        'UI问题': ['UI', '界面', '显示', 'streamlit'],
        '逻辑错误': ['逻辑', '标记', '状态', 'session_state'],
    }
    
    cause_count = Counter()
    for bug in bugs:
        cause_text = bug.root_cause.lower()
        for category, keywords in cause_categories.items():
            if any(keyword.lower() in cause_text for keyword in keywords):
                cause_count[category] += 1
                break
        else:
            cause_count['其他'] += 1
    
    return {
        'monthly_count': dict(sorted(monthly_count.items())),
        'module_count': dict(module_count.most_common(10)),
        'cause_count': dict(cause_count.most_common()),
        'total_bugs': len(bugs),
    }


def generate_report(bugs: List[BugInfo], analysis: Dict, output_path: Optional[Path] = None) -> str:
    """生成自我审视报告"""
    report_lines = [
        "# Bug 自我审视报告",
        "",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**分析范围**: 全部 agent-task-log",
        "",
        "---",
        "",
        "## 1. 总体统计",
        "",
        f"- **Bug 总数**: {analysis['total_bugs']} 个",
        f"- **时间跨度**: {min(analysis['monthly_count'].keys())} ~ {max(analysis['monthly_count'].keys())}",
        "",
        "## 2. 时间趋势",
        "",
        "### 按月分布",
        "",
    ]
    
    # 月度统计
    for month, count in analysis['monthly_count'].items():
        bar = '█' * count
        report_lines.append(f"- **{month}**: {count:2d} 个  {bar}")
    
    report_lines.extend([
        "",
        "## 3. 高频问题模块",
        "",
    ])
    
    # 模块统计
    for module, count in analysis['module_count'].items():
        report_lines.append(f"- `{module}`: {count} 次")
    
    report_lines.extend([
        "",
        "## 4. Bug 根因分类",
        "",
    ])
    
    # 根因统计
    for cause, count in analysis['cause_count'].items():
        percentage = (count / analysis['total_bugs']) * 100
        report_lines.append(f"- **{cause}**: {count} 个 ({percentage:.1f}%)")
    
    report_lines.extend([
        "",
        "## 5. 自我审视",
        "",
        "### 🔍 发现的模式",
        "",
    ])
    
    # 生成洞察
    top_cause = max(analysis['cause_count'].items(), key=lambda x: x[1])
    top_module = max(analysis['module_count'].items(), key=lambda x: x[1])
    
    report_lines.extend([
        f"1. **最高频问题类型**: {top_cause[0]} ({top_cause[1]} 次)",
        f"   - 说明这类问题容易重复出现，需要系统性预防",
        "",
        f"2. **最高频问题模块**: `{top_module[0]}` ({top_module[1]} 次)",
        f"   - 该模块可能设计复杂度较高，或者变更频繁",
        "",
        "3. **月度趋势观察**:",
    ])
    
    # 趋势分析
    monthly_values = list(analysis['monthly_count'].values())
    if len(monthly_values) >= 2:
        recent_avg = sum(monthly_values[-3:]) / min(3, len(monthly_values))
        early_avg = sum(monthly_values[:3]) / min(3, len(monthly_values))
        if recent_avg > early_avg:
            report_lines.append(f"   - Bug 数量呈上升趋势（早期平均 {early_avg:.1f} vs 近期平均 {recent_avg:.1f}）")
        else:
            report_lines.append(f"   - Bug 数量相对稳定或下降（早期平均 {early_avg:.1f} vs 近期平均 {recent_avg:.1f}）")
    
    report_lines.extend([
        "",
        "### 💡 改进建议",
        "",
        f"1. **针对高频问题**（{top_cause[0]}）:",
        "   - 考虑在规则或检查清单中增加针对性预防措施",
        "   - 创建专门的测试用例覆盖此类场景",
        "",
        f"2. **针对高频模块**（`{top_module[0]}`）:",
        "   - 考虑重构以降低复杂度",
        "   - 增加单元测试覆盖率",
        "   - 在修改前增加 code review 流程",
        "",
        "3. **预防性措施**:",
        "   - 定期运行 linter 和 type checker",
        "   - 建立 bug 修复前的根因分析习惯",
        "   - 记录常见陷阱到 aha-moments",
        "",
        "---",
        "",
        "**注**: 这是基于历史数据的自动分析，具体决策需结合实际情况。",
    ])
    
    report = "\n".join(report_lines)
    
    # 保存到文件
    if output_path:
        output_path.write_text(report, encoding='utf-8')
        print(f"✅ 报告已保存到: {output_path}")
    
    return report


def main():
    parser = argparse.ArgumentParser(description='分析 bug 日志')
    parser.add_argument('--month', help='只分析指定月份 (格式: YYYY-MM)')
    parser.add_argument('--output', help='输出文件路径')
    args = parser.parse_args()
    
    # 查找所有 bugfix 日志
    archive_dir = Path('agent-task-log/archive')
    if not archive_dir.exists():
        print(f"❌ 找不到目录: {archive_dir}")
        return
    
    print("🔍 扫描 bugfix 日志...")
    bug_files = list(archive_dir.rglob('*bugfix*.md'))
    
    # 过滤月份
    if args.month:
        bug_files = [f for f in bug_files if args.month in str(f)]
    
    print(f"📊 找到 {len(bug_files)} 个 bugfix 日志")
    
    # 提取信息
    bugs = []
    for file in bug_files:
        bug_info = extract_bug_info(file)
        if bug_info:
            bugs.append(bug_info)
    
    print(f"✅ 成功解析 {len(bugs)} 个 bug 记录")
    
    # 分析
    analysis = analyze_bug_patterns(bugs)
    
    # 生成报告
    output_path = Path(args.output) if args.output else None
    if not output_path:
        output_path = Path('agent-task-log') / f'bug_analysis_{datetime.now().strftime("%Y-%m-%d")}.md'
    
    report = generate_report(bugs, analysis, output_path)
    
    print("\n" + "="*60)
    print(report)


if __name__ == '__main__':
    main()
