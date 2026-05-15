# Cascade Chat Conversation

  Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

https://yousali.com/posts/20251124-how-to-coding-with-ai/
https://yousali.com/posts/20260405-harness-engineering-guide/

读一下这两篇文章我感觉质量还挺高的。嗯希望你能够去总结他的核心论点。然后我会针对的，我会针对，然后摘抄一些它的核心句子，然后我会针对性的给你提问，然后以便我能够最快的去了解它。


*Read URL content from /posts/20251124-how-to-coding-with-ai/ *

*Read URL content from /posts/20260405-harness-engineering-guide/ *

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

### Planner Response

全部内容已经读完了，足够总结。来整理两篇文章的核心论点。

---

# 两篇文章核心论点

---

## 文章一：《从「写代码」到「验代码」》

**核心命题：AI 时代工程师的角色已经从「生成者」变成「验证者」。**

### 五个核心论点

1. **别再问「准不准」，先算「值不值」**
   AI 不是精确工具，是概率工具。正确的心态是：接受它会出错，然后设计一套流程把错误控制在可接受范围内，而不是追求每次输出都对。

2. **对 AI 写的代码，要比自己写的代码更不信任**
   AI 生成的代码最危险的不是写不出来，而是「看起来对，其实不对」。能跑通 happy path ≠ 安全上线。

3. **让项目「AI 友好」= 标准化 + 自动化**
   - 标准化（接口规范、设计文档、术语表）是喂给 AI 的高质量上下文，同时也是给人看的说明书。
   - 自动化（pre-commit、CI、linter、测试）是让机器先说「对/不对」，降低人工验证成本。
   - 这两件事可以用 AI 来做——用 AI 生成文档、再用文档反哺 AI，形成正向飞轮。

4. **人类是「上下文极小的 LLM」，调度开销才是真正瓶颈**
   用了 AI 反而更累，根本原因是同时开 N 个任务、不停切换上下文，心流被打碎。解法是时间分层、时分复用 AI（先定任务，让 AI 跑，再集中验收）。

5. **两条长期原则**
   - **瓶颈已从「生成」转到「验证」**——把精力放在写测试、设计监控、建立回滚机制上。
   - **上下文为王**——「AI 写代码的水平，往往就是你提供上下文的水平。」

---

## 文章二：《一文读懂 Harness Engineering》

**核心命题：Harness 是一套围绕大模型能力缺口而建的补偿制度，它的价值不在厚度，在追踪「补偿面迁移」的速度。**

### 四个核心论点

1. **Harness 的三层架构各自对应一种 AI 缺陷**
   - **第一层（流程管控）**：解决 AI 不遵守流程的问题。Anthropic 用 JSON 物理锁防虚标、三步唤醒仪式防失忆、Git 存档防死胡同、Context Reset 应对上下文爆炸；OpenAI 用「仓库即现实（Repo-as-truth）」——一切规则必须写进仓库并变成可执行的 CI 检查，Agent 不需要记住规则，只需要根据报错改到通过。
   - **第二层（并发调度）**：解决多 Agent 协作时的无政府状态。Cursor 用 Planner-Worker-Judge 三层架构 + DAG 引擎硬性门控；Anthropic 用二分查找+并行隔离定位并发 Bug。
   - **第三层（验证对抗）**：解决 AI 无法客观评估自己的问题。Anthropic 把 Evaluator 拆成独立 Agent，对抗生成器的盲目自信；Cursor 用 8 通道并行盲审 + 多数投票。沙盒隔离是必需品，防止 AI 在考不过时直接篡改评分标准。

2. **补偿面在迁移，不是在增长**
   Harness 的每个组件编码的是「模型做不到什么」的假设。模型每强一分，某些假设就不再成立——Anthropic 在 Opus 4.6 后开始拆掉 Context Reset 和 Sprint Contract。**能拆，说明之前搭得有效；拆得快，说明一直知道自己在补偿什么。**

