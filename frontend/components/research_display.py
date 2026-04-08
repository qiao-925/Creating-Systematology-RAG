"""
研究结果展示组件：将 ResearchOutput 渲染为结构化 Streamlit UI

核心职责：
- render_research_output()：在聊天消息中渲染研究结果
- 展示判断、证据列表、置信度、张力、下一步追问

不负责：研究执行、路由分派、状态管理
"""

def render_research_output(output) -> str:
    """将 ResearchOutput 渲染为 Markdown 字符串

    Args:
        output: ResearchOutput 实例（或含相同字段的 dict）

    Returns:
        格式化后的 Markdown 文本
    """
    if isinstance(output, dict):
        return _render_from_dict(output)
    return _render_from_model(output)


def _render_from_model(output) -> str:
    """从 ResearchOutput Pydantic 模型渲染"""
    lines = []

    # 判断
    lines.append(f"### 研究判断\n\n{output.judgment}")

    # 置信度
    badge = _confidence_badge(output.confidence.value if hasattr(output.confidence, 'value') else str(output.confidence))
    lines.append(f"\n**置信度**：{badge}")

    # 证据
    if output.evidence:
        lines.append("\n### 关键证据\n")
        for i, item in enumerate(output.evidence, 1):
            source = item.source_ref or "未知来源"
            score = f"{item.score:.2f}" if item.score else ""
            text_preview = item.text[:200].replace("\n", " ")
            lines.append(f"**[{i}]** {source} {score}\n> {text_preview}\n")

    # 张力
    if output.tensions:
        lines.append("\n### 未解决的张力\n")
        for tension in output.tensions:
            lines.append(f"- {tension}")

    # 追问方向
    if output.next_questions:
        lines.append("\n### 值得继续追问\n")
        for q in output.next_questions:
            lines.append(f"- {q}")

    # 元信息
    stop = output.stop_reason.value if hasattr(output.stop_reason, 'value') else str(output.stop_reason)
    lines.append(f"\n---\n*轮次 {output.turns_used} | 停止原因: {stop}*")

    return "\n".join(lines)


def _render_from_dict(data: dict) -> str:
    """从字典渲染（RAGResponse.metadata 兼容路径）"""
    lines = []

    judgment = data.get("judgment") or data.get("answer", "")
    lines.append(f"### 研究判断\n\n{judgment}")

    confidence = data.get("confidence", "low")
    lines.append(f"\n**置信度**：{_confidence_badge(confidence)}")

    tensions = data.get("tensions", [])
    if tensions:
        lines.append("\n### 未解决的张力\n")
        for t in tensions:
            lines.append(f"- {t}")

    next_questions = data.get("next_questions", [])
    if next_questions:
        lines.append("\n### 值得继续追问\n")
        for q in next_questions:
            lines.append(f"- {q}")

    turns = data.get("turns_used", 0)
    stop = data.get("stop_reason", "")
    if turns or stop:
        lines.append(f"\n---\n*轮次 {turns} | 停止原因: {stop}*")

    return "\n".join(lines)


def _confidence_badge(level: str) -> str:
    """置信度徽章"""
    badges = {
        "high": "🟢 高",
        "medium": "🟡 中",
        "low": "🔴 低",
    }
    return badges.get(level, f"⚪ {level}")
