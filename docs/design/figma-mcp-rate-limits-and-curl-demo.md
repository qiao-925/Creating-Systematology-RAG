# Figma MCP：限速、重试与 cURL 自测

> 官方说明：[Rate limits & access](https://developers.figma.com/docs/figma-mcp-server/rate-limits-access/)  
> 远程端点：`https://mcp.figma.com/mcp`（与 Cursor `mcp.json` 一致）

## 1. 两种「被拦住」要分开看

| 类型 | 典型报错文案 | 等 5 秒再试有用吗 |
|------|----------------|-------------------|
| **每分钟限速** | HTTP 429 / 提示 rate limit，响应头可能有 `Retry-After` | **有用**（按 `Retry-After` 或默认 5–15s） |
| **月度/日度额度** | `Starter plan` / `View seat` / `6 tool calls per month` | **没用**（需升级席位或换 Full/Dev） |

### 读操作 vs 写操作

- **计入限速（读）**：`get_metadata`、`get_design_context`、`get_screenshot`、`get_variable_defs` 等从 Figma **读取**的工具。
- **官方写明豁免（常见）**：`whoami`、`generate_figma_design`、`add_code_connect_map`；**`use_figma` 写入**在文档里属于写画布，理论上不应占「读」配额（若仍报 Education/Starter 限额，以当时 Figma 策略为准）。

### 你当前账号（曾用 `whoami` 测到）

- `noneplus@outlook.com`，**View seat**，Education → **读工具约 6 次/月**。
- 访问**别人 Starter 团队**里的文件时，可能按**文件所在团队计划**计费，错误里会出现 `Starter plan` 字样。

**结论**：连续快速调用要 **间隔 5s+**；若已是「6/month」类错误，只能换 **Full/Dev 席位** 或等下月，重试无效。

---

## 2. Agent 侧重试约定（本仓库后续执行 Figma MCP 时）

1. 读类工具默认 **串行**，两次调用之间 **`sleep 5`**（秒）。
2. 若返回 429 或文案含 `rate limit` / `Too Many Requests`：
   - 有 `Retry-After` → 等待该秒数（上限 60s）；
   - 否则 → **等待 5s**，最多 **3 次**。
3. 若文案含 `6 tool calls per month` / `Upgrade your plan` → **停止重试**，改提示用户升级或改用手动复制。
4. 批量读（metadata + screenshot + design_context）→ **只选一种**，不要同一轮全打。

---

## 3. cURL 自测（Windows 用 `curl.exe`）

PowerShell 里 `curl` 常被映射成 `Invoke-WebRequest`，请用 **`curl.exe`**。

### 3.1 准备 JSON  body（任意目录均可）

`init.json`：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": { "name": "curl-demo", "version": "1.0" }
  }
}
```

`initialized.json`：

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

`whoami.json`：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "whoami",
    "arguments": {}
  }
}
```

### 3.2 远程服务器（需 OAuth Token）

在 Cursor 里 **Settings → MCP → Figma → Connect** 完成 OAuth 后，远程调用必须带：

```http
Authorization: Bearer <FIGMA_MCP_ACCESS_TOKEN>
```

Cursor **不会**在 UI 里直接展示该 token。纯 cURL 测远程有两种做法：

- **A（推荐自测）**：用下文 **3.3 桌面本地 MCP**，无需 Bearer。  
- **B**：自行走 Figma OAuth（`www-authenticate` 响应里的 `authorization_uri`），拿到 access token 后填入下面命令。

**Step 1 — initialize（看是否 401 / 是否返回 session）**

```bash
curl.exe -sS -D headers.txt -o body.txt -X POST "https://mcp.figma.com/mcp" ^
  -H "Content-Type: application/json" ^
  -H "Accept: application/json, text/event-stream" ^
  -H "Authorization: Bearer YOUR_TOKEN_HERE" ^
  --data-binary "@init.json"
```

- **未带 Token**：应得 **`401 Unauthorized`**，且 `www-authenticate` 含 OAuth 信息 → 说明端点可达，MCP 服务正常。  
- **带有效 Token**：`200`，响应头里常有 **`mcp-session-id`**（名称以实际响应为准），body 为 SSE 或 JSON。

