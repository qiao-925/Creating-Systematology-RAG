"""
词云组件：从静态 JSON 加载关键词，支持多选（最多 10 个）、生成问题、点击问题即发送。
"""

import json
from pathlib import Path

import streamlit as st

from backend.infrastructure.config import config

# 词云展示数量、已选上限
MAX_CLOUD_ITEMS = 60
MAX_SELECTED = 10
KEYWORD_CLOUD_PATH = "data/keyword_cloud.json"


def _load_keyword_cloud() -> list[dict]:
    path = config.PROJECT_ROOT / KEYWORD_CLOUD_PATH
    if not path.is_file():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _ensure_state() -> None:
    if "keyword_cloud_selected" not in st.session_state:
        st.session_state.keyword_cloud_selected = []
    if "keyword_cloud_generated" not in st.session_state:
        st.session_state.keyword_cloud_generated = []
    if "keyword_cloud_loading" not in st.session_state:
        st.session_state.keyword_cloud_loading = False


def _on_toggle_word(word: str) -> None:
    sel = st.session_state.keyword_cloud_selected
    if word in sel:
        sel.remove(word)
    elif len(sel) < MAX_SELECTED:
        sel.append(word)
    st.session_state.keyword_cloud_selected = sel


def _on_generate() -> None:
    _ensure_state()
    sel = st.session_state.keyword_cloud_selected
    if not sel:
        return
    st.session_state.keyword_cloud_loading = True
    try:
        from backend.business.rag_engine.processing.question_generator import generate_questions
        model_id = st.session_state.get("selected_model")
        questions = generate_questions(sel, model_id=model_id)
        st.session_state.keyword_cloud_generated = questions[:2]
    finally:
        st.session_state.keyword_cloud_loading = False


def _on_use_question(question: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.selected_question = question


def _on_regenerate() -> None:
    _on_generate()


def render_keyword_cloud() -> None:
    """渲染探索知识库大框：词云区、已选词、生成问题、生成结果。"""
    _ensure_state()
    cloud = _load_keyword_cloud()
    items = cloud[:MAX_CLOUD_ITEMS]
    selected = st.session_state.keyword_cloud_selected
    generated = st.session_state.keyword_cloud_generated
    loading = st.session_state.keyword_cloud_loading

    st.subheader("💡 探索知识库")
    st.caption("点击词云选词（最多 10 个），再点击「生成问题」")

    if not items:
        st.warning("未找到词云数据，请先运行 scripts/build_keyword_cloud.py 生成 data/keyword_cloud.json")
        return

    # 词云区：多列按钮，按权重分档显示
    max_w = max((x.get("weight", 1) for x in items), default=1)
    cols = st.columns(8)
    col_idx = 0
    for i, item in enumerate(items):
        w = item.get("word", "")
        weight = item.get("weight", 1)
        if not w:
            continue
        is_selected = w in selected
        with cols[col_idx % 8]:
            st.button(
                w,
                key=f"kw_{i}_{w}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
                on_click=_on_toggle_word,
                args=(w,),
            )
        col_idx += 1
    st.markdown("---")

    # 选择框（已选词，非输入框）
    st.caption("已选词（最多 10 个）")
    if selected:
        st.write("、".join(selected))
    else:
        st.caption("尚未选择关键词")
    st.button(
        "✨ 生成问题",
        key="keyword_cloud_generate_btn",
        disabled=not selected or loading,
        on_click=_on_generate,
    )
    st.markdown("---")

    # 生成结果：2 个问题 + 重新生成
    if generated:
        st.caption("生成结果：点击问题将填入并发送")
        for q in generated:
            st.button(
                f"💬 {q}",
                key=f"gen_q_{hash(q)}",
                use_container_width=True,
                on_click=_on_use_question,
                args=(q,),
            )
        st.button(
            "💬 重新生成",
            key="keyword_cloud_regenerate",
            use_container_width=True,
            on_click=_on_regenerate,
        )
