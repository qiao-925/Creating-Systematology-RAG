# Claude Code Plugins 全量清单

> 来源：`claude-plugins-official` marketplace（GitHub: anthropics/claude-plugins-official）
> 生成时间：2026-05-26
> 总计：**203 个插件**

**导航**：[项目依赖清单](dependency-list.md) | [约束体系](constraint-system.md) | [决策日志](decision-log.md) | [文档索引](README.md)

## 统计概览

| 类别 | 数量 |
|------|------|
| development | 92 |
| productivity | 39 |
| database | 20 |
| security | 12 |
| monitoring | 10 |
| deployment | 5 |
| design | 5 |
| uncategorized | 14 |
| learning | 2 |
| location | 2 |
| testing | 1 |
| math | 1 |

## 当前已安装

| 插件 | 版本 | 启用 |
|------|------|------|
| figma | v2.2.12 | ✅ |
| frontend-design | v1b527e2ee74e | ✅ |

## 项目依赖上下文

> 完整依赖清单见 [dependency-list.md](dependency-list.md)

本项目技术栈：**Next.js + FastAPI + Python + Tailwind/shadcn**

### 插件 ↔ 依赖映射

| 项目层 | 核心依赖 | 对应插件/MCP | 作用 |
|--------|---------|-------------|------|
| LLM 编排 | llama-index, litellm, openai | context7 (MCP) | 文档查询加速 |
| Embedding | sentence-transformers, huggingface-hub | context7 (MCP) | 模型文档参考 |
| 向量存储 | chromadb | — | 无专用插件 |
| Web 框架 | FastAPI, uvicorn | — | 无专用插件 |
| 前端框架 | Next.js, React, Tailwind | frontend-design, context7 | UI 生成 + 文档查询 |
| UI 组件 | shadcn, lucide-react, zustand | frontend-design | 组件生成 |
| 设计协作 | — | figma | 设计稿读写同步 |
| E2E 测试 | — | playwright (MCP) | 浏览器自动化测试 |

### 当前 MCP Servers

| Server | 用途 | 配置位置 |
|--------|------|---------|
| context7 | 实时文档查询 | `.mcp.json` |
| figma | 设计稿读写 | Claude Code settings |
| playwright | 浏览器自动化 | Claude Code settings |

### 工具链依赖（非 npm/pip）

| 工具 | 用途 | 必需 |
|------|------|------|
| uv | Python 依赖解析和环境同步 | ✅ |
| npm | 前端依赖安装 | ✅ |
| gh | GitHub CLI + 环境同步 | ✅ |
| make | 本地编排 | ✅ |
| Docker | 容器化部署 | 按需 |

---

## 分类详细清单

### Design（5 个）

| 插件 | 描述 | 作者 |
|------|------|------|
| adobe-for-creativity | Adobe 创意 AI 工具：图片编辑、设计工作流自动化、矢量化、专业修图 | Adobe |
| figma | Figma 设计平台集成：读取设计文件、提取组件、解析 design tokens、设计转代码 | Anthropic |
| hyperframes | HeyGen HyperFrames：HTML 转视频、GSAP 动画、字幕、配音 | HeyGen |
| miro | Miro 白板安全访问：读取 board context、创建图表、生成代码 | Miro |
| runway-api | Runway API 视频生成：批量广告、产品视频、营销素材 | Runway |

### Development（92 个）

#### Anthropic 官方

| 插件 | 描述 |
|------|------|
| agent-sdk-dev | Claude Agent SDK 开发工具包 |
| clangd-lsp | C/C++ 语言服务器（clangd） |
| code-modernization | 遗留代码现代化（COBOL、旧 Java/C++、单体 Web 应用） |
| csharp-lsp | C# 语言服务器 |
| feature-dev | 功能开发工作流：代码库探索、架构设计、快速验证 |
| gopls-lsp | Go 语言服务器 |
| jdtls-lsp | Java 语言服务器（Eclipse JDT.LS） |
| kotlin-lsp | Kotlin 语言服务器 |
| lua-lsp | Lua 语言服务器 |
| mcp-server-dev | MCP Server 开发技能 |
| mcp-tunnels | 通过 Anthropic MCP tunnel 连接私有 MCP Server |
| php-lsp | PHP 语言服务器（Intelephense） |
| playground | 创建交互式 HTML playground |
| plugin-dev | Claude Code 插件开发工具包（7 个专家技能） |
| pyright-lsp | Python 语言服务器（Pyright） |
| ralph-loop | 交互式自引用 AI 循环，迭代开发 |
| ruby-lsp | Ruby 语言服务器 |
| rust-analyzer-lsp | Rust 语言服务器 |
| skill-creator | 创建和优化 skill |
| swift-lsp | Swift 语言服务器（SourceKit-LSP） |
| typescript-lsp | TypeScript/JavaScript 语言服务器 |

