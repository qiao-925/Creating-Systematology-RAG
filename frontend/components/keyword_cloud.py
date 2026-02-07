"""
词云组件：从静态 JSON 加载关键词，支持多选（最多 5 个）、生成问题、点击问题即发送。
词云区为浮动气泡，通过 streamlit-iframe-event 用 data URL 嵌入，点击后 postMessage 回传选中词，实现与下方联动。
"""

import base64
import json

import streamlit as st

from backend.infrastructure.config import config

# 词云展示数量、已选上限
MAX_CLOUD_ITEMS = 90
MAX_SELECTED = 5
KEYWORD_CLOUD_PATH = "data/keyword_cloud.json"
BUBBLE_CLOUD_HEIGHT_PX = 720
BUBBLE_COMPONENT_HEIGHT_PX = 800
KEYWORD_IFRAME_VERSION = "v3"


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
    if "show_keyword_cloud_dialog" not in st.session_state:
        st.session_state.show_keyword_cloud_dialog = False


def _on_open_keyword_cloud_dialog() -> None:
    """打开组词弹窗。"""
    st.session_state.show_keyword_cloud_dialog = True


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
    # 关闭弹窗
    st.session_state.show_keyword_cloud_dialog = False


def _on_regenerate() -> None:
    _on_generate()


