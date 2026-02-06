"""
词云组件：从静态 JSON 加载关键词，支持多选（最多 5 个）、生成问题、点击问题即发送。
词云区为浮动气泡，通过 streamlit-iframe-event 用 data URL 嵌入，点击后 postMessage 回传选中词，实现与下方联动。
"""

import base64
import json

import streamlit as st

from backend.infrastructure.config import config

# 词云展示数量、已选上限
MAX_CLOUD_ITEMS = 30
MAX_SELECTED = 5
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
    if "keyword_cloud_generate_pending" not in st.session_state:
        st.session_state.keyword_cloud_generate_pending = False


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
    # 延迟生成，避免按钮回调中执行耗时任务
    st.session_state.keyword_cloud_generate_pending = True


def _on_use_question(question: str) -> None:
    """点击问题时的回调：将问题添加到消息历史并标记为待处理"""
    # 确保 messages 列表存在
    if "messages" not in st.session_state:
        st.session_state.messages = []
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": question})
    # 设置待处理的问题（query_handler 会检测并处理）
    st.session_state.selected_question = question


def _on_regenerate() -> None:
    _on_generate()


# 气泡配色（与 iframe 内一致）
_BUBBLE_COLORS = [
    "#7c3aed", "#6366f1", "#3b82f6", "#0ea5e9", "#06b6d4",
    "#14b8a6", "#10b981", "#22c55e", "#84cc16", "#eab308",
    "#f59e0b", "#f97316", "#ef4444", "#ec4899", "#d946ef",
    "#a855f7", "#8b5cf6", "#6366f1", "#4f46e5", "#2563eb",
]


def _build_bubble_cloud_html(items: list[dict], selected: list[str]) -> str:
    """浮动气泡词云 HTML。点击后 postMessage(selected) 给父页，由 streamlit-iframe-event 转成组件返回值。"""
    items_js = json.dumps([{"word": item.get("word", ""), "weight": item.get("weight", 0)} for item in items if item.get("word")])
    selected_js = json.dumps(selected)
    colors_js = json.dumps(_BUBBLE_COLORS)
    max_selected = MAX_SELECTED

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  .kw-box {{
    position: relative;
    width: 100%;
    height: clamp(280px, 38vh, 420px);
    background: linear-gradient(160deg, #0f172a 0%%, #1e293b 40%%, #334155 100%);
    border-radius: 20px;
    overflow: hidden;
    border: 1px solid rgba(148,163,184,0.2);
    box-shadow: 0 4px 24px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.05);
  }}
  .kw-bubble {{
    position: absolute;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 999px;
    cursor: pointer;
    user-select: none;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.02em;
    color: rgba(255,255,255,0.95);
    text-shadow: 0 1px 2px rgba(0,0,0,0.25);
    white-space: nowrap;
    transition: transform 0.25s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.25s ease, filter 0.25s ease;
    padding: 0 10px;
    border: 1px solid rgba(255,255,255,0.2);
    box-shadow: 0 2px 8px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.15);
  }}
  .kw-bubble:hover {{ transform: scale(1.1); box-shadow: 0 6px 20px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.2); filter: brightness(1.1); }}
  .kw-bubble.selected {{ box-shadow: 0 0 0 2px rgba(255,255,255,0.95), 0 0 20px rgba(99,102,241,0.5), 0 4px 12px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.25); transform: scale(1.06); filter: brightness(1.05); }}
</style>
</head>
<body>
  <div class="kw-box" id="kw-box"></div>
  <script>
    (function() {{
      var items = {items_js};
      var initialSelected = {selected_js};
      var colors = {colors_js};
      var maxSelected = {max_selected};
      var selected = initialSelected.slice();
      var widthScale = 1.25;
      var box = document.getElementById('kw-box');
      if (!box || !items.length) return;

      function flushToParent() {{
        try {{
          window.parent.postMessage({{ code: 0, token: JSON.stringify(selected) }}, '*');
        }} catch (e) {{}}
      }}

      function darken(hex, pct) {{
        var n = parseInt(hex.slice(1), 16), r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
        r = Math.round(r * (1 - pct)); g = Math.round(g * (1 - pct)); b = Math.round(b * (1 - pct));
        return '#' + (0x1000000 + (r << 16) + (g << 8) + b).toString(16).slice(1);
      }}
      items.forEach(function(item, i) {{
        var w = item.word, weight = item.weight;
        if (!w) return;
        var el = document.createElement('div');
        el.className = 'kw-bubble' + (selected.indexOf(w) !== -1 ? ' selected' : '');
        el.textContent = w + '(' + weight + ')';
        el.setAttribute('data-word', w);
        el.style.background = 'linear-gradient(145deg, ' + colors[i % colors.length] + ' 0%, ' + darken(colors[i % colors.length], 0.25) + ' 100%)';
        el.style.width = 'auto'; el.style.minWidth = ((40 + (i % 5) * 12) * widthScale) + 'px'; el.style.height = (32 + (i % 4) * 6) + 'px';
        el.style.left = (8 + (i * 17) % 82) + '%'; el.style.top = (10 + (i * 23) % 72) + '%';
        el.style.animation = 'float' + (i % 4) + ' ' + (8 + i % 5) + 's ease-in-out infinite';
        el.onclick = function() {{
          var idx = selected.indexOf(w);
          if (idx !== -1) selected.splice(idx, 1);
          else if (selected.length < maxSelected) selected.push(w);
          box.querySelectorAll('.kw-bubble').forEach(function(b) {{
            var bw = b.getAttribute('data-word');
            if (selected.indexOf(bw) !== -1) b.classList.add('selected');
            else b.classList.remove('selected');
          }});
          flushToParent();
        }};
        box.appendChild(el);
      }});
      var style = document.createElement('style');
      style.textContent = '@keyframes float0{{0%,100%{{transform:translate(0,0)}} 25%{{transform:translate(6px,-8px)}} 50%{{transform:translate(-4px,4px)}} 75%{{transform:translate(8px,6px)}}}} @keyframes float1{{0%,100%{{transform:translate(0,0)}} 33%{{transform:translate(-6px,6px)}} 66%{{transform:translate(4px,-6px)}}}} @keyframes float2{{0%,100%{{transform:translate(0,0)}} 50%{{transform:translate(-8px,-4px)}}}} @keyframes float3{{0%,100%{{transform:translate(0,0)}} 25%{{transform:translate(4px,8px)}} 50%{{transform:translate(-6px,-4px)}} 75%{{transform:translate(-2px,6px)}}}}';
      document.head.appendChild(style);
    }})();
  </script>