从 `headers.txt` 取出 session id（示例名：`mcp-session-id`）：

```bash
# PowerShell 示例
$session = (Select-String -Path headers.txt -Pattern "mcp-session-id").Line.Split(":")[1].Trim()
```

**Step 2 — notifications/initialized**

```bash
curl.exe -sS -X POST "https://mcp.figma.com/mcp" ^
  -H "Content-Type: application/json" ^
  -H "Accept: application/json, text/event-stream" ^
  -H "Authorization: Bearer YOUR_TOKEN_HERE" ^
  -H "mcp-session-id: %SESSION%" ^
  --data-binary "@initialized.json"
```

**Step 3 — tools/call whoami（豁免读限额，最适合验连通）**

```bash
curl.exe -sS -X POST "https://mcp.figma.com/mcp" ^
  -H "Content-Type: application/json" ^
  -H "Accept: application/json, text/event-stream" ^
  -H "Authorization: Bearer YOUR_TOKEN_HERE" ^
  -H "mcp-session-id: %SESSION%" ^
  --data-binary "@whoami.json"
```

成功时 body 里应能看到你的 Figma 邮箱与 `plans` / `seat` / `tier`。

**Step 4 — 可选：读帧 metadata（占读配额，易触发限速）**

`get_metadata.json`：

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "get_metadata",
    "arguments": {
      "fileKey": "GetdOs1IPlJcW5mdrKhVH3",
      "nodeId": "0:1"
    }
  }
}
```

```bash
curl.exe -sS -X POST "https://mcp.figma.com/mcp" ^
  -H "Content-Type: application/json" ^
  -H "Accept: application/json, text/event-stream" ^
  -H "Authorization: Bearer YOUR_TOKEN_HERE" ^
  -H "mcp-session-id: %SESSION%" ^
  --data-binary "@get_metadata.json"
```

若被限速，响应头可能包含：`Retry-After`、`X-Figma-Plan-Tier`、`X-Figma-Rate-Limit-Type`、`X-Figma-Upgrade-Link`。

---

### 3.3 桌面本地 MCP（无需 Bearer，推荐你先测这个）

1. 打开 **Figma 桌面版** → 打开任意 Design 文件 → **Dev Mode (Shift+D)**。  
2. Inspect 面板 → **Enable desktop MCP server**。  
3. 确认本地地址：`http://127.0.0.1:3845/mcp`。

```bash
curl.exe -sS -D headers.txt -o body.txt -X POST "http://127.0.0.1:3845/mcp" ^
  -H "Content-Type: application/json" ^
  -H "Accept: application/json, text/event-stream" ^
  --data-binary "@init.json"
```

连接失败 `Could not connect` → 桌面 MCP 未开启或端口不是 3845。

后续 `initialized` / `tools/call` 与远程相同，仅把 URL 换成 `http://127.0.0.1:3845/mcp`，一般**不需要** `Authorization`。

---

## 4. 带 5 秒重试的 PowerShell 片段（whoami）

将 `YOUR_TOKEN_HERE` 换成真实 token，或改用桌面 URL。

```powershell
$base = "https://mcp.figma.com/mcp"   # 桌面: "http://127.0.0.1:3845/mcp"
$headers = @{
  "Content-Type" = "application/json"
  "Accept"       = "application/json, text/event-stream"
  # "Authorization" = "Bearer YOUR_TOKEN_HERE"
}
$initBody = @{
  jsonrpc = "2.0"; id = 1; method = "initialize"
  params = @{
    protocolVersion = "2024-11-05"
    capabilities    = @{}
    clientInfo      = @{ name = "ps-demo"; version = "1.0" }
  }
} | ConvertTo-Json -Depth 5

$max = 3
for ($i = 1; $i -le $max; $i++) {
  try {
    $r = Invoke-WebRequest -Uri $base -Method POST -Headers $headers -Body $initBody -UseBasicParsing
    Write-Host "OK" $r.StatusCode
    $r.Headers["mcp-session-id"]
    break
  } catch {
    Write-Host "Attempt $i failed:" $_.Exception.Message
    if ($i -lt $max) { Start-Sleep -Seconds 5 }
  }
}
```