# 终端主题气泡配色（深浅绿）
_BUBBLE_COLORS = [
    "#1E9E61", "#2AA66A", "#33AE73", "#2F9B67", "#3CB87D",
    "#46C086", "#3FAF79", "#2F8E5F", "#57C991", "#2B7E56",
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
  body {{
    margin: 0;
    font-family: "JetBrains Mono", "SFMono-Regular", Menlo, Consolas, monospace;
    background: #0F1825;
  }}
  .kw-box {{
    position: relative;
    width: 100%;
    height: {BUBBLE_CLOUD_HEIGHT_PX}px;
    background:
      linear-gradient(180deg, rgba(15,24,37,0.98) 0%, rgba(10,16,24,0.99) 100%),
      linear-gradient(90deg, rgba(147,229,164,0.04) 1px, transparent 1px),
      linear-gradient(0deg, rgba(147,229,164,0.04) 1px, transparent 1px);
    background-size: 100% 100%, 22px 22px, 22px 22px;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #2B3D52;
    box-shadow: inset 0 0 0 1px rgba(147,229,164,0.08);
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
    font-weight: 600;
    letter-spacing: 0.02em;
    color: #d8ffe5;
    text-shadow: 0 0 6px rgba(99, 218, 138, 0.25);
    white-space: nowrap;
    transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
    padding: 0 10px;
    border: 1px solid rgba(157, 246, 184, 0.42);
    box-shadow: 0 2px 8px rgba(0,0,0,0.25), inset 0 0 0 1px rgba(0,0,0,0.08);
  }}
  .kw-bubble:hover {{
    transform: scale(1.08);
    box-shadow: 0 0 0 1px rgba(147,229,164,0.4), 0 0 14px rgba(93, 215, 134, 0.33);
    filter: brightness(1.08);
  }}
  .kw-bubble.selected {{
    box-shadow: 0 0 0 2px rgba(147,229,164,0.95), 0 0 20px rgba(99,218,138,0.55), 0 4px 12px rgba(0,0,0,0.35);
    transform: scale(1.06);
    filter: brightness(1.06);
  }}
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

    with st.expander("[终端模块] 组词器", expanded=True):
        st.caption("$ 点击词气泡（最多 5 个）并生成问题")
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        if not items:
            st.warning("未找到词云数据（请生成 data/keyword_cloud.json）")
            return

        # 词云区：streamlit-iframe-event + data URL，点击气泡 postMessage 回传选中词
        bubble_html = _build_bubble_cloud_html(items, selected)
        st.markdown(
            f"""
<style>
.st-key-keyword_cloud_frame_shell iframe,
[data-testid="stDialog"] iframe[title="InnerSSO"] {{
    min-height: {BUBBLE_COMPONENT_HEIGHT_PX}px !important;
    height: {BUBBLE_COMPONENT_HEIGHT_PX}px !important;
}}

.st-key-keyword_cloud_iframe iframe,
.st-key-keyword_cloud_iframe [data-testid="stIFrame"] iframe,
.st-key-keyword_cloud_iframe [data-testid="stCustomComponentV1"] iframe {{
    min-height: {BUBBLE_COMPONENT_HEIGHT_PX}px !important;
    height: {BUBBLE_COMPONENT_HEIGHT_PX}px !important;
}}
</style>
            """,
            unsafe_allow_html=True,
        )
        try:
            from streamlit_iframe_event import st_iframe_event

            data_url = "data:text/html;base64," + base64.b64encode(bubble_html.encode("utf-8")).decode("ascii")
            try:
                with st.container(key="keyword_cloud_frame_shell"):
                    event_value = st_iframe_event(
                        data_url,
                        key=f"keyword_cloud_iframe_{KEYWORD_IFRAME_VERSION}",
                        default_width="100%",
                        default_height=f"{BUBBLE_COMPONENT_HEIGHT_PX}px",
                    )
            except TypeError:
                with st.container(key="keyword_cloud_frame_shell"):
                    event_value = st_iframe_event(
                        data_url,
                        key=f"keyword_cloud_iframe_{KEYWORD_IFRAME_VERSION}",
                        default_width="100%",
                    )
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

            components.html(bubble_html, height=BUBBLE_COMPONENT_HEIGHT_PX, scrolling=False)
            st.caption("[hint] 安装 streamlit-iframe-event 后可点击气泡与下方联动")

        st.markdown("---")
        st.caption("$ 选择关键词（最多 5 个）")
        options = [item.get("word", "") for item in items if item.get("word")]
        st.multiselect(
            "已选词",
            options=options,
            max_selections=MAX_SELECTED,
            key="keyword_cloud_selected",
            placeholder="请选择关键词",
            label_visibility="collapsed",
        )
        selected = st.session_state.keyword_cloud_selected
        if loading:
            st.info("[thinking] 正在生成问题...")
        st.button(
            "> 生成问题",
            key="keyword_cloud_generate_btn",
            disabled=not selected or loading,
            on_click=_on_generate,
        )

        st.markdown("---")

        # 延迟生成问题（避免回调阻塞 UI）
        if st.session_state.get("keyword_cloud_generate_pending"):
            st.session_state.keyword_cloud_generate_pending = False
            st.session_state.keyword_cloud_loading = True
            with st.spinner("生成中..."):
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

            generated = st.session_state.keyword_cloud_generated

        # 生成结果：2 个问题 + 重新生成
        if generated:
            st.caption("$ 候选问题")
            for idx, q in enumerate(generated, 1):
                st.button(
                    f"> {q}",
                    key=f"gen_q_{hash(q)}_{idx}",
                    use_container_width=True,
                    on_click=_on_use_question,
                    args=(q,),
                )
            st.button(
                "> 重新生成",
                key="keyword_cloud_regenerate",
                use_container_width=True,
                disabled=loading,
                on_click=_on_regenerate,
            )


@st.dialog("组词", width="large", icon="🧭")
def show_keyword_cloud_dialog() -> None:
    """显示组词弹窗。"""
    render_keyword_cloud()


def render_keyword_cloud_entry(
    button_label: str = "> 组词",
    use_container_width: bool = True,
) -> None:
    """渲染组词入口按钮，并按需打开弹窗。"""
    _ensure_state()
    st.button(
        button_label,
        key="open_keyword_cloud_dialog_btn",
        use_container_width=use_container_width,
        on_click=_on_open_keyword_cloud_dialog,
    )
    if st.session_state.get("show_keyword_cloud_dialog", False):
        show_keyword_cloud_dialog()
        st.session_state.show_keyword_cloud_dialog = False
