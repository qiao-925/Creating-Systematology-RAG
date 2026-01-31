"""
请求节流工具
统一控制最小请求间隔，避免短时间多次触发查询
"""

from __future__ import annotations

import time

import streamlit as st


DEFAULT_MIN_REQUEST_INTERVAL_SECONDS = 3.0


def throttle_requests(
    min_gap_seconds: float | None = None,
    state_key: str = "prev_question_timestamp",
) -> None:
    """节流请求，确保两次请求至少间隔 min_gap_seconds。

    Args:
        min_gap_seconds: 最小间隔（秒），None 则使用默认值。
        state_key: 存储上次请求时间戳的 session_state key。
    """
    if min_gap_seconds is None:
        min_gap_seconds = DEFAULT_MIN_REQUEST_INTERVAL_SECONDS

    last_ts = st.session_state.get(state_key)
    now = time.time()

    if last_ts is None:
        st.session_state[state_key] = now
        return

    elapsed = now - last_ts
    if elapsed < min_gap_seconds:
        # Non-blocking throttle: avoid sleeping in Streamlit run loop
        # to prevent UI "white overlay" / laggy reruns.
        st.session_state[state_key] = now
        return

    st.session_state[state_key] = now
