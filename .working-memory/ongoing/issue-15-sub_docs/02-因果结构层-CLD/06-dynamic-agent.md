# 动态视角 Agent 生成机制调研

> 目标：为 CLDFlow 设计"根据问题动态生成 Specialist Agent"的机制
> 调研日期：2026-04-12

---

## 一、核心问题：为什么需要动态生成视角

**固定视角的问题**：
- 预设的"政策/经济/社会"视角无法覆盖所有问题类型
- 不同问题需要的专业领域差异巨大（医疗政策 vs 能源政策 vs 教育政策）
- 硬性分配视角会导致某些视角无话可说，某些视角遗漏关键信息

**动态视角的价值**：
- 根据问题特征生成最相关的专家角色
- 每个 Agent 都有明确的专业边界和关注焦点
- 避免视角冗余，提高多 Agent 协作效率

---

## 二、学术前沿：PersonaFlow 与 PRISM

### 2.1 PersonaFlow (arXiv 2409.12538, 2024)

**核心贡献**：
- 使用 LLM 模拟**领域特定专家视角**（domain-specific expert perspectives）
- 支持**跨学科研究创意生成**（interdisciplinary research ideation）
- 用户可**自定义专家画像**（customizable expert profiles）

**关键发现**：
1. 用户自定义专家画像的能力显著提升**自主性感**（sense of agency）
2. 多样化专家视角促进**批判性思维活动**（interpretation, analysis, evaluation, inference）
3. 不增加用户的**认知负荷**（cognitive load）

**对 CLDFlow 的启示**：
- ✅ 让用户（或 Conductor）能够定义需要的专家类型
- ✅ 动态生成的 Persona 应包含：角色定义、专业背景、关注焦点、检索偏好

---

### 2.2 PRISM (arXiv 2603.18507, 2026)

**核心贡献**：
- **基于意图的专家角色路由**（Intent-Based Persona Routing）
- 发现：专家角色能提升对齐度，但可能损害准确性
- 解决方案：根据任务类型动态选择是否使用专家角色

**关键技术**：
```
PRISM = Persona Routing via Intent-based Self-Modeling

流程：
1. 识别任务意图（生成型 vs 判别型）
2. 如果是生成型任务（如创意、写作）→ 使用专家角色，提升对齐度
3. 如果是判别型任务（如分类、判断）→ 减少角色干扰，保持准确性
```

**对 CLDFlow 的启示**：
- CLD 提取是**生成型任务**（从文本生成因果结构）→ 适合使用专家角色
- 但节点融合时的**语义相似度判断**是判别型任务 → 应减少角色干扰

---

## 三、行业实践：CrewAI 与 AutoGen

### 3.1 CrewAI 的动态 Agent 模式

**核心概念**：
- `Agent` + `Task` + `Crew` 三层架构
- `Process` 控制执行流程（sequential / hierarchical / consensual）

**动态生成能力**（来自社区讨论）：
```python
# CrewAI 支持 YAML 配置或代码动态创建 agents
# 社区实践：根据用户输入动态选择或生成 agent 配置

# 示例模式：基于任务特征选择预定义角色
researcher = Agent(
    role='{domain} Policy Analyst',  # 动态填充领域
    goal='Analyze {policy_name} from {perspective} angle',
    backstory='You are an expert in {domain} with focus on {aspect}...',
    tools=[search_tool, analysis_tool]
)
```

**限制**：
- CrewAI 的 Agent 创建是**配置驱动**，而非完全的动态生成
- 需要预定义角色模板，然后填充变量

---

### 3.2 AutoGen 的 Conversable Agent

**核心概念**：
- `ConversableAgent` 支持自定义 system message
- 通过 `description` 字段定义 Agent 角色

**动态生成模式**：
```python
# AutoGen 支持完全动态创建
agent = ConversableAgent(
    name=f"{domain}_expert",
    system_message=generate_persona_prompt(domain, question),
    llm_config=llm_config,
)
```

**优势**：更灵活，完全由 LLM 生成角色描述
**劣势**：缺乏结构化约束，角色质量依赖 prompt 工程

---

## 四、最接近的现有研究：Agentic Leash

**论文**: arXiv 2601.00097, "The Agentic Leash: Extracting Causal Feedback Fuzzy Cognitive Maps"

**核心机制**：
- LLM Agent 从原始文本提取 FCM
- 使用 **3-step pipeline**：名词提取 → 精炼 → 边提取
- **单 Agent 架构**，无多视角隔离

**与 CLDFlow 的差异**（我们的创新点）：

| 维度 | Agentic Leash | CLDFlow |
|------|---------------|---------|
| Agent 数量 | 单 Agent | 多 Agent（动态生成） |
| 视角隔离 | ❌ 无 | ✅ 有（Conductor 协调） |
| CLD 融合 | ❌ 无（直接输出 FCM） | ✅ 有（多视角归并） |
| 杠杆点分析 | ❌ 无 D2D | ✅ 有简化版 D2D |

**结论**：Agentic Leash 验证了 LLM 提取 FCM 的可行性，但缺少多视角架构。我们的**动态视角生成 + 视角隔离 + CLD 融合**是增量创新。

---

## 五、CLDFlow 动态视角 Agent 生成机制设计

### 5.1 核心架构

