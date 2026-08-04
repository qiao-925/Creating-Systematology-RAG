#!/usr/bin/env python3
"""Figma MCP 每日调用上限测试。

通过反复调用 get_metadata（轻量只读工具）来探测速率限制。
跟踪 HTTP 状态码、Retry-After、X-Figma-Rate-Limit-Type 等响应头。

用法:
  # 方式 1: 从 Figma 网页抓 OAuth token（推荐）
  #   1. 打开 https://www.figma.com，F12 → Network → 找任意 API 请求
  #   2. 复制 Authorization header 中的 Bearer token
  set FIGMA_MCP_TOKEN=your_oauth_token
  python scripts/figma_rate_limit_test.py

  # 方式 2: Figma 桌面版 Dev Mode（需打开 Figma 桌面端）
  set FIGMA_MCP_BASE_URL=http://127.0.0.1:3845/mcp
  python scripts/figma_rate_limit_test.py

  # 可选参数:
  set FIGMA_FILE_KEY=your_file_key    # 要查询的文件 key
  set FIGMA_MAX_CALLS=300             # 最大调用次数（默认 300）
  set FIGMA_INTERVAL=1                # 每次调用间隔秒数（默认 1）
  set FIGMA_LOG_FILE=rate_limit_log.jsonl  # 日志文件路径
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

# ── 配置 ──────────────────────────────────────────────────────────────
BASE_URL = os.environ.get("FIGMA_MCP_BASE_URL", "https://mcp.figma.com/mcp")
TOKEN = os.environ.get("FIGMA_MCP_TOKEN", "")
FILE_KEY = os.environ.get("FIGMA_FILE_KEY", "GetdOs1IPlJcW5mdrKhVH3")
MAX_CALLS = int(os.environ.get("FIGMA_MAX_CALLS", "300"))
INTERVAL = float(os.environ.get("FIGMA_INTERVAL", "1"))
LOG_FILE = os.environ.get("FIGMA_LOG_FILE", "rate_limit_log.jsonl")
ACCEPT = "application/json, text/event-stream"

# ── 统计 ──────────────────────────────────────────────────────────────
stats = {
    "start_time": None,
    "total_calls": 0,
    "success": 0,
    "rate_limited": 0,   # 429
    "errors": 0,          # 其他错误
    "monthly_limit": 0,   # 月度配额耗尽
    "results": [],        # 每次调用的详细记录
}


def post(payload: dict, session_id: str | None = None) -> tuple[int, dict[str, str], str]:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": ACCEPT}
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


def parse_session_id(hdrs: dict[str, str]) -> str | None:
    for key in ("mcp-session-id", "Mcp-Session-Id", "MCP-Session--Id"):
        if key in hdrs:
            return hdrs[key]
    return None


def init_session() -> str | None:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "rate-limit-test", "version": "1.0"},
        },
    }
    status, hdrs, body = post(payload)
    if status != 200:
        print(f"[ERROR] initialize 失败: {status}")
        print(body[:1000])
        return None
    session = parse_session_id(hdrs)
    if session:
        post({"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id=session)
    return session


def extract_rate_info(hdrs: dict[str, str], body: str) -> dict:
    """从响应头和 body 中提取限流信息。"""
    info = {
        "status_code": None,
        "retry_after": hdrs.get("Retry-After"),
        "rate_limit_type": hdrs.get("X-Figma-Rate-Limit-Type"),
        "plan_tier": hdrs.get("X-Figma-Plan-Tier"),
        "upgrade_link": hdrs.get("X-Figma-Upgrade-Link"),
    }
    # 尝试从 body 中提取错误信息
    try:
        data = json.loads(body)
        if "error" in data:
            info["error_message"] = data["error"].get("message", "")
        if "result" in data:
            content = data["result"].get("content", [])
            for c in content:
                if c.get("type") == "text":
                    text = c["text"]
                    if "rate" in text.lower() or "limit" in text.lower() or "quota" in text.lower():
                        info["body_rate_hint"] = text[:500]
                    break
    except (json.JSONDecodeError, AttributeError):
        pass
    return info


def classify_response(status: int, hdrs: dict, body: str) -> str:
    """分类响应类型。"""
    if status == 200:
        return "success"
    if status == 429:
        return "rate_limited"
    if status in (401, 403):
        return "auth_error"
    body_lower = body.lower()
    if "month" in body_lower or "quota" in body_lower or "upgrade" in body_lower:
        return "monthly_limit"
    return "error"


def call_get_metadata(session: str, call_num: int) -> dict:
    """调用 get_metadata 工具并记录结果。"""
    payload = {
        "jsonrpc": "2.0",
        "id": call_num,
        "method": "tools/call",
        "params": {
            "name": "get_metadata",
            "arguments": {"fileKey": FILE_KEY},
        },
    }

    start = time.monotonic()
    status, hdrs, body = post(payload, session_id=session)
    elapsed = time.monotonic() - start

    rate_info = extract_rate_info(hdrs, body)
    rate_info["status_code"] = status
    classification = classify_response(status, hdrs, body)

    record = {
        "call_num": call_num,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "elapsed_s": round(elapsed, 3),
        "classification": classification,
        "rate_limit_type": rate_info.get("rate_limit_type"),
        "retry_after": rate_info.get("retry_after"),
        "plan_tier": rate_info.get("plan_tier"),
        "error_message": rate_info.get("error_message", ""),
        "body_rate_hint": rate_info.get("body_rate_hint", ""),
    }
    return record


def print_banner():
    print("=" * 60)
    print("  Figma MCP 每日调用上限测试")
    print("=" * 60)
    print(f"  Server:      {BASE_URL}")
    print(f"  Token:       {'已设置' if TOKEN else '未设置'}")
    print(f"  File Key:    {FILE_KEY}")
    print(f"  Max Calls:   {MAX_CALLS}")
    print(f"  Interval:    {INTERVAL}s")
    print(f"  Log File:    {LOG_FILE}")
    print("=" * 60)


def print_progress(record: dict, total: int):
    cls = record["classification"]
    status = record["status"]
    elapsed = record["elapsed_s"]
    rate_type = record.get("rate_limit_type") or "-"

    icon = {
        "success": "✓",
        "rate_limited": "⛔",
        "monthly_limit": "⛔(月)",
        "auth_error": "✗",
        "error": "✗",
    }.get(cls, "?")

    print(
        f"  [{record['call_num']:>4}/{total}] {icon} "
        f"HTTP {status} | {cls:<14} | {elapsed:.2f}s | "
        f"rate_type={rate_type}"
    )


def print_summary():
    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    print(f"  总调用次数:     {stats['total_calls']}")
    print(f"  成功:           {stats['success']}")
    print(f"  被限流 (429):   {stats['rate_limited']}")
    print(f"  月度配额耗尽:   {stats['monthly_limit']}")
    print(f"  其他错误:       {stats['errors']}")
    print(f"  开始时间:       {stats['start_time']}")
    print(f"  结束时间:       {datetime.now(timezone.utc).isoformat()}")

    if stats["results"]:
        # 找到首次被限流的位置
        first_limit = None
        for r in stats["results"]:
            if r["classification"] in ("rate_limited", "monthly_limit"):
                first_limit = r
                break

        if first_limit:
            print(f"\n  ⚡ 首次触发限制:")
            print(f"     调用序号:   #{first_limit['call_num']}")
            print(f"     限制类型:   {first_limit['rate_limit_type'] or first_limit['classification']}")
            print(f"     Retry-After: {first_limit['retry_after'] or 'N/A'}")
            if first_limit.get("body_rate_hint"):
                print(f"     提示信息:   {first_limit['body_rate_hint'][:200]}")
            if first_limit.get("error_message"):
                print(f"     错误信息:   {first_limit['error_message'][:200]}")
        else:
            print(f"\n  ✅ 在 {stats['total_calls']} 次调用内未触发限制")

    # 输出每次调用间隔统计
    if len(stats["results"]) > 1:
        intervals = []
        for i in range(1, len(stats["results"])):
            t1 = datetime.fromisoformat(stats["results"][i - 1]["timestamp"])
            t2 = datetime.fromisoformat(stats["results"][i]["timestamp"])
            intervals.append((t2 - t1).total_seconds())
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            print(f"\n  平均调用间隔:   {avg_interval:.2f}s")

    print("=" * 60)


def main() -> int:
    print_banner()

    if not TOKEN and "127.0.0.1" not in BASE_URL:
        print("\n[ERROR] 远程 MCP 需要 FIGMA_MCP_TOKEN。")
        print("  获取方法: 打开 figma.com → F12 → Network → 找 API 请求")
        print("  → 复制 Authorization: Bearer xxx 中的 token")
        print("\n  或使用桌面版: set FIGMA_MCP_BASE_URL=http://127.0.0.1:3845/mcp")
        return 1

    print("\n[1/3] 初始化 MCP 会话...")
    session = init_session()
    if not session:
        print("[ERROR] 无法建立 MCP 会话")
        return 1
    print(f"  会话 ID: {session[:20]}...")

    # 先调一次 whoami 确认认证正常
    print("\n[2/3] 验证认证 (whoami)...")
    whoami_payload = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "tools/call",
        "params": {"name": "whoami", "arguments": {}},
    }
    status, hdrs, body = post(whoami_payload, session_id=session)
    print(f"  whoami status: {status}")
    if status != 200:
        print(f"  body: {body[:500]}")
        print("[ERROR] 认证失败，无法继续")
        return 1
    print("  认证正常 ✓")

    # 开始正式测试
    print(f"\n[3/3] 开始调用 get_metadata x {MAX_CALLS} 次...")
    print(f"  工具: get_metadata | 文件: {FILE_KEY}")
    print(f"  每次间隔: {INTERVAL}s\n")

    stats["start_time"] = datetime.now(timezone.utc).isoformat()

    with open(LOG_FILE, "w", encoding="utf-8") as logf:
        for i in range(1, MAX_CALLS + 1):
            record = call_get_metadata(session, i)
            stats["total_calls"] = i
            stats["results"].append(record)

            cls = record["classification"]
            if cls == "success":
                stats["success"] += 1
            elif cls == "rate_limited":
                stats["rate_limited"] += 1
            elif cls == "monthly_limit":
                stats["monthly_limit"] += 1
            else:
                stats["errors"] += 1

            print_progress(record, MAX_CALLS)
            logf.write(json.dumps(record, ensure_ascii=False) + "\n")
            logf.flush()

            # 遇到月度限制直接停止
            if cls == "monthly_limit":
                print("\n  ⛔ 月度配额已耗尽，测试终止")
                break

            # 遇到 429 时，等待 Retry-After 后继续（探测是否恢复）
            if cls == "rate_limited":
                retry_after = record.get("retry_after")
                if retry_after and str(retry_after).isdigit():
                    wait = int(retry_after)
                    print(f"  ⏳ 等待 Retry-After: {wait}s ...")
                    time.sleep(wait)
                else:
                    time.sleep(INTERVAL)
                continue

            # 遇到认证错误直接停止
            if cls == "auth_error":
                print("\n  ✗ 认证错误，测试终止")
                break

            time.sleep(INTERVAL)

    print_summary()
    return 0


if __name__ == "__main__":
    sys.exit(main())