#### 云平台 / DevOps

| 插件 | 描述 | 来源 |
|------|------|------|
| aws-agents | AWS Bedrock AgentCore agent 构建 | AWS |
| aws-amplify | AWS Amplify Gen 2 全栈应用 | AWS |
| aws-core | AWS 基础服务和 IaC | AWS |
| aws-data-analytics | S3 Tables、Glue、Athena 数据分析 | AWS |
| aws-dev-toolkit | 34 skills + 11 agents + 3 MCP servers | AWS |
| aws-serverless | 无服务器应用设计、构建、调试 | AWS |
| azure | Azure MCP + 50+ 服务专家技能 | Microsoft |
| cloudflare | Workers、Durable Objects、Agents SDK | Cloudflare |
| deploy-on-aws | AWS 部署 + 架构推荐 + 成本估算 | AWS |
| railway | Railway 部署和管理 | Railway |
| vercel | Vercel 部署平台集成 | Vercel |

#### 前端 / 移动

| 插件 | 描述 |
|------|------|
| appwrite | Appwrite SDK + MCP + 部署命令 |
| expo | React Native + Expo 开发 |
| frontend-design | 高质量前端界面生成 |
| laravel-boost | Laravel 开发工具包 |
| liquid-lsp | Shopify Liquid 模板语言服务器 |
| liquid-skills | Liquid 语言基础、CSS/JS/HTML 编码标准 |
| netlify-skills | Netlify 平台技能 |
| sanity | Sanity 内容平台集成 |
| shopify | Shopify 开发工具（GraphQL、Liquid、UI extensions） |
| shopify-ai-toolkit | Shopify AI 工具包（18 个技能） |
| ui5 | SAPUI5 / OpenUI5 开发 |
| wix | Wix 站点和应用构建 |
| wordpress.com | WordPress 站点创建和编辑 |

#### AI / ML

| 插件 | 描述 |
|------|------|
| atomic-agents | Atomic Agents 框架 agent 开发 |
| datarobot-agent-skills | DataRobot AI/ML 工作流 |
| huggingface-skills | HuggingFace 模型训练、评估、部署 |
| pydantic-ai | Pydantic AI 代码模式 |
| togetherai-skills | Together AI 平台技能 |
| snowflake-cortex-code | Snowflake Cortex Code 路由 |

#### API / 支付

| 插件 | 描述 |
|------|------|
| apollo-skills | Apollo GraphQL 全栈技能 |
| circle-skills | USDC 支付、跨链、智能合约 |
| mercadopago | Mercado Pago 全产品集成 |
| postman | API 全生命周期管理 |
| rc / revenuecat | RevenueCat 应用内购买 |
| stripe | Stripe 支付集成 |
| sumup | SumUp 支付终端和在线结账 |
| twilio-developer-kit | Twilio 通信 API |
| zoom-plugin | Zoom 集成开发 |

#### 搜索 / 数据获取

| 插件 | 描述 |
|------|------|
| brightdata-plugin | 网页抓取、Google 搜索、结构化数据提取 |
| exa | Exa AI 网页搜索和深度研究 |
| firecrawl | 网页抓取和爬取，转为 LLM-ready markdown |
| greptile | AI 代码库搜索和理解 |
| lumen | 本地语义代码搜索（Go AST + Ollama） |
| nimble | 网页数据工具包 |
| sourcegraph | 跨仓库代码搜索和理解 |

#### 其他开发

