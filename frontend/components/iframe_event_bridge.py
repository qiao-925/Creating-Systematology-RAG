from pathlib import Path

import streamlit.components.v1 as components


_COMPONENT_PATH = Path(__file__).resolve().parent / "iframe_event_bridge"
_iframe_event_component = components.declare_component(
    "keyword-cloud-iframe-event",
    path=str(_COMPONENT_PATH),
)


def st_iframe_event(
    url: str,
    key: str | None = None,
    default_width: str = "100%",
    default_height: str = "800px",
):
    return _iframe_event_component(
        key=key,
        url=url,
        default_width=default_width,
        default_height=default_height,
    )

