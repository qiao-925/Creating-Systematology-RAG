# Codex 与 Claude Code 实践拆解

## 1. 文档目标

这份文档不比较 `Codex` 和 `Claude Code` 谁更强，而是回答四个更重要的问题：

1. 它们到底是不是 Agent
2. 它们和 Agent 框架、工具、模型分别是什么关系
3. 它们公开了哪些实现信息，哪些没有公开
4. 对学习 Agent 开发的人来说，应该从它们身上学什么

本文刻意把信息分成三层：

- `已确认事实`：来自官方产品页、官方文档、官方 GitHub、官方工程文章
- `高可信推断`：官方没有逐条明说，但从公开资料中可以稳定推断
- `未证实猜测`：社区分析、逆向、二手总结，不能直接当定论

这样做的目的，是避免把“合理猜测”误当成“已经确认的架构事实”。

## 2. 先把几个概念分开

理解 `Codex` 和 `Claude Code`，首先不要把下面四类东西混在一起。

### 2.1 模型

模型负责推理、生成、规划建议和工具调用意图。

例如：

- `Claude Code` 官方公开支持 `Opus 4.6`、`Sonnet 4.6`、`Haiku 4.5`
- `Codex` 官方公开有 `codex-1`、`GPT-5-Codex` 这类面向软件工程优化的模型

模型本身不是完整 Agent。

### 2.2 工具

工具负责让系统具备行动能力，例如：

- 读写文件
- 搜索代码
- 运行 Shell
- 调 Git
- 访问 MCP server
- 调第三方 API

工具也不是 Agent。工具更像 Agent 的手。

### 2.3 Agent 框架

Agent 框架负责帮你把“模型 + 工具 + 状态 + 多步执行”组织起来。

它通常提供：

- 消息流组织
- 工具注册
- 状态管理
- 结构化输出
- 多 Agent 编排
- 记忆或 tracing 支持

框架是“造 Agent 的脚手架”，不是已经交付好的 Agent 产品。

### 2.4 Agent 产品

`Codex` 和 `Claude Code` 处在这一层。

它们不是“只有一个模型接口”，也不是“几个工具的集合”，而是把这些能力产品化了：

- 模型能力
- 工具能力
- agent loop
- 权限控制
- 上下文管理
- 执行与恢复
- CLI / IDE / Web 等入口

所以更准确地说：

- `Codex` / `Claude Code` 是产品化的 coding agent
- 它们暴露的文件操作、Shell、MCP 等是 Agent 的工具层

## 3. 已确认事实

这一部分只放官方明确公开的信息。

### 3.1 Claude Code 是什么

Anthropic 官方文档把 Claude Code 明确定义为 `agentic coding tool`，并说明它：

- 读取代码库
- 编辑文件
- 运行命令
- 集成开发工具
- 可在终端、IDE、桌面应用和浏览器中使用

官方文档还明确说明：

- Claude Code 可以通过 `MCP` 连接外部数据源和工具
- `CLAUDE.md` 是项目级指令文件，Claude Code 会在会话开始时读取
- Claude Code 还会构建 `auto memory`
- 可以运行多个 Claude Code agents 协同工作
- 官方提供 `Agent SDK`，允许开发者基于 Claude Code 的工具与能力构建自己的 agent

这说明 Claude Code 不只是“会回答问题的模型前端”，而是已经具备多步执行、工具访问和工作流能力的 Agent 产品。

### 3.2 Claude Code 公开了哪些实现信息

官方产品页明确写到：

- Claude Code 运行在你的终端中
- 它直接和模型 API 通信
- 不依赖后端服务器或远程代码索引
- 在修改文件或运行命令前会请求权限
- 支持的模型包括 `Opus 4.6`、`Sonnet 4.6`、`Haiku 4.5`
- 企业用户可以通过 `Amazon Bedrock` 或 `Google Cloud Vertex AI` 使用 Claude Code

官方 GitHub 仓库也是公开的，仓库主页明确说明 Claude Code 是一个运行在终端中的 `agentic coding tool`。GitHub 页面当前显示该仓库的主要语言构成为：

- `Shell 47.0%`
- `Python 29.3%`
- `TypeScript 17.7%`
- 另有少量 `PowerShell`、`Dockerfile`

这里要注意：GitHub 语言占比只能说明“公开仓库里哪些语言较多”，不能反推出完整商业系统就只有这些语言。

### 3.3 Codex 是什么

OpenAI 官方把 Codex 描述为：

- `AI coding partner`
- `cloud-based software engineering agent`
- 可以并行处理多个任务
- 每个任务运行在独立的云沙箱环境中

OpenAI 还明确说明，Codex 不只是一个单独产品，而是一套软件代理能力集合，至少包括：

