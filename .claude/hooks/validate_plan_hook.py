#!/usr/bin/env python3
"""Plan 文档校验 hook

检查 plan 文档是否符合版本开发计划规范（docs/plan-checklist.md）：
1. 版本目标 — 必须包含"做什么"和"为什么"
2. 文档锚定 — 必须包含锚定或同步条目
3. 决策清单 — 必须分核心/支撑两层
4. 任务清单 — 必须分阶段，且包含验收标准和失败路径
5. 执行规则 — 必须包含硬性约束和 checkpoint/自主推进机制
6. 执行记录 — 必须包含清单项
7. 执行 prompt 模板 — 必须包含可执行的 prompt 模板内容
"""
import json
import re
import sys


# ── 检查项定义 ──────────────────────────────────────────────

def check_goal(section_text: str) -> str | None:
    """版本目标：必须包含"做什么"和"为什么"。"""
    has_do = bool(re.search(r"(做什么|What|Goal)", section_text, re.IGNORECASE))
    has_why = bool(re.search(r"(为什么|Why|Motivation)", section_text, re.IGNORECASE))
    if not has_do:
        return '版本目标缺少"做什么"'
    if not has_why:
        return '版本目标缺少"为什么"'
    return None


def check_anchor(section_text: str) -> str | None:
    """文档锚定：必须包含锚定或同步条目（排除标题行本身）。"""
    # 跳过第一行（标题），只检查正文
    body = "\n".join(section_text.split("\n")[1:])
    has_anchor = bool(re.search(r"(锚定|Anchor)", body))
    has_sync = bool(re.search(r"(同步|Sync)", body))
    if not has_anchor and not has_sync:
        return '文档锚定缺少锚定或同步条目'
    return None


def check_decision(section_text: str) -> str | None:
    """决策清单：必须分核心/支撑两层。"""
    has_core = bool(re.search(r"#{2,4}\s*(?:核心|Core)", section_text))
    has_support = bool(re.search(r"#{2,4}\s*(?:支撑|Support)", section_text))
    has_item = bool(re.search(r"-\s*\[[ x]\]", section_text))
    if not has_core:
        return '决策清单缺少"核心决策"分层'
    if not has_support:
        return '决策清单缺少"支撑决策"分层'
    if not has_item:
        return "决策清单没有决策条目"
    return None


def check_task(section_text: str) -> str | None:
    """任务清单：必须分阶段，且包含验收标准和失败路径。"""
    has_phase = bool(re.search(r"#{2,4}\s*(?:阶段|Phase|Stage)", section_text))
    has_acceptance = bool(re.search(r"(验收|Acceptance|Done)", section_text)
                         )
    has_fallback = bool(re.search(r"(失败路径|Fallback|降级|重试|升级|跳过)", section_text)
                        )
    has_item = bool(re.search(r"-\s*\[[ x]\]", section_text))
    if not has_phase:
        return '任务清单缺少"阶段"分层'
    if not has_acceptance:
        return "任务清单缺少验收标准"
    if not has_fallback:
        return "任务清单缺少失败路径"
    if not has_item:
        return "任务清单没有任务条目"
    return None


def check_log(section_text: str) -> str | None:
    """执行记录：必须包含清单项。"""
    has_item = bool(re.search(r"-\s*\[[ x]\]", section_text))
    if not has_item:
        return "执行记录没有清单项"
    return None


def check_execution_rules(section_text: str) -> str | None:
    """执行规则：必须包含硬性约束子节和 checkpoint/自主推进关键词。"""
    has_hard = bool(re.search(r"#{2,4}\s*(?:硬性约束|Hard\s*(?:Constraint|Rule))", section_text))
    has_checkpoint = bool(re.search(
        r"(自检|验收|逐任务|暂停|确认|checkpoint|self.?check|deliverable|自主|自动继续|auto.?continue)",
        section_text, re.IGNORECASE
    ))
    if not has_hard:
        return '执行规则缺少"硬性约束"子节'
    if not has_checkpoint:
        return "执行规则缺少 checkpoint 机制（自检/验收/确认/自主推进）"
    return None


