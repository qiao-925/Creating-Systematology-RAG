# MCP 工具生态调研（2026-04-13）

> 来源：与 Cascade 对话调研，供 CLDFlow 项目工具层集成参考。

---

## Playwright MCP 原理

### 设计哲学

放弃截图→视觉识别→猜位置的传统路径，改用**语义结构树**让 LLM 理解页面。

### 三层核心技术

#### 1. AOM 树（Accessibility Object Model）

浏览器为屏幕阅读器维护的语义树，记录每个有意义元素的 `role`（button/link/textbox）、`name`（按钮文字）、`state`（disabled/checked）。

Playwright 通过 `page.accessibility.snapshot()` 直接读取，拿到结构化 JSON，不碰像素。

```json
{"role": "textbox", "name": "Username or email address"},
{"role": "button", "name": "Sign in"}
```

#### 2. 自定义序列化器 `snapshotter.ts`

- 原始 AOM JSON 太大，直接喂给 LLM 会撑爆 context
- 转为专为 LLM 优化的 YAML-like 格式，只保留 role/name/URL/状态等决策字段
- 给每个元素分配临时稳定 ID（`ref=e23`），LLM 后续操作直接引用，不需要 CSS selector 或 XPath

```yaml
generic [ref=e1]:
  link "Sign in" [ref=e4] [cursor=pointer]:
    /url: "/login"
  button "Submit" [ref=e42] [cursor=pointer]
```

#### 3. MCP 协议层：JSON-RPC over WebSocket/stdio

`npx @playwright/mcp` 启动 MCP Server，AI 客户端通过 JSON-RPC 调用标准工具：
`browser_snapshot`、`browser_click`、`browser_type`、`browser_navigate`。

Server 将工具调用翻译成 Playwright API（如 `getByRole('button', {name: 'Sign in'})`），执行后返回结果。

### 完整执行循环

```
LLM                    Playwright MCP Server          Browser
 |                           |                          |
 |-- browser_snapshot() ---> |                          |
 |                           |-- accessibility.snapshot() -->|
 |                           |<-- AOM JSON --------------- |
 |                           |-- snapshotter.ts 序列化 --|
 |<-- YAML ref树 ----------- |                          |
 |                           |                          |
 |（LLM推理：找 ref=e42 的按钮）                        |
 |                           |                          |
 |-- browser_click(ref=e42)->|                          |
 |                           |-- getByRole('button') --> |
 |                           |<-- 成功/失败 ------------ |
 |<-- 执行结果 -------------- |                          |
```

**关键优势**：`ref=eX` 比 XPath/CSS Selector 稳定，跟语义绑定而非 DOM 结构。

---

## 现象级 MCP 工具清单

### 浏览器自动化

| 工具 | 维护方 | 亮点 | 安装 |
|------|--------|------|------|
| **Playwright MCP** | Microsoft（官方） | AOM树+ref定位，真实浏览器，headless/headed均支持 | `npx -y @playwright/mcp` |

### 搜索类

| 工具 | 维护方 | 亮点 | 安装 |
|------|--------|------|------|
| **Exa MCP** | Exa | 2026年使用量最大；专为 Agent 设计，返回语义结构化 JSON；免费额度 | `EXA_API_KEY=... npx -y exa-mcp-server` |
| **Tavily MCP** | Tavily | research mode 自动多步搜索计划，长上下文优化，agent-first | `TAVILY_API_KEY=... npx -y tavily-mcp` |
| **Perplexity MCP** | 社区维护（成熟） | 返回带引用的综合答案，适合可溯源摘要场景 | `PERPLEXITY_API_KEY=... npx -y @modelcontextprotocol/server-perplexity` |
| **Brave Search MCP** | 官方 | 隐私优先，独立索引，支持图片/新闻搜索 | `BRAVE_API_KEY=... npx -y @modelcontextprotocol/server-brave-search` |

### 代码与版本控制

| 工具 | 维护方 | 亮点 | 安装 |
|------|--------|------|------|
| **GitHub MCP** | GitHub（官方） | PR/Issue/文件/提交全覆盖，OAuth scoped | `GITHUB_TOKEN=... npx -y @modelcontextprotocol/server-github` |
| **Git MCP** | 官方 | 本地 git 操作（log/diff/blame/commit），零配置 | `npx -y @modelcontextprotocol/server-git --repository /path` |
| **Filesystem MCP** | 官方 | 白名单目录读写，官方标准参考实现 | `npx -y @modelcontextprotocol/server-filesystem /path` |

### 工程协作

| 工具 | 维护方 | 亮点 | 安装 |
|------|--------|------|------|
| **Linear MCP** | Linear（官方） | Issue tracker 全 CRUD，工程团队标配，API 延迟极低 | `npx -y @modelcontextprotocol/server-linear` |
| **Notion MCP** | 官方 | 知识库查询+写入，OAuth，适合团队知识管理 | `npx -y @modelcontextprotocol/server-notion` |

### 基础设施

| 工具 | 维护方 | 亮点 | 安装 |
|------|--------|------|------|
| **AWS MCP** | 社区 | EC2/S3/IAM/CloudWatch 管理，面向云运维 Agent | 见各发行包 |
| **Docker MCP** | Docker | 容器管理，隔离执行安全 | 见 Docker 官方文档 |

---

## 对 CLDFlow 的集成建议

| MCP 工具 | 潜在用途 | 优先级 |
|----------|----------|--------|
| **Exa MCP** | Perspective Agent 的语义搜索工具，结构化 JSON 对 RAG pipeline 友好 | 高（Phase 2/3） |
| **Tavily MCP** | research mode 多步搜索，适合 Conductor 调度的深度调研 | 中 |
| **Playwright MCP** | 爬取需登录的数据源（FRED/World Bank 动态页面） | 低（Phase 3） |
| **GitHub MCP** | 已在用，Actions 监控 CI 状态 | 已在用 |
| **Filesystem MCP** | 白名单访问本地 data/ 目录 | 视需要 |

### 架构建议

Phase 2 设计 Perspective Agent 工具层时，**预留 MCP 接口插槽**（不锁定具体实现），优先考虑 Exa/Tavily 作为搜索工具，根据 API 成本最终决策。

---

*Updated: 2026-04-13 | 关联 Issue: #15*
