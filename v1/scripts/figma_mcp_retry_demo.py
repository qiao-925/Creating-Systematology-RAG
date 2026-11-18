#!/usr/bin/env python3
"""Figma MCP 连通性自测：initialize → whoami，失败时等待 5s 重试。

用法:
  # 远程（需 OAuth token，与 Cursor 登录同一账号）
  set FIGMA_MCP_TOKEN=your_access_token
  python scripts/figma_mcp_retry_demo.py

  # 桌面 MCP（Figma 桌面版 Dev Mode 已开启）
  set FIGMA_MCP_BASE_URL=http://127.0.0.1:3845/mcp
  python scripts/figma_mcp_retry_demo.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE_URL = os.environ.get("FIGMA_MCP_BASE_URL", "https://mcp.figma.com/mcp")
TOKEN = os.environ.get("FIGMA_MCP_TOKEN", "")
MAX_ATTEMPTS = int(os.environ.get("FIGMA_MCP_MAX_ATTEMPTS", "3"))
WAIT_SECONDS = int(os.environ.get("FIGMA_MCP_WAIT_SECONDS", "5"))

ACCEPT = "application/json, text/event-stream"


def post(payload: dict, session_id: str | None = None) -> tuple[int, dict[str, str], str]:
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": ACCEPT,
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    if session_id:
        headers["mcp-session-id"] = session_id

    req = urllib.request.Request(BASE_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, dict(resp.headers), body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, dict(e.headers), body


def parse_session_id(response_headers: dict[str, str]) -> str | None:
    for key in ("mcp-session-id", "Mcp-Session-Id", "MCP-Session-Id"):
        if key in response_headers:
            return response_headers[key]
    return None


def main() -> int:
    print(f"BASE_URL={BASE_URL}")
    print(f"TOKEN={'set' if TOKEN else 'not set (401 expected on remote)'}")

    session_id: str | None = None
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "figma-mcp-retry-demo", "version": "1.0"},
        },
    }

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n--- initialize attempt {attempt}/{MAX_ATTEMPTS} ---")
        status, hdrs, body = post(init_payload)
        print("status:", status)
        if status == 401:
            print("body:", body[:500])
            print("Remote MCP needs FIGMA_MCP_TOKEN or use desktop BASE_URL.")
            if attempt < MAX_ATTEMPTS:
                time.sleep(WAIT_SECONDS)
            continue
        session_id = parse_session_id(hdrs)
        print("session:", session_id or "(not in headers; check body/SSE)")
        print("body preview:", body[:400])
        if status == 200 and session_id:
            break
        retry_after = hdrs.get("Retry-After")
        wait = int(retry_after) if retry_after and retry_after.isdigit() else WAIT_SECONDS
        if attempt < MAX_ATTEMPTS:
            print(f"waiting {wait}s...")
            time.sleep(wait)

    if not session_id:
        print("\nNo session id; cannot call whoami.")
        return 1

    post(
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        session_id=session_id,
    )

    whoami_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "whoami", "arguments": {}},
    }

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n--- whoami attempt {attempt}/{MAX_ATTEMPTS} ---")
        status, hdrs, body = post(whoami_payload, session_id=session_id)
        print("status:", status)
        print("body:", body[:2000])
        if status == 200:
            return 0
        if "month" in body.lower() or "upgrade" in body.lower():
            print("Monthly quota hit; retry will not help.")
            return 2
        wait = WAIT_SECONDS
        ra = hdrs.get("Retry-After")
        if ra and str(ra).isdigit():
            wait = int(ra)
        if attempt < MAX_ATTEMPTS:
            print(f"waiting {wait}s...")
            time.sleep(wait)

    return 1


if __name__ == "__main__":
    sys.exit(main())