```
用户问题
    ↓
[Conductor Agent - 问题分析]
    ├── 识别问题领域（domain）
    ├── 识别关键维度（dimensions）
    └── 生成视角清单（perspectives）
        ↓
[动态 Agent 实例化]
    对每个 perspective:
        - 生成角色描述（Role Description）
        - 生成检索策略（Search Strategy）
        - 生成提取偏好（Extraction Focus）
        ↓
    [Specialist Agent 1] ... [Specialist Agent N]
        ↓
[并行执行]
        ↓
[CLD 融合]
```

### 5.2 动态生成 Prompt 模板

```python
PERSPECTIVE_GENERATION_PROMPT = """
You are the Conductor of a multi-agent research system.

Given the research question: {question}

Generate 3-5 expert perspectives needed for comprehensive analysis.

For each perspective, provide:
1. **Role Name**: Clear title (e.g., "Public Finance Expert")
2. **Domain**: Specific domain of expertise
3. **Focus Areas**: 2-3 key aspects this expert should focus on
4. **Search Strategy**: What types of sources to prioritize
5. **Extraction Preference**: What causal relationships to look for

Output format (JSON):
{
    "perspectives": [
        {
            "role": "...",
            "domain": "...",
            "focus_areas": ["...", "..."],
            "search_strategy": "...",
            "extraction_preference": "..."
        }
    ],
    "reasoning": "Why these perspectives are needed"
}

Constraints:
- Perspectives should be complementary, not overlapping
- Each should have distinct expertise boundaries
- Cover both macro and micro aspects of the problem
"""
```

### 5.3 Specialist Agent System Prompt 模板

```python
def generate_specialist_prompt(perspective: dict, question: str) -> str:
    return f"""
You are a {perspective['role']} specializing in {perspective['domain']}.

Your task: Extract causal relationships from research materials related to:
"{question}"

Your focus areas: {', '.join(perspective['focus_areas'])}

When analyzing materials:
1. Look for: {perspective['extraction_preference']}
2. Prioritize sources: {perspective['search_strategy']}
3. Be thorough but stay within your expertise boundary
4. Always cite your sources with specific quotes

Output format:
- Use CausalLink structured output (via Instructor)
- Include: source, target, polarity, weight, evidence, confidence

You do NOT need to consider perspectives outside your domain.
Trust that other specialists will cover those aspects.
"""
```

### 5.4 视角数量决策

| 问题复杂度 | 视角数量 | 示例 |
|-----------|---------|------|
| 简单 | 2-3 | 经济政策：财政 + 市场 + 社会 |
| 中等 | 3-4 | 住房政策：法律 + 财政 + 市场 + 社会 |
| 复杂 | 4-5 | 能源转型：政策 + 技术 + 经济 + 环境 + 社会 |

**动态决策因素**：
- Conductor 根据问题广度自动调整
- 硬上限：最多 5 个视角（避免协作复杂度爆炸）

---

## 六、与检索停止条件的联动

```
[动态视角 Agent 生成]
        ↓
[并行检索]
        ↓
[每个 Agent 的检索停止条件]
    ├── 该视角下的变量覆盖度 ≥ 80%
    ├── 连续 2 轮无新发现
    └── 硬限制：最多 5 轮
        ↓
[所有 Agent 完成后]
        ↓
[CLD 融合]
```

---

## 七、Phase 1 实现建议

### 7.1 简化方案（MVP）

| 复杂度 | 方案 | 说明 |
|--------|------|------|
| 轻量 | 预定义模板 + 变量填充 | 10-15 个角色模板，按领域匹配 |
| 中等 | LLM 动态生成角色描述 | 完全由 LLM 根据问题生成 |
| 复杂 | 训练专用生成模型 | Phase 2 考虑 |

**推荐 Phase 1 采用"预定义模板 + LLM 优化"混合**：
- 预定义 3-5 个通用视角模板（政策/经济/社会/法律/技术）
- LLM 根据问题动态调整模板细节（关注焦点、检索策略）

### 7.2 代码结构草案

```python
class PerspectiveGenerator:
    """动态视角生成器"""
    
    TEMPLATES = {
        "policy": {...},
        "economic": {...},
        "social": {...},
        "legal": {...},
        "technical": {...},
    }
    
    def generate(self, question: str) -> List[Perspective]:
        # 1. 用 LLM 识别问题需要的领域
        domains = self._identify_domains(question)
        
        # 2. 加载对应模板
        templates = [self.TEMPLATES[d] for d in domains]
        
        # 3. 用 LLM 细化每个模板
        perspectives = []
        for template in templates:
            refined = self._refine_with_llm(template, question)
            perspectives.append(refined)
        
        return perspectives

class SpecialistAgentFactory:
    """Specialist Agent 工厂"""
    
    def create(self, perspective: Perspective) -> Agent:
        system_prompt = generate_specialist_prompt(perspective)
        return Agent(
            role=perspective.role,
            system_message=system_prompt,
            tools=[search_tool, extraction_tool],
        )
```

---

## 八、参考资源

- **PersonaFlow** (arXiv 2409.12538): LLM-Simulated Expert Perspectives
- **PRISM** (arXiv 2603.18507): Intent-Based Persona Routing
- **Agentic Leash** (arXiv 2601.00097): Single-Agent FCM Extraction
- **CrewAI Docs**: https://docs.crewai.com/
- **CrewAI Dynamic Generation**: https://community.crewai.com/t/generating-agents-and-tasks-files-dynamically/1625

---

*Related: CLDFlow 业务架构设计 | 下一步: 工程架构图（模块接口 + 流水线）*