</body>
</html>
"""
    return html


def render_keyword_cloud() -> None:
    """渲染探索知识库大框：词云区（气泡浮动）、已选词、生成问题、生成结果。"""
    _ensure_state()
    cloud = _load_keyword_cloud()
    items = cloud[:MAX_CLOUD_ITEMS]
    selected = st.session_state.keyword_cloud_selected
    generated = st.session_state.keyword_cloud_generated
    loading = st.session_state.keyword_cloud_loading

    st.caption("点击气泡选词（最多 5 个），再点击「生成问题」")
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    if not items:
        st.warning("未找到词云数据（离线生成脚本已移除，请改用其他方式生成 data/keyword_cloud.json）")
        return

    # 词云区：streamlit-iframe-event + data URL，点击气泡 postMessage 回传选中词，组件返回值同步到 session_state
    bubble_html = _build_bubble_cloud_html(items, selected)
    try:
        from streamlit_iframe_event import st_iframe_event

        data_url = "data:text/html;base64," + base64.b64encode(bubble_html.encode("utf-8")).decode("ascii")
        event_value = st_iframe_event(data_url, key="keyword_cloud_iframe", default_width="100%")
        if event_value is not None and isinstance(event_value, dict) and "token" in event_value:
            try:
                new_selected = json.loads(event_value["token"])
                if isinstance(new_selected, list):
                    st.session_state.keyword_cloud_selected = new_selected
                    selected = st.session_state.keyword_cloud_selected
            except (TypeError, ValueError):
                pass
    except ImportError:
        import streamlit.components.v1 as components

        components.html(bubble_html, height=460, scrolling=False)
        st.caption("气泡选词需安装 streamlit-iframe-event 才能与下方联动，请用下方多选选词。")
    st.markdown("---")

    # 已选词：从 URL 同步后与 session_state 一致，可在此勾选或依赖上方气泡
    st.caption("已选词（最多 5 个，可点击上方气泡或在此勾选）")
    options = [item.get("word", "") for item in items if item.get("word")]
    st.multiselect(
        "已选词",
        options=options,
        max_selections=MAX_SELECTED,
        key="keyword_cloud_selected",
        label_visibility="collapsed",
    )
    selected = st.session_state.keyword_cloud_selected
    if loading:
        st.info("🤔 正在生成问题...")
    st.button(
        "✨ 生成问题",
        key="keyword_cloud_generate_btn",
        disabled=not selected or loading,
        on_click=_on_generate,
    )
    st.markdown("---")

    # 延迟生成问题（避免回调阻塞 UI）
    if st.session_state.get("keyword_cloud_generate_pending"):
        st.session_state.keyword_cloud_generate_pending = False
        st.session_state.keyword_cloud_loading = True
        with st.spinner("正在生成问题..."):
            try:
                from backend.business.rag_engine.processing.question_generator import generate_questions
                model_id = st.session_state.get("selected_model")
                questions = generate_questions(selected, model_id=model_id)
                # 确保至少返回 2 个问题，不足则用占位符
                if len(questions) < 2:
                    questions.extend([f"请详细解释关于{selected[0]}的内容"] * (2 - len(questions)))
                st.session_state.keyword_cloud_generated = questions[:2]
            except Exception as e:
                from backend.infrastructure.logger import get_logger
                logger = get_logger("keyword_cloud")
                logger.exception("生成问题失败: %s", e)
                st.session_state.keyword_cloud_generated = []
            finally:
                st.session_state.keyword_cloud_loading = False

        # 同步生成结果
        generated = st.session_state.keyword_cloud_generated


    # 生成结果：2 个问题 + 重新生成
    if generated:
        st.caption("生成结果：点击问题将填入并发送")
        for idx, q in enumerate(generated, 1):
            st.button(
                f"💬 {q}",
                key=f"gen_q_{hash(q)}_{idx}",
                use_container_width=True,
                on_click=_on_use_question,
                args=(q,),
            )
        st.button(
            "💬 重新生成",
            key="keyword_cloud_regenerate",
            use_container_width=True,
            disabled=loading,
            on_click=_on_regenerate,
        )
