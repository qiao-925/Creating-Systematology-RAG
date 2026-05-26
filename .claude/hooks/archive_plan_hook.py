#!/usr/bin/env python3
r"""Plan 文档存档 hook

在 plan 文档 Write 时自动存档。存档文件与 plan 同域目录，
格式为 Markdown + frontmatter，记录任务状态、约束、决策快照。

触发条件：PostToolUse on Write，文件名匹配 (plan|计划).*\.md$
排除：checklist、template、archive 文件本身
"""
import json
import os
import re
import sys
from datetime import datetime


def is_plan_file(file_path: str) -> bool:
    """判断是否为 plan 文档（排除 checklist/template/archive）。

    匹配规则：
    1. 文件名含 plan/计划 的 .md 文件（项目内手动命名的计划文档）
    2. .claude/plans/ 目录下的任何 .md 文件（Claude Code plan mode 自动生成）
    """
    lower = file_path.lower().replace("\\", "/")

    # Claude Code plan mode 生成的文件
    if "/.claude/plans/" in lower and lower.endswith(".md"):
        return True

    # 项目内手动命名的 plan 文档
    if not re.search(r"(plan|计划).*\.md$", file_path, re.IGNORECASE):
        return False
    if any(skip in lower for skip in ("checklist", "template", "archive")):
        return False
    return True


def extract_sections(content: str) -> dict[str, str]:
    """按 H2 分节，返回 {标题: 正文}。"""
    lines = content.split("\n")
    sections: dict[str, str] = {}
    heading = ""
    buf: list[str] = []
    in_code = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            buf.append(line)
            continue
        if in_code:
            buf.append(line)
            continue
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            if heading:
                sections[heading] = "\n".join(buf)
            heading = m.group(1).strip()
            buf = []
        else:
            buf.append(line)

    if heading:
        sections[heading] = "\n".join(buf)
    return sections


def extract_tasks(section_text: str) -> list[dict]:
    """从任务清单节提取任务条目及其状态。"""
    tasks = []
    pattern = re.compile(
        r"^-\s*\[([ xX])\]\s*(T\d+(?:\.\d+)?)\s+(.+)$",
        re.MULTILINE,
    )
    for m in pattern.finditer(section_text):
        done = m.group(1).lower() == "x"
        task_id = m.group(2)
        name = m.group(3).strip()
        tasks.append({"id": task_id, "name": name, "done": done})
    return tasks


def extract_decisions(section_text: str) -> list[dict]:
    """从决策清单节提取决策条目。"""
    decisions = []
    pattern = re.compile(
        r"^-\s*\[([ xX])\]\s*(D\d+)\s+(.+)$",
        re.MULTILINE,
    )
    for m in pattern.finditer(section_text):
        done = m.group(1).lower() == "x"
        dec_id = m.group(2)
        desc = m.group(3).strip()
        decisions.append({"id": dec_id, "description": desc, "resolved": done})
    return decisions


def find_section_text(sections: dict, keywords: list[str]) -> str:
    """在 sections 中查找匹配关键词的节。"""
    for heading, body in sections.items():
        for kw in keywords:
            if kw in heading:
                return body.strip()
    return ""


def extract_hard_constraints(sections: dict) -> list[str]:
    """从执行规则节提取硬性约束。"""
    rules_text = find_section_text(sections, ["执行规则", "Execution Rules"])
    if not rules_text:
        return []
    # 找硬性约束子节
    m = re.search(
        r"#{2,4}\s*(?:硬性约束|Hard).*?\n(.*?)(?=\n#{2,4}|\Z)",
        rules_text,
        re.DOTALL,
    )
    if not m:
        return []
    block = m.group(1).strip()
    constraints = []
    for line in block.split("\n"):
        line = line.strip()
        if re.match(r"^[\d]+[\.\)、]\s*\*\*.*?\*\*", line):
            # 提取编号和标题
            cm = re.match(r"^[\d]+[\.\)、]\s*\*\*(.+?)\*\*", line)
            if cm:
                constraints.append(cm.group(1))
    return constraints


def get_archive_path(plan_path: str) -> str:
    """根据 plan 路径生成存档路径。

    - 项目内 plan 文档：存档放在 plan 同域的 .archive/ 子目录下
    - Claude Code plan mode 文件（.claude/plans/）：存档放到项目 docs/.archive/
    """
    normalized = plan_path.replace("\\", "/")

    # Claude Code plan mode 生成的文件 → 项目 docs/.archive/
    if "/.claude/plans/" in normalized:
        # 向上查找项目根（含 CLAUDE.md 或 .git 的目录）
        project_root = os.getcwd()
        archive_dir = os.path.join(project_root, "docs", ".archive")
        plan_name = os.path.splitext(os.path.basename(plan_path))[0]
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        archive_name = f"{plan_name}-{timestamp}.archive.md"
        return os.path.join(archive_dir, archive_name)

    # 项目内 plan 文档 → 同域 .archive/
    plan_dir = os.path.dirname(plan_path)
    plan_name = os.path.splitext(os.path.basename(plan_path))[0]
    archive_dir = os.path.join(plan_dir, ".archive")
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    archive_name = f"{plan_name}-{timestamp}.archive.md"
    return os.path.join(archive_dir, archive_name)