---

## 5. 在 Cursor 里最快验证「是否生效」

不必 cURL，在 Agent 里发一句：

```text
请只调用一次 Figma MCP 的 whoami，把返回的 email 和 plans 原样贴给我。
```

若 whoami 成功而 `get_metadata` 失败 → MCP 连通正常，多半是**读配额/每分钟限速**；按第 1 节处理。

---

## 6. 与本项目相关的 fileKey

| 用途 | fileKey |
|------|---------|
| 阶段一主文件 | `GetdOs1IPlJcW5mdrKhVH3` |
| 旧免费账号初版 | `6ajDseXpLEBRGu12Ta4BRM`（节点 `1:2` 为完整 Agent 屏） |

---

## 7. 仓库内自动化脚本

`scripts/figma_mcp_retry_demo.py`：对 **whoami** 做最多 3 次、间隔 5s 的请求（需设置环境变量 `FIGMA_MCP_TOKEN`，或改 `BASE_URL` 为桌面 MCP）。

---

## 8. Agent 报错交付约定（用户要求）

凡 Figma MCP 在 Cursor Agent 中失败，**同条回复内**须给出可复制 **cURL**（Windows 用 `curl.exe`），便于用户手动复现。至少包含：

1. **失败工具名**与**原始报错全文**
2. **推荐路径**：桌面 MCP `http://127.0.0.1:3845/mcp`（开 Dev Mode → Enable desktop MCP，**无需 Bearer**）
3. **远程路径**（需 Bearer）：`https://mcp.figma.com/mcp` + 本节 §3 JSON body
4. 与本项目相关的 `fileKey`：`GetdOs1IPlJcW5mdrKhVH3`（阶段一）

### 8.1 一键模板：whoami（不占读配额）

在任意目录保存 `whoami.json`（内容见 §3.1），然后：

```powershell
# 桌面 MCP（推荐）
$BASE = "http://127.0.0.1:3845/mcp"
curl.exe -sS -D headers.txt -o body-init.txt -X POST $BASE `
  -H "Content-Type: application/json" `
  -H "Accept: application/json, text/event-stream" `
  --data-binary "@init.json"
$session = (Select-String -Path headers.txt -Pattern "mcp-session-id").Line.Split(":",2)[1].Trim()
curl.exe -sS -X POST $BASE `
  -H "Content-Type: application/json" `
  -H "Accept: application/json, text/event-stream" `
  -H "mcp-session-id: $session" `
  --data-binary "@initialized.json"
curl.exe -sS -X POST $BASE `
  -H "Content-Type: application/json" `
  -H "Accept: application/json, text/event-stream" `
  -H "mcp-session-id: $session" `
  --data-binary "@whoami.json"
```

远程时在三段 `curl.exe` 均加：`-H "Authorization: Bearer YOUR_TOKEN_HERE"`，URL 改为 `https://mcp.figma.com/mcp`。

### 8.2 一键模板：get_metadata（占读配额，易触发限额）

`get_metadata.json` 见 §3.2 Step 4；`fileKey` 用 `GetdOs1IPlJcW5mdrKhVH3`，`nodeId` 可省略（列 pages）或 `0:1`。

```powershell
# 在已有 $session 后（同上 init → initialized）
curl.exe -sS -D headers-meta.txt -o body-meta.txt -X POST $BASE `
  -H "Content-Type: application/json" `
  -H "Accept: application/json, text/event-stream" `
  -H "mcp-session-id: $session" `
  --data-binary "@get_metadata.json"
Get-Content headers-meta.txt | Select-String -Pattern "Retry-After|X-Figma"
Get-Content body-meta.txt
```

### 8.3 use_figma（写画布）

cURL 的 `tools/call` 参数为 `name: "use_figma"`，`arguments: { fileKey, code, description }`。body 较大，建议用 `@use_figma.json` 文件；**View 席位**或文件无 Edit 时会失败 — 与读限额无关时需查 Figma 分享权限。