| 插件 | 描述 |
|------|------|
| agentforce-adlc | Salesforce Agentforce agent 开发生命周期 |
| base44 | Base44 全栈应用 |
| buildkite | Buildkite CI/CD 技能 |
| cds-mcp / sap-cds-mcp | SAP CAP 项目开发 |
| chrome-devtools-mcp | Chrome DevTools 控制和检查 |
| codspeed | 性能测试工具包 |
| convex-backend | Convex 响应式后端 |
| dominodatalab | Domino Data Lab 平台 |
| fastly-agent-toolkit | Fastly 开发工具 |
| forge-skills | Atlassian Forge 开发 |
| mcp-apps | MCP Apps SDK 技能 |
| microsoft-docs | Microsoft 文档访问 |
| mintlify | 文档站点构建 |
| netsuite-suitecloud | NetSuite SuiteCloud 开发 |
| oracle-ai-data-platform | Oracle 数据平台 Spark 连接器 |
| outputai | 工作流开发工具包（5 个专家 agent） |
| qt-development-skills | Qt C++/QML 开发技能 |
| quarkus-agent | Quarkus 应用管理 |
| sap-fiori-mcp-server | SAP Fiori 开发 |
| sap-mdk-server | SAP MDK 移动开发 |
| servicenow-sdk | ServiceNow 应用开发 |
| teamcity-cli | TeamCity CI/CD 集成 |
| terraform | Terraform 生态集成 |

---

### Productivity（39 个）

| 插件 | 描述 | 类型 |
|------|------|------|
| airtable | Airtable 数据库和操作层 | 数据协作 |
| apollo | Apollo.io 销售线索和外联 | 销售 |
| asana | Asana 项目管理 | 项目管理 |
| atlassian | Jira + Confluence 集成 | 项目管理 |
| box | Box 文件管理和协作 | 文件管理 |
| carta-cap-table / crm / investors | Carta 投资者关系管理 | 金融 |
| circleback | 会议、邮件、日历上下文搜索 | 日程 |
| claude-code-setup | 分析代码库并推荐 Claude Code 自动化 | 效率 |
| claude-md-management | CLAUDE.md 维护和审计 | 效率 |
| code-review | 自动化 PR 代码审查 | 代码质量 |
| code-simplifier | 代码简化和重构 | 代码质量 |
| coderabbit | 外部 AI 代码审查（40+ 静态分析器） | 代码质量 |
| commit-commands | git commit/push/PR 工作流 | Git |
| cwc-makers | Code-with-Claude Makers 硬件入门 | 硬件 |
| desktop-commander | 终端命令、进程管理、文件操作 | 系统 |
| discord | Discord 消息桥接 | 通讯 |
| github | GitHub MCP Server | 代码托管 |
| gitlab | GitLab DevOps 集成 | 代码托管 |
| hookify | 自定义 hook 创建 | 效率 |
| hunter | 专业邮箱查找和验证 | 销售 |
| imessage | iMessage 消息桥接 | 通讯 |
| intercom | Intercom 客户支持集成 | 客服 |
| legalzoom | 法律文档审查和指导 | 法律 |
| linear | Linear issue tracking | 项目管理 |
| notion | Notion 工作区集成 | 知识管理 |
| pigment | 业务数据分析和建模 | BI |
| pr-review-toolkit | 综合 PR 审查 agent | 代码质量 |
| save-to-spotify | TTS 音频 + Spotify 保存 | 媒体 |
| session-report | 会话使用报告生成 | 监控 |
| slack | Slack 工作区集成 | 通讯 |
| spotify-ads-api | Spotify 广告管理 | 广告 |
| telegram | Telegram 消息桥接 | 通讯 |
| windsor-ai | 325+ 业务数据源连接 | 数据集成 |
| youdotcom-agent-skills | You.com 搜索和研究 | 搜索 |
| zapier | 8000+ 应用连接 | 自动化 |
| zoominfo | 公司和联系人搜索 | 销售 |

---

### Database（20 个）