- `Codex CLI`
- `Codex Cloud`
- `Codex VS Code extension`

OpenAI 官方工程文章也明确写到，Codex 的核心是 `agent loop`，负责协调：

- 用户输入
- 模型推理
- 工具调用

这等于直接公开承认：Codex 的核心不是简单问答，而是一个持续执行的软件代理循环。

### 3.4 Codex 公开了哪些实现信息

OpenAI 官方目前明确公开了这些点：

- `Codex CLI` 是开源的
- `Codex CLI` 可以本地在终端运行
- 它可以读取、修改并运行当前目录里的代码
- `Codex CLI` 是用 `Rust` 构建的
- OpenAI 发布过专门的工程文章解释 `Codex agent loop`
- 该文章明确说明 `Codex CLI` 通过 `Responses API` 驱动 agent loop
- `Responses API endpoint` 是可配置的
- Codex 使用结构化工具定义参与模型调用
- OpenAI 公开了 `Codex SDK`
- 官方说明 `Codex SDK` 可以把“驱动 Codex CLI 的同一个 Agent”嵌入自己的工作流、工具和应用中

OpenAI 官方 GitHub 页面当前显示 `openai/codex` 仓库的主要语言构成为：

- `Rust 95.2%`
- `Python 2.2%`
- `TypeScript 1.6%`
- 另有少量 `JavaScript`、`Starlark`、`PowerShell`

同样，这只说明公开仓库的语言构成，不等于整个商业化 Codex 产品的全部技术栈。

### 3.5 两者都明确属于 Agent，而不是单纯工具集合

从官方表述看，两者都不只是“工具盒子”。

因为它们都公开强调了以下特征：

- 能理解整个代码库
- 能跨多个文件工作
- 能调用外部工具
- 能执行多步任务
- 有明确的权限控制
- 有多个产品入口
- 有持续的 agent loop 或等价执行循环

所以合理结论是：

- 它们都是 Agent 产品
- 它们暴露出来的 `shell`、文件读写、MCP 等是工具层，不是 Agent 本身

## 4. 高可信推断

这一部分不是官方逐条明说，但从公开资料中可以稳定推断。

### 4.1 它们背后都存在完整的 Agent Runtime

虽然两家都没有完全公开所有内部实现，但从产品行为和公开文档看，二者背后都不只是“模型 + function calling”。

更可信的结构应该是：

- 输入层：CLI / IDE / Web / Slack 等入口
- 运行时层：agent loop / orchestration
- 工具层：文件、Shell、Git、MCP、外部 API
- 状态层：会话、上下文、工作目录、权限状态
- 结果层：消息输出、diff、提交、PR、日志、恢复

也就是说，它们都已经具备产品级 agent runtime，只是完整源码和内部策略没有完全公开。

### 4.2 真正的差距通常不在“会不会调工具”，而在工程化

很多人自己做一个 Agent Demo，也能实现：

- 读取文件
- 调用工具
- 写代码
- 跑测试

但体验通常和 `Codex`、`Claude Code` 差很多。高可信原因不是“它们有某个神秘框架”，而是它们在这些工程环节上做得更完整：

- 上下文组织
- 权限控制
- 长任务管理
- 错误恢复
- 工具协议稳定性
- 多入口一致性
- 用户交互设计
- 持续评估和调优

这也是产品级 Agent 和“会跑的 demo”之间最真实的差距。

### 4.3 它们一定有上下文压缩、状态推进与终止条件设计

OpenAI 已经公开讲了 Codex 的 `context window management` 和 `compaction`。Anthropic 虽然没有同样细致地公开 Claude Code 的内部做法，但从 Claude Code 支持长任务、多表面、多会话和 auto memory 的事实看，可以高可信地推断：

- Claude Code 也一定有自己的上下文管理策略
- 一定存在会话状态推进机制
- 一定存在任务终止和交还控制权的判定逻辑

否则产品很难稳定运行。

### 4.4 产品入口和核心 runtime 是分层的

Claude Code 已公开 terminal、IDE、desktop、web 等多个入口。Codex 也已公开 CLI、cloud、VS Code extension 等多个形态。

因此可以高可信推断：

- 它们的核心能力不是只写死在某个界面里
- 更可能是“共享核心 runtime + 多前端入口”

OpenAI 在 agent loop 文章里甚至直接把这种核心逻辑称为 `Codex harness`，这进一步支持这种推断。

## 5. 未证实猜测

下面这些内容，如果没有官方出处，就不能写成稳定事实。

### 5.1 关于 Claude Code 的具体前端/CLI 技术栈

例如下面这类说法，如果只是来自社区逆向或二手文章，就只能暂时归入“未证实”：

