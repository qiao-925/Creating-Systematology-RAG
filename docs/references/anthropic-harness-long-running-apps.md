# Anthropic Harness Design for Long-Running Application Development

## 原始来源

- 标题：Harness design for long-running application development
- 来源：Anthropic
- 原始链接：`https://www.anthropic.com/engineering/harness-design-long-running-apps`
- 访问日期：2026-05-15

## 原文副本

Harness design for long-running application development

Published Mar 24, 2026

Harness design is key to performance at the frontier of agentic coding. Here's how we pushed Claude further in frontend design and long-running autonomous software engineering.

Written by Prithvi Rajasekaran, a member of our Labs team.

Over the past several months I’ve been working on two interconnected problems: getting Claude to produce high-quality frontend designs, and getting it to build complete applications without human intervention. This work originated with earlier efforts on our frontend design skill and long-running coding agent harness, where my colleagues and I were able to improve Claude’s performance well above baseline through prompt engineering and harness design—but both eventually hit ceilings.

To break through, I sought out novel AI engineering approaches that held across two quite different domains, one defined by subjective taste, the other by verifiable correctness and usability. Taking inspiration from Generative Adversarial Networks (GANs), I designed a multi-agent structure with a generator and evaluator agent. Building an evaluator that graded outputs reliably—and with taste—meant first developing a set of criteria that could turn subjective judgments like “is this design good?” into concrete, gradable terms.

I then applied these techniques to long-running autonomous coding, carrying over two lessons from our earlier harness work: decomposing the build into tractable chunks, and using structured artifacts to hand off context between sessions. The final result was a three-agent architecture—planner, generator, and evaluator—that produced rich full-stack applications over multi-hour autonomous coding sessions.

Why naive implementations fall short

We've previously shown that harness design has a substantial impact on the effectiveness of long running agentic coding. In an earlier experiment, we used an initializer agent to decompose a product spec into a task list, and a coding agent that implemented the tasks one feature at a time before handing off artifacts to carry context across sessions. The broader developer community has converged on similar insights, with approaches like the "Ralph Wiggum" method using hooks or scripts to keep agents in continuous iteration cycles.

But some problems remained persistent. For more complex tasks, the agent still tends to go off the rails over time. While decomposing this issue, we observed two common failure modes with agents executing these sorts of tasks.

First is that models tend to lose coherence on lengthy tasks as the context window fills. Some models also exhibit "context anxiety," in which they begin wrapping up work prematurely as they approach what they believe is their context limit. Context resets—clearing the context window entirely and starting a fresh agent, combined with a structured handoff that carries the previous agent's state and the next steps—addresses both these issues.

This differs from compaction, where earlier parts of the conversation are summarized in place so the same agent can keep going on a shortened history. While compaction preserves continuity, it doesn't give the agent a clean slate, which means context anxiety can still persist.

A second issue, which we haven’t previously addressed, is self-evaluation. When asked to evaluate work they've produced, agents tend to respond by confidently praising the work—even when, to a human observer, the quality is obviously mediocre. Separating the agent doing the work from the agent judging it proves to be a strong lever to address this issue.

Frontend design: making subjective quality gradable

I started by experimenting on frontend design, where the self-evaluation issue was most visible. Absent any intervention, Claude normally gravitates toward safe, predictable layouts that are technically functional but visually unremarkable.

Two insights shaped the harness I built for frontend design. First, while aesthetics can’t be fully reduced to a score—they can be improved with grading criteria that encode design principles and preferences. Second, by separating frontend generation from frontend grading, we can create a feedback loop that drives the generator toward stronger outputs.

With this in mind, I wrote four grading criteria that I gave to both the generator and evaluator agents in their prompts:

- Design quality
- Originality
- Craft
- Functionality

I emphasized design quality and originality over craft and functionality.

I calibrated the evaluator using few-shot examples with detailed score breakdowns. This ensured the evaluator’s judgment aligned with my preferences, and reduced score drift across iterations.

I built the loop on the Claude Agent SDK, which kept the orchestration straightforward. A generator agent first created an HTML/CSS/JS frontend based on a user prompt. I gave the evaluator the Playwright MCP, which let it interact with the live page directly before scoring each criterion and writing a detailed critique. That feedback flowed back to the generator as input for the next iteration. I ran 5 to 15 iterations per generation.

Scaling to full-stack coding

With these findings in hand, I applied this GAN-inspired pattern to full-stack development. The generator-evaluator loop maps naturally onto the software development lifecycle, where code review and QA serve the same structural role as the design evaluator.

The architecture

For this work I built on the foundation from the original harness with a three-agent system, with each agent addressing a specific gap I'd observed in prior runs. The system contained the following agent personas:

- Planner
- Generator
- Evaluator

Before each sprint, the generator and evaluator negotiated a sprint contract: agreeing on what "done" looked like for that chunk of work before any code was written.

Communication was handled via files: one agent would write a file, another agent would read it and respond either within that file or with a new file that the previous agent would read in turn.

Running the harness

The harness was over 20x more expensive, but the difference in output quality was immediately apparent.

Iterating on the harness

The first set of harness results was encouraging, but it was also bulky, slow, and expensive. The logical next step was to find ways to simplify the harness without degrading its performance.

Removing the sprint construct

I started by removing the sprint construct entirely.

I kept both the planner and evaluator, as each continued to add obvious value.

With the sprint construct removed, I moved the evaluator to a single pass at the end of the run rather than grading per sprint.

Results from the updated harness

The generator was still liable to miss details or stub features when left to its own devices, and the QA still added value in catching those last mile issues for the generator to fix.

What comes next

As models continue to improve, we can roughly expect them to be capable of working for longer, and on more complex tasks.

From this work, my conviction is that the space of interesting harness combinations doesn't shrink as models improve. Instead, it moves, and the interesting work for AI engineers is to keep finding the next novel combination.

## 范式摘录（原文节选）

- Harness design is key to performance.
- Decomposing the build into tractable chunks.
- Using structured artifacts to hand off context between sessions.
- Separating the agent doing the work from the agent judging it.
- Create a feedback loop that drives the generator toward stronger outputs.
- Before each sprint, the generator and evaluator negotiated a sprint contract.
- Communication was handled via files.
- Remove pieces that are no longer load-bearing to performance.

## 本地化映射

- 对应 `AGENTS.md` 的验证闭环、结构化交接、生成与评估分离。
- 对应 `docs/ARCHITECTURE.md` 中的 `RunContext`、`SharedCLD`、`StructuredReport` 等中间工件。
- 对应当前仓库对长任务、分层模块和可恢复执行流程的治理方式。