| 插件 | 描述 |
|------|------|
| alloydb | Google AlloyDB for PostgreSQL |
| azure-cosmos-db-assistant | Azure Cosmos DB 专家助手 |
| bigdata-com | 金融研究和分析（RavenPack） |
| clickhouse | ClickHouse Cloud 数据库连接 |
| clickhouse-best-practices | ClickHouse 最佳实践（28 条规则） |
| cloud-sql-postgresql | Google Cloud SQL for PostgreSQL |
| cockroachdb | CockroachDB 集群管理（14 tools + 32 skills） |
| databases-on-aws | AWS 数据库组合专家指导 |
| datahub-skills | DataHub 数据目录和治理 |
| dataverse | Microsoft Dataverse |
| duckdb-skills | DuckDB 数据分析 |
| firebase | Google Firebase（Firestore、Auth、Functions） |
| mongodb | MongoDB MCP + Skills |
| neon | Neon PostgreSQL serverless |
| pinecone | Pinecone 向量数据库 |
| planetscale | PlanetScale MySQL |
| qdrant-skills | Qdrant 向量搜索 |
| redis-development | Redis 开发最佳实践 |
| supabase | Supabase 数据库 + Auth + 存储 |
| zilliz | Zilliz Cloud 向量数据库管理 |

---

### Security（12 个）

| 插件 | 描述 |
|------|------|
| 42crunch-api-security-testing | OpenAPI 安全审计（OWASP） |
| auth0 | Auth0 认证集成 |
| crowdstrike-falcon-foundry | CrowdStrike 安全平台开发 |
| duende-skills | OAuth/OIDC、IdentityServer 技能 |
| jfrog | JFrog 制品仓库和安全扫描 |
| security-guidance | 安全提醒 hook（XSS、注入等） |
| semgrep | Semgrep 实时安全漏洞检测 |
| sonarqube | SonarQube 代码质量和安全（7000+ 规则） |
| sonatype-guide | 软件供应链安全 |
| vanta-mcp-plugin | Vanta 安全合规平台 |
| workos | WorkOS AuthKit、SSO、RBAC |
| zscaler | Zscaler 云安全平台 |

---

### Monitoring（10 个）

| 插件 | 描述 |
|------|------|
| amplitude | Amplitude 产品分析 |
| dash0 | OpenTelemetry 可观测性 |
| datadog | Datadog 日志/指标/追踪 |
| fullstory | FullStory 行为分析和会话回放 |
| logfire | Python 应用 Logfire 可观测性 |
| pagerduty | PagerDuty 风险评分和事件关联 |
| posthog | PostHog 分析、Feature Flags、实验 |
| rootly | 事件管理全生命周期 |
| sentry | Sentry 错误监控 |
| sentry-cli | Sentry CLI 技能 |

---

### 其他类别

#### Deployment（5 个）
azure, cloudflare, deploy-on-aws, railway, vercel

#### Learning（2 个）
explanatory-output-style, learning-output-style

#### Location（2 个）
amazon-location-service, mapbox

#### Testing（1 个）
playwright

#### Math（1 个）
math-olympiad

#### Uncategorized（14 个）
ai-plugins, aikido, atlan, brightdata-plugin, cloudinary, data-engineering, fastly-agent-toolkit, fiftyone, nightvision, nimble, postiz, prisma, remember, wordpress.com

---

## 与本项目相关的推荐插件

基于项目技术栈（Next.js + FastAPI + Python + Tailwind/shadcn）：

### 已安装 ✅
- **figma** — 设计稿读取和同步
- **frontend-design** — 高质量前端界面生成

### 强烈推荐安装
| 插件 | 理由 |
|------|------|
| context7 | 实时文档查询（React、Next.js、Tailwind 等） |
| playwright | E2E 测试 |
| code-review | 自动化 PR 审查 |
| security-guidance | 编辑文件时的安全提醒 |
| posthog | 产品分析和 Feature Flags |

### 按需安装
| 插件 | 场景 |
|------|------|
| sentry | 错误监控 |
| vercel | Vercel 部署 |
| notion | Notion 文档集成 |
| linear | Issue tracking |
| slack | 团队通讯 |
| datadog | 基础设施监控 |
| anthropic agent-sdk-dev | 构建 Claude agent |
| mcp-server-dev | 开发自定义 MCP server |