3. **「最轻量的干预反而最有效」，但有前提**
   Cursor 发现影响系统行为最大的因素是 Prompt，其次是 Harness 架构，最后才是模型本身。但这个排序建立在 Harness 已经搭好的前提上——没有那层架构，再好的 Prompt 只是对一群互相踩踏的 Agent 喊话。

4. **真正的护城河不在 Harness 的厚度**
   声称拥有「最完善 Harness」的公司，实际上是在对当前模型的短板下重注，模型越强它越慢。护城河在于：**知道下一寸该加什么，上一寸该拆什么。**

---

## 两篇的关系

| | 文章一 | 文章二 |
|---|---|---|
| **视角** | 个人/团队工程实践 | 行业架构演化图谱 |
| **核心问题** | 个人怎么和 AI 高效协作 | 系统怎么管住 AI |
| **共同内核** | 验证比生成更难；上下文质量决定输出质量 |

---

你的问题随时来，我已经把两篇的结构都消化了。

*Viewed [%E6%B5%8F%E8%A7%88%E5%99%A8%E6%93%8D%E4%BD%9C%E5%B7%A5%E5%85%B7%E6%8A%80%E6%9C%AF%E9%80%89%E5%9E%8B%E5%AF%B9%E6%AF%94.md](file:///c:/Users/nonep/Desktop/win11/%E6%B5%8F%E8%A7%88%E5%99%A8%E6%93%8D%E4%BD%9C%E5%B7%A5%E5%85%B7%E6%8A%80%E6%9C%AF%E9%80%89%E5%9E%8B%E5%AF%B9%E6%AF%94.md) *

*User accepted the command `python -c "
import json
data = json.load(open(r'C:\Users\nonep\AppData\Local\Google\Chrome\User Data\Profile 1\Bookmarks', encoding='utf-8'))

# 找 arxiv 文件夹
def find_folder(node, name):
    if isinstance(node, dict):
        if node.get('name') == name and node.get('type') == 'folder':
            return node
        if 'children' in node:
            for child in node['children']:
                result = find_folder(child, name)
                if result:
                    return result
    elif isinstance(node, list):
        for item in node:
            result = find_folder(item, name)
            if result:
                return result
    return None

arxiv = find_folder(data, 'arxiv')
if arxiv:
    print('arxiv 文件夹内容：\n')
    for item in arxiv.get('children', []):
        if item.get('type') == 'folder':
            print(f'?? {item[\"name\"]}')
            for sub in item.get('children', [])[:3]:
                print(f'   - {sub.get(\"name\", \"\")}: {sub.get(\"url\", \"\")[:60]}...')
            if len(item.get('children', [])) > 3:
                print(f'   ... 还有 {len(item.get(\"children\")) - 3} 项')
        elif item.get('type') == 'url':
            print(f'?? {item[\"name\"]}: {item.get(\"url\", \"\")[:60]}...')
"`*

### User Input

总结我并没有他的核心观点。你你你这样你再结合他自己去做一做一版总结，他到底想说什么？总结出三个点。

### Planner Response

两篇合并，各提炼三个字的核心，然后给你一个终极结论。

---

## 文章一：写代码 → 验代码

1. **AI 会犯错，接受它** — 不要追求每次生成都对，要设计一套能兜住错误的流程
2. **验证比生成更值钱** — 你的时间应该花在测试、监控、回滚，而不是盯着 AI 写每一行
3. **上下文决定输出质量** — 你给 AI 的背景越清晰，它越像靠谱的人；你只丢一句模糊需求，它就是个诗人

---

## 文章二：Harness Engineering

1. **Harness 是补偿，不是能力** — 每一个组件都是在填模型当前做不到的坑，模型变强了就该拆，厚不代表好
2. **管住 AI 要靠三层制度** — 流程管控（不让它乱走）、并发调度（不让它互相踩踏）、验证对抗（不让它自我感觉良好）
3. **护城河在拆的速度，不在加的厚度** — 知道该加什么是入门，知道该拆什么才是真本事

---

## 两篇的共同底色

> **模型是概率机器，你是系统设计师。** 你的工作不是让它每次都对，是设计一个让它错了也能被发现、被纠正的环境。