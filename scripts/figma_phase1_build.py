#!/usr/bin/env python3
"""Run CLDFlow Figma phase-1 use_figma scripts via MCP (desktop or remote).

Requires Figma desktop MCP (http://127.0.0.1:3845/mcp) or FIGMA_MCP_TOKEN for remote.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

FILE_KEY = "GetdOs1IPlJcW5mdrKhVH3"
BASE_URL = os.environ.get("FIGMA_MCP_BASE_URL", "http://127.0.0.1:3845/mcp")
TOKEN = os.environ.get("FIGMA_MCP_TOKEN", "")
WAIT_SECONDS = int(os.environ.get("FIGMA_MCP_WAIT_SECONDS", "5"))
SCRIPT_DIR = Path(__file__).resolve().parent / "figma-phase1"
SCRIPTS = [
    "00_inspect.js",
    "01_page01_clean.js",
    "02_page01_canonical.js",
    "03_page02_styles.js",
    "04_page03_thinking.js",
]
ACCEPT = "application/json, text/event-stream"


def post(payload: dict, session_id: str | None = None) -> tuple[int, dict[str, str], str]:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": ACCEPT}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    if session_id:
        headers["mcp-session-id"] = session_id
    req = urllib.request.Request(BASE_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", errors="replace")


def parse_session_id(hdrs: dict[str, str]) -> str | None:
    for key in ("mcp-session-id", "Mcp-Session-Id", "MCP-Session-Id"):
        if key in hdrs:
            return hdrs[key]
    return None


def init_session() -> str | None:
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "cldflow-phase1-build", "version": "1.0"},
        },
    }
    status, hdrs, body = post(init_payload)
    if status != 200:
        print(f"initialize failed: {status}\n{body[:800]}")
        return None
    session = parse_session_id(hdrs)
    if session:
        post({"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id=session)
    return session


def call_tool(session: str, name: str, arguments: dict) -> tuple[int, str]:
    payload = {
        "jsonrpc": "2.0",
        "id": name,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    return post(payload, session_id=session)


def run_use_figma(session: str, code: str, description: str) -> int:
    status, body = call_tool(
        session,
        "use_figma",
        {"fileKey": FILE_KEY, "code": code, "description": description, "skillNames": "figma-use"},
    )
    print(f"  status={status}")
    print(body[:4000])
    if status != 200:
        return 1
    if "error" in body.lower() and '"isError":true' in body.replace(" ", ""):
        return 1
    return 0


def main() -> int:
    print(f"BASE_URL={BASE_URL} TOKEN={'set' if TOKEN else 'not set'}")
    session = init_session()
    if not session:
        print("\nBlocked: no MCP session. Enable desktop MCP or set FIGMA_MCP_TOKEN.")
        print("See docs/design/figma-mcp-rate-limits-and-curl-demo.md §8")
        return 1

    whoami_status, whoami_body = call_tool(session, "whoami", {})
    print(f"whoami status={whoami_status}\n{whoami_body[:1500]}\n")

    for i, name in enumerate(SCRIPTS):
        path = SCRIPT_DIR / name
        if not path.exists():
            print(f"Missing {path}")
            return 1
        code = path.read_text(encoding="utf-8")
        print(f"\n=== [{i + 1}/{len(SCRIPTS)}] {name} ===")
        rc = run_use_figma(session, code, f"CLDFlow phase1: {name}")
        if rc != 0:
            return rc
        if i < len(SCRIPTS) - 1:
            print(f"sleep {WAIT_SECONDS}s...")
            time.sleep(WAIT_SECONDS)

    print("\nDone. Verify with get_screenshot per page in Cursor (read quota).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