def generate_archive(content: str, plan_path: str) -> str:
    """生成存档内容（Markdown + frontmatter）。"""
    sections = extract_sections(content)
    task_section = find_section_text(sections, ["任务清单", "Task", "任务"])
    decision_section = find_section_text(sections, ["决策清单", "Decision", "决策"])
    tasks = extract_tasks(task_section)
    decisions = extract_decisions(decision_section)
    constraints = extract_hard_constraints(sections)

    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    dec_done = sum(1 for d in decisions if d["resolved"])
    dec_total = len(decisions)

    # 确定当前阶段：找到最后一个未完成任务所在阶段
    current_phase = ""
    phase_pattern = re.compile(r"#{2,4}\s*(.+?(?:阶段|Phase|Stage).*?)$", re.MULTILINE)
    phase_matches = list(phase_pattern.finditer(content))
    if phase_matches:
        # 找最后一个已完成任务的位置，反推当前阶段
        last_done_pos = -1
        for m in re.finditer(r"^-\s*\[x\]", content, re.MULTILINE | re.IGNORECASE):
            last_done_pos = m.start()
        for pm in reversed(phase_matches):
            if pm.start() <= last_done_pos:
                current_phase = pm.group(1).strip()
                break
        if not current_phase and phase_matches:
            current_phase = phase_matches[0].group(1).strip()

    # 提取版本目标
    goal_text = find_section_text(sections, ["版本目标", "Version Goal", "Goal"])
    goal_first_line = ""
    if goal_text:
        for line in goal_text.split("\n"):
            line = line.strip().lstrip("- ")
            if line:
                goal_first_line = line
                break

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 构建 frontmatter
    fm_lines = [
        "---",
        f"plan_name: \"{os.path.splitext(os.path.basename(plan_path))[0]}\"",
        f"source: \"{plan_path}\"",
        f"archive_date: \"{now}\"",
        f"current_phase: \"{current_phase}\"",
        f"tasks_done: {done_count}",
        f"tasks_total: {total_count}",
        f"decisions_resolved: {dec_done}",
        f"decisions_total: {dec_total}",
        f"constraints_count: {len(constraints)}",
        "---",
    ]

    # 构建正文
    body_lines = [
        "",
        f"# 存档：{os.path.basename(plan_path)}",
        "",
        f"> 自动生成于 {now}，源文件：`{plan_path}`",
        "",
        "## 任务状态",
        "",
    ]

    # 任务按完成/未完成分组
    if tasks:
        done_tasks = [t for t in tasks if t["done"]]
        pending_tasks = [t for t in tasks if not t["done"]]
        if done_tasks:
            body_lines.append(f"### 已完成 ({len(done_tasks)}/{len(tasks)})")
            for t in done_tasks:
                body_lines.append(f"- [x] {t['id']} {t['name']}")
            body_lines.append("")
        if pending_tasks:
            body_lines.append(f"### 待完成 ({len(pending_tasks)}/{len(tasks)})")
            for t in pending_tasks:
                body_lines.append(f"- [ ] {t['id']} {t['name']}")
            body_lines.append("")
    else:
        body_lines.append("_无任务条目_")
        body_lines.append("")

    # 决策快照
    body_lines.extend([
        "## 决策快照",
        "",
    ])
    if decisions:
        for d in decisions:
            mark = "x" if d["resolved"] else " "
            body_lines.append(f"- [{mark}] {d['id']} {d['description']}")
        body_lines.append("")
    else:
        body_lines.append("_无决策条目_")
        body_lines.append("")

    # 硬性约束快照
    body_lines.extend([
        "## 硬性约束快照",
        "",
    ])
    if constraints:
        for i, c in enumerate(constraints, 1):
            body_lines.append(f"{i}. {c}")
        body_lines.append("")
    else:
        body_lines.append("_无硬性约束_")
        body_lines.append("")

    return "\n".join(fm_lines) + "\n" + "\n".join(body_lines)


def main():
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name != "Write":
        sys.exit(0)

    file_path = data.get("tool_input", {}).get("file_path", "")
    if not is_plan_file(file_path):
        sys.exit(0)

    content = data.get("tool_input", {}).get("content", "")
    if not content:
        sys.exit(0)

    archive_path = get_archive_path(file_path)
    archive_content = generate_archive(content, file_path)

    # 确保 .archive 目录存在
    archive_dir = os.path.dirname(archive_path)
    os.makedirs(archive_dir, exist_ok=True)

    # 写入存档
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(archive_content)

    print(json.dumps({
        "hookSpecificOutput": {
            "permissionDecision": "allow",
            "reason": f"Plan 存档已生成：{archive_path}"
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
