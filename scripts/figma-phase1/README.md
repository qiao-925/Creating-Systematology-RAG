# CLDFlow Figma Phase 1 — Executor Scripts

**File key:** `GetdOs1IPlJcW5mdrKhVH3`  
**Pages:** `01 — Canonical (Vercel)` · `02 — Style Explorations (7×)` · `03 — Thinking & Workflow`

## Prerequisites

1. Open the file in Figma desktop with **Dev Mode → Enable desktop MCP**.
2. Or set `FIGMA_MCP_TOKEN` and use remote `https://mcp.figma.com/mcp`.
3. Account needs **Can edit** on the file (View seat may block `use_figma` writes).
4. Run from repo root:

```powershell
$env:FIGMA_MCP_BASE_URL = "http://127.0.0.1:3845/mcp"
python scripts/figma_phase1_build.py
```

Scripts run in order with **≥5s** between MCP calls. Read tools (`get_screenshot`) are optional and consume monthly View-seat quota (~6/month).

## Script order

| # | File | Page |
|---|------|------|
| 0 | `00_inspect.js` | all (read) |
| 1 | `01_page01_clean.js` | 01 |
| 2 | `02_page01_canonical.js` | 01 |
| 3 | `03_page02_styles.js` | 02 |
| 4 | `04_page03_thinking.js` | 03 |

Manual `use_figma` in Cursor: paste each `.js` body, set `fileKey: "GetdOs1IPlJcW5mdrKhVH3"`, `skillNames: "figma-use"`.
