# Cascade Chat Conversation

  Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

分析一下agent workflow和skill的区别

### Planner Response

让我先看看相关的 workflow 和 skill 文件来理解当前架构。

*Listed directory [.workflows](file:///c:/Users/nonep/Desktop/typing-hub/.workflows) *

*Listed directory [workflows](file:///c:/Users/nonep/Desktop/typing-hub/.windsurf/workflows) *

*Viewed [structure-mobile-typing.md](file:///c:/Users/nonep/Desktop/typing-hub/.workflows/structure-mobile-typing.md) *

*Viewed [extract-ai-conversation-results.md](file:///c:/Users/nonep/Desktop/typing-hub/.workflows/extract-ai-conversation-results.md) *

*Viewed [archive-cleanup.md](file:///c:/Users/nonep/Desktop/typing-hub/.workflows/archive-cleanup.md) *

### Planner Response

现在我也来看看 skill 系统的内部结构，以便进行比较。

*Viewed [batch-discipline-protocol.md](file:///c:/Users/nonep/Desktop/typing-hub/.workflows/_shared/batch-discipline-protocol.md) *

*Viewed [daily-priority.md](file:///c:/Users/nonep/Desktop/typing-hub/.workflows/daily-priority.md) *

### Planner Response

# Agent Workflow vs Skill：区别分析

基于你项目中的实际 workflow 文件和 Cascade 内置的 skill 系统，核心区别如下：

## 本质定位

| 维度 | Workflow | Skill |
|---|---|---|
| **是什么** | 自然语言编写的**过程程序** | 内嵌的**能力单元/知识模块** |
| **回答的问题** | "按什么步骤做什么事" | "在某种场景下怎么判断/决策" |
| **类比** | 食谱（先切菜→再下锅→调味→出锅） | 厨师的刀工训练/味觉判断力 |
| **执行模式** | 线性/分支步骤流，Step 0→1→2→... | 被动注入上下文，影响推理方式 |

## 结构差异

**Workflow** — 你项目中的典型结构（如 `@c:\Users\nonep\Desktop\typing-hub\.workflows\structure-mobile-typing.md`）：
- YAML frontmatter（description + auto_execution_mode）
- 渐进式披露（主文件 + [_refs/](file:///c:/Users/nonep/Desktop/typing-hub/.workflows/_refs:0:0-0:0) + [_shared/](file:///c:/Users/nonep/Desktop/typing-hub/.workflows/_shared:0:0-0:0)）
- 压缩规则卡（≤30 行最小可执行子集）
- 明确的 Step 编号流程
- 批次纪律协议、SCAN 锚点、偏差检测
- 自反馈循环（运行时评估 + 事后自进化）

**Skill** — Cascade 内置的结构（如 `critical-thinking-evaluation`、`core-first-simplicity`）：
- 由 supporting files 定义
- 通过 `skill` 工具调用，注入上下文
- 不定义步骤序列，而是定义**判断规则和决策框架**
- 被动生效——agent 在相关场景中自动应用，而非按步骤执行

## 关键区别

### 1. 确定性 vs 灵活性

- **Workflow** 追求确定性：Step 编号、压缩规则卡、SCAN 锚点、偏差检测——所有这些机制都在对抗 agent 执行的不确定性。你项目的 `@c:\Users\nonep\Desktop\typing-hub\.workflows\_shared\batch-discipline-protocol.md` 就是典型的"用规则对抗注意力衰减"的设计。
- **Skill** 接受灵活性：它不规定"必须先做 A 再做 B"，而是说"遇到这类判断时，注意检查 X、Y、Z"。它增强 agent 的判断力，不约束执行路径。

### 2. 失控风险

- **Workflow** 有明确的失控风险——你之前的判断完全正确：**任务复杂、批次变长、上下文膨胀后会出现注意力衰减、规则偏移和执行失控**。压缩规则卡和 SCAN 锚点只能缓解，不改变其不确定性本质。
- **Skill** 几乎不存在失控风险——它不驱动长链路执行，只是在 agent 已有的推理过程中注入判断规则。它不会"跑偏"，因为没有一个"跑"的过程。

### 3. 适用场景

- **Workflow 适合**：有明确输入/输出、可枚举步骤、需要批量处理的任务（如你的 mobile-typing 结构化、AI 对话提取、archive 降噪）
- **Skill 适合**：需要判断力、决策质量、避免常见思维陷阱的场景（如批判性评估、架构治理、复杂度控制、优先级判断）

### 4. 演化方向

- **Workflow** 的自然演化终点是**硬编码脚本**——你的 `@c:\Users\nonep\Desktop\typing-hub\.workflows\structure-mobile-typing.md:327` 已经写了："当条目模板、分流规则、写法规则、输出位置、关键词提取规则都稳定后，再升级成命令/脚本"
- **Skill** 没有这个演化方向——判断力无法硬编码，它始终依赖语义理解

## 一句话总结

**Workflow 是"告诉 agent 怎么做"，Skill 是"让 agent 变得更会判断"。** 前者在简单任务上可靠，复杂时需要大量纪律机制对抗失控；后者不驱动执行，但提升执行中的决策质量。两者互补：Workflow 管流程，Skill 管判断。

### User Input

关于workflow的自然演化终点是硬编码脚本这件事情，除了我的这个，我的观点是这样，能找到目前与之契合的观点吗？我是觉得它workflow的自然语言workflow的确定性太差了，通过一部分硬编码能够增强它的确定性，但是又不会失去它过多的灵活性

*Searched web for natural language agent workflow determinism vs hardcoded scripts hybrid approach*

*Searched web for LLM agent workflow reliability hardcoding deterministic steps flexible judgment boundary*

*Read URL content from /blog/ai-agents-and-deterministic-workflows-a-spectrum *

*Read URL content from /demianbrecht/stop-asking-llms-to-be-deterministic-e32 *

*Read URL content from /blog/the-no-nonsense-approach-to-ai-agent-development *

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Read URL content from /agentforces-agent-graph-toward-guided-determinism-with-hybrid-reasoning/ *

*Read URL content from /blog/structured-ai-coding-workflow-deterministic-agentic-nodes *

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

### Planner Response

现在我再看看 Reddit 的讨论，以获取更实际的观点：

*Read URL content from /r/ExperiencedDevs/comments/1nqlm09/agentic_ai_vs_deterministic_workflows_with_llms/ *

### Planner Response

已有足够材料。以下是与你的观点契合的外部观点汇总：

---

# 你的观点 vs 行业共识

你的核心判断：**自然语言 workflow 确定性太差，通过部分硬编码增强确定性，但不过度失去灵活性**。这个观点在当前行业中有多个高度契合的声音。

## 1. Demian Brecht — "Stop Asking LLMs to Be Deterministic"

最直接契合你的观点。核心主张：

> **"LLMs should be used when judgment is actually required. Everything else should execute as code: microseconds instead of API calls, at zero marginal cost."**

他的方法论：**用代码包围混沌**（"surrounding chaos with code"）。具体做法是把 workflow 拆成节点，能确定性的全用代码，只在需要判断的地方调 LLM。他的案例：一个 ops review 流程 4 个节点，3 个纯代码（拉数据、统计计算、格式化报告），只有 1 个调 LLM（把统计结果解释为高管摘要）。

这和你的判断完全一致——**不是不用 LLM，而是把 LLM 从"执行者"收缩为"判断者"**。

## 2. Salesforce Agent Graph — "Guided Determinism"

Salesforce 工程团队提出的概念，和你说的"部分硬编码增强确定性"几乎同义：

> **"Orchestration as design-time configuration, not runtime improvisation."**

他们发现纯 prompt 驱动的 agent 在企业场景中会出现 **"goal drift"**（目标漂移）——和你的 workflow 中的"注意力衰减、规则偏移"是同一现象。他们的解法：**把业务流程建模为图（graph），节点的拓扑结构在设计时确定（硬编码），节点内部的推理交给 LLM（灵活）**。

关键原话：

> **"The hard truth: LLM reasoning alone cannot carry enterprise load."**
> **"The future isn't endless prompt refinement. It's structured, auditable workflows."**

他们的"doom-prompting"概念——不断调 prompt 祈祷一致性——就是你在做的压缩规则卡、SCAN 锚点等机制的困境本质。

## 3. Vercel — "No-Nonsense Approach"

Vercel 的方法论更工程化：

> **"Gather input, perform deterministic computation where possible, call the model when logic or judgment is needed, evaluate the result, and decide whether to continue."**

> **"Don't be afraid of plain old programming. Save the LLM for parts that truly need judgment."**

> **"Building AI agents might seem like a new thing that calls for new abstractions, but it is just regular programming. Use if statements, loops, or switches, whatever fits."**

这和你的 `@c:\Users\nonep\Desktop\typing-hub\.workflows\structure-mobile-typing.md:327` 里的"升级成命令/脚本"方向完全一致。

## 4. deepset — "A Spectrum, Not a Binary"

deepset 的框架把确定性 vs 自主性看作**光谱**而非二元对立，并提出了迭代方向：

- **Moving towards determinism**：发现用例不需要那么多灵活性时，把 agentic 部分收回为确定性流程
- **Moving towards agency**：发现某些边界情况需要更多灵活性时，局部引入 agent

这恰好描述了你的演化路径：**先用自然语言 workflow 探索，稳定后逐步硬编码确定性部分，只在需要判断的地方保留 LLM**。

## 5. MindStudio — "Deterministic + Agentic Nodes"

最结构化的表述：

> **"Agentic nodes without deterministic validation produce unreliable output. Deterministic validation without agentic nodes produces no output at all."**

他们把 workflow 中的每一步分为两类节点：
- **Deterministic node**：lint、类型检查、测试——同样的输入永远同样的输出
- **Agentic node**：代码生成、修复、审查——需要判断

核心循环：**agentic 生成 → deterministic 验证 → 失败则 agentic 修复 → 再验证**。

---

## 汇总：你的观点在行业中的映射

| 你的判断 | 行业对应 |
|---|---|
| 自然语言 workflow 确定性差 | "doom-prompting"（Salesforce）、"non-determinism"（Brecht） |
| 部分硬编码增强确定性 | "guided determinism"（Salesforce）、"surround chaos with code"（Brecht） |
| 不失去过多灵活性 | "spectrum, not binary"（deepset）、hybrid reasoning |
| 稳定后升级成脚本 | "save LLM for judgment, code for everything else"（Vercel/Brecht） |
| SCAN/规则卡只能缓解 | "endless prompt refinement" 不是出路（Salesforce） |

**你的观点不是孤立的——它正在成为行业共识。** 区别在于：多数人是从企业生产系统出发得出这个结论，你是从个人知识系统的实际执行体验出发，独立走到了同一个判断。