- Claude Code 一定使用 `Bun`
- Claude Code 一定使用 `CommanderJS`
- Claude Code 一定使用 `React Ink`
- Claude Code 会话一定实时以 `JSONL` 持久化
- 它的自动压缩一定按某种特定格式实现

这些说法可能对，也可能部分对，但如果官方没有直接确认，就不能当定论。

### 5.2 关于 Codex 的某些商业架构细节

下面这类内容也要谨慎：

- Codex 的完整后端服务拓扑
- 云端任务的完整调度实现
- 全量权限匹配规则
- 完整系统 prompt
- 完整评估体系
- 全部内部恢复策略

OpenAI 虽然比很多厂商更愿意公开 agent loop，但并没有把商业系统全部公开。

### 5.3 不要把“支持某云平台”混成同一家的事实

一个常见混淆是：

- Claude Code 官方明确提到了 `Amazon Bedrock` 和 `Google Vertex AI`
- 这并不等于 Codex 也公开支持同样路径

如果没有 OpenAI 官方明确声明，就不能把 Anthropic 公开的能力迁移成 Codex 的事实。

这是整理资料时最容易出现的错误之一。

## 6. 对学习 Agent 开发最有价值的启发

从学习角度，`Codex` 和 `Claude Code` 最值得学的，不是某个具体技术栈名称，而是它们体现出来的产品化 Agent 实践。

### 6.1 Agent loop 才是灵魂，不是单次问答

这类工具最核心的特征不是“回答得像人”，而是：

- 接收目标
- 形成执行意图
- 调用工具
- 观察结果
- 决定下一步
- 直到任务结束

只要你把这一点抓住，就不会把 Agent 学成“更复杂的 prompt 工程”。

### 6.2 工具不等于 Agent，工具编排才接近 Agent

很多初学者会误以为：

- 有 function calling
- 能调 shell
- 能读写文件

就已经做出了 Agent。

其实这还差得很远。真正的关键在于：

- 何时调用工具
- 失败后怎么办
- 如何避免误操作
- 如何管理上下文
- 如何判断任务完成

这才是 Agent 的核心工程问题。

### 6.3 产品级 Agent 的重点在“稳定完成任务”

从这两个工具可以明显看出，产品级 Agent 的目标不是“偶尔惊艳一次”，而是“在真实工程环境里稳定完成一类任务”。

所以真正值得学的能力包括：

- 权限系统
- 沙箱边界
- 上下文裁剪
- 长任务恢复
- 多入口一致性
- 结果验证
- 可观测性

### 6.4 不要先纠结框架名，先学运行时思维

你在书里看到的很多 Agent 框架都很有用，但它们更像“积木”。真正应该优先建立的是 runtime 视角：

- 用户目标如何进入系统
- 状态如何推进
- 工具如何被调用
- 错误如何恢复
- 结果如何交付

一旦这条主线清楚了，再看框架就不会迷失在 API 细节里。

## 7. 对你当前学习路径的具体建议

如果你正在边看书边理解 Agent，建议把这两个工具当作“产品化样本”，而不是“神秘黑箱”。

推荐学习顺序：

1. 先观察它们的行为
2. 再把行为映射成模块
3. 然后自己做最小单 Agent
4. 最后回头看书里的框架与模式

观察时重点问自己这些问题：

- 它什么时候先读环境
- 它什么时候先规划
- 它什么时候直接执行
- 它什么时候请求权限
- 它什么时候调用工具
- 它什么时候停止并把控制权交回给用户

如果你能回答这些问题，你就已经开始从“会用产品”走向“理解 Agent 系统”了。

## 8. 一句话结论

`Codex` 和 `Claude Code` 不是“几个工具 + 一个模型”的简单拼装，而是已经产品化的 coding agent。

它们公开了不少重要信息，足够你学习很多工程实践；但它们并没有把完整内部实现全部公开，因此最正确的学习方式不是猜它们“具体用了哪个框架”，而是提炼它们在 `agent loop`、工具、权限、上下文管理、恢复和产品化上的通用方法。

## 9. 官方来源

- Claude Code 概览：https://code.claude.com/docs/en/overview
- Claude Code 产品页：https://claude.com/product/claude-code
- Claude Code GitHub：https://github.com/anthropics/claude-code
- Codex 产品页：https://openai.com/codex/
- Introducing Codex：https://openai.com/index/introducing-codex/
- Codex GA：https://openai.com/index/codex-now-generally-available/
- Codex CLI 文档：https://developers.openai.com/codex/cli
- Codex GitHub：https://github.com/openai/codex
- Unrolling the Codex agent loop：https://openai.com/index/unrolling-the-codex-agent-loop/