def check_execution_prompt(section_text: str) -> str | None:
    """执行 prompt 模板：必须包含模板内容（代码块或列表）。"""
    has_template = bool(re.search(r"(prompt|模板|template)", section_text, re.IGNORECASE))
    has_content = bool(re.search(r"(```|-\s*\S)", section_text))
    if not has_template:
        return '缺少"执行 prompt 模板"标识'
    if not has_content:
        return "执行 prompt 模板内容为空"
    return None


# ── 校验规则表 ──────────────────────────────────────────────

CHECKS = [
    # (显示名, 可能的标题关键词, 检查函数)
    ("版本目标", ["版本目标", "Version Goal", "Goal", "Objective"], check_goal),
    ("文档锚定", ["文档锚定", "Doc Anchor", "Anchor", "锚定"], check_anchor),
    ("决策清单", ["决策清单", "Decision", "决策"], check_decision),
    ("任务清单", ["任务清单", "Task", "任务"], check_task),
    ("执行规则", ["执行规则", "Execution Rules", "执行约束"], check_execution_rules),
    ("执行记录", ["执行记录", "Execution", "Checkpoint", "Log", "记录"], check_log),
    ("执行 prompt 模板", ["执行 prompt 模板", "Execution Prompt", "Prompt Template", "执行 Prompt 模板"], check_execution_prompt),
]


# ── Markdown 分节解析 ───────────────────────────────────────

def extract_sections(content: str) -> dict[str, str]:
    """将 markdown 按 H2 分节，返回 {标题文本: 正文} 的映射。

    H2 作为主节分割点，H3/H4 内容归入所属 H2 节。
    代码块（```）内的内容跳过，不参与分节。
    """
    lines = content.split("\n")
    sections: dict[str, str] = {}
    current_heading = ""
    current_lines: list[str] = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            current_lines.append(line)
            continue
        if in_code_block:
            current_lines.append(line)
            continue

        # 只用 H2 作为分节边界
        heading_match = re.match(r"^##\s+(.+)$", line)
        if heading_match:
            if current_heading:
                sections[current_heading] = "\n".join(current_lines)
            current_heading = heading_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_heading:
        sections[current_heading] = "\n".join(current_lines)

    return sections


def find_section(content: str, keywords: list[str]) -> str | None:
    """在内容中查找匹配关键词的节，返回该节的完整文本（含标题）。"""
    sections = extract_sections(content)
    for heading, body in sections.items():
        for kw in keywords:
            if kw in heading:
                return f"{heading}\n{body}"
    return None


# ── 主流程 ──────────────────────────────────────────────────

def is_plan_file(file_path: str) -> bool:
    if not re.search(r"(plan|计划).*\.md$", file_path, re.IGNORECASE):
        return False
    lower = file_path.lower()
    if "checklist" in lower or "template" in lower:
        return False
    return True


def validate(content: str) -> list[str]:
    """校验计划文档，返回问题列表（空列表 = 通过）。"""
    problems: list[str] = []

    for display_name, keywords, check_fn in CHECKS:
        section_text = find_section(content, keywords)
        if section_text is None:
            problems.append(f'缺少"{display_name}"章节')
            continue
        error = check_fn(section_text)
        if error:
            problems.append(error)

    return problems


def main():
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        sys.exit(0)
    # Edit 是增量操作，Write 时已完整校验
    if tool_name == "Edit":
        sys.exit(0)

    file_path = data.get("tool_input", {}).get("file_path", "")
    if not is_plan_file(file_path):
        sys.exit(0)

    content = data.get("tool_input", {}).get("content", "")
    if not content:
        sys.exit(0)

    problems = validate(content)

    if problems:
        print(json.dumps({
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "reason": "Plan 文档校验未通过：" + "；".join(problems) + "。参考 docs/plan-checklist.md"
            }
        }))
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
