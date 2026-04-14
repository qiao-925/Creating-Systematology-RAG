# 指挥调度机制调研

## 核心问题

如何设计 Conductor 调度 Agent 并行/串行执行、处理任务拆分、结果融合和失败重试。

---

## 调度模式对比

| 模式 | 描述 | 适用场景 | 推荐 |
|------|------|----------|------|
| **全并行** | 所有 Agent 同时启动 | 任务独立，无依赖 | CLD 提取层 |
| **全串行** | Agent 逐个执行 | 有严格依赖顺序 | 不适合我们 |
| **混合拓扑** | 部分并行+部分串行 | 有依赖关系 | FCM 层（先评级后聚合）|
| **动态图** | 运行时决定依赖 | 复杂自适应 | Phase 2 |

---

## 备选方案对比

### 方案 A：CrewAI 原生编排（评估）

**优点**：
- 成熟的 Agent 编排框架
- 支持任务依赖、工具调用
- 社区活跃

**缺点**：
- 可能过于复杂
- 需要适配我们的分层架构

**适用**：快速原型验证

### 方案 B：LlamaIndex AgentWorkflow（推荐）

**理由**（来自冻结原则）：
- 项目已选定 LlamaIndex AgentWorkflow
- 不引入 LangGraph（留给下个项目）

**实现要点**：
```python
from llama_index.core.agent import AgentWorkflow, FunctionAgent

# 定义 Agent
policy_agent = FunctionAgent(
    name="policy_perspective",
    description="政策视角分析",
    tools=[search_tool, extract_causal_links],
    llm=llm
)

# 定义工作流
workflow = AgentWorkflow(
    agents=[policy_agent, economic_agent, social_agent],
    root_agent=conductor_agent
)

# 执行
result = await workflow.run(query="分析 Prop 13 对住房的影响")
```

### 方案 C：自定义轻量编排器（推荐 Phase 1）

**理由**：
- 我们的流程相对固定（CLD→FCM→D2D）
- 自定义可控性强，无框架依赖
- 易于集成评估和观测

**核心组件**：
```python
class Conductor:
    """轻量编排器"""
    
    def __init__(self, config):
        self.agents = {}
        self.execution_graph = config['graph']
    
    async def run_pipeline(self, task):
        """执行完整流水线"""
        results = {}
        
        # Phase 1: CLD 提取（并行）
        cld_results = await self._run_parallel(
            agents=['policy', 'economic', 'social'],
            task=task,
            stage='cld_extraction'
        )
        results['cld_raw'] = cld_results
        
        # 融合（串行）
        merged = await self._run_fusion(cld_results)
        results['cld_merged'] = merged
        
        # Phase 2: FCM 评级（并行）
        fcm_results = await self._run_parallel(
            agents=['policy', 'economic', 'social'],
            task=merged,
            stage='fcm_rating'
        )
        results['fcm_raw'] = fcm_results
        
        # 聚合（串行）
        aggregated = await self._run_aggregation(fcm_results)
        results['fcm_aggregated'] = aggregated
        
        # Phase 3: D2D 分析（串行）
        leverage_points = await self._run_d2d_analysis(aggregated)
        results['d2d_result'] = leverage_points
        
        return results
```

---

## 学术/工业界实践

### 1. LangGraph（被排除但值得了解）

**特点**：
- 状态机驱动的 Agent 编排
- 支持循环、条件分支
- 适合复杂多轮对话

**排除理由**：项目冻结原则，留给下个项目

### 2. CrewAI 流程（Flow）

**概念**：
```python
@crew.flow
def policy_analysis_flow():
    # 步骤 1：提取
    extraction = extract_task()
    
    # 步骤 2：融合（依赖步骤 1）
    merged = merge_task(extraction)
    
    # 步骤 3：评级（依赖步骤 2）
    rating = rate_task(merged)
    
    return rating
```

**优点**：Python 原生，易于理解

### 3. Temporal / Cadence（工作流引擎）

**特点**：
- 企业级工作流编排
- 持久化、可重试、可观测
- 过重，不适合研究项目

### 4. 自定义实现模式

**基于 asyncio**：
```python
import asyncio

class AgentExecutor:
    async def execute_parallel(self, agents, input_data):
        """并行执行多个 Agent"""
        tasks = [
            self._run_agent(agent, input_data)
            for agent in agents
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理失败
        successful = []
        for agent, result in zip(agents, results):
            if isinstance(result, Exception):
                self._log_failure(agent, result)
                # 重试或继续
            else:
                successful.append((agent, result))
        
        return successful
```

---

## 推荐方案

### Phase 1 MVP：自定义编排器 + LlamaIndex Agent

**架构**：
```
Conductor (自定义编排)
    ├── 阶段管理（CLD/FCM/D2D）
    ├── 并行执行器（asyncio）
    ├── 失败处理器（重试/降级）
    └── 结果融合器

Agent (LlamaIndex FunctionAgent)
    ├── 工具集（搜索、提取、评级）
    └── 状态管理
```

**执行流程**：
```python
class CLDFlowConductor:
    """CLDFlow 专用编排器"""
    
    async def run(self, user_query, documents):
        # 1. 输入解析
        parsed = await self._parse_input(user_query, documents)
        
        # 2. CLD 层（并行提取）
        cld_results = await self._run_phase_cld(parsed)
        
        # 3. 检查是否需要人工介入
        if cld_results['conflicts']:
            human_decision = await self._request_human_review(cld_results['conflicts'])
            cld_results = self._apply_human_decision(cld_results, human_decision)
        
        # 4. FCM 层（并行评级）
        fcm_results = await self._run_phase_fcm(cld_results['shared_cld'])
        
        # 5. D2D 层（分析）
        d2d_results = await self._run_phase_d2d(fcm_results['weight_matrix'])
        
        # 6. 生成报告
        report = self._generate_report(cld_results, fcm_results, d2d_results)
        
        return report
    
    async def _run_phase_cld(self, parsed_input):
        """CLD 层执行"""
        # 并行启动多视角 Agent
        raw_extractions = await self._execute_parallel([
            ('policy', self.policy_agent),
            ('economic', self.economic_agent),
            ('social', self.social_agent)
        ], task=parsed_input)
        
        # 节点归并（串行）
        merged_nodes = self._merge_nodes(raw_extractions)
        
        # 冲突检测（串行）
        conflicts = self._detect_conflicts(raw_extractions, merged_nodes)
        
        # 构建共享 CLD
        shared_cld = self._build_shared_cld(merged_nodes, raw_extractions)
        
        return {
            'raw_extractions': raw_extractions,
            'merged_nodes': merged_nodes,
            'conflicts': conflicts,
            'shared_cld': shared_cld
        }
```

### 失败处理策略

| 失败类型 | 处理策略 |
|----------|----------|
| Agent 超时 | 重试 1 次，仍失败则标记为"无输出" |
| Agent 异常 | 记录日志，其他 Agent 结果继续 |
| 全部失败 | 报错，请求人工检查 |
| 冲突未消解 | 标记待审核，不阻塞流程 |

### 可观测性集成

```python
class ObservableConductor(CLDFlowConductor):
    """带观测的编排器"""
    
    async def _run_phase(self, phase_name, coro):
        start_time = time.time()
        
        try:
            result = await coro
            
            self.telemetry.record_success(
                phase=phase_name,
                duration=time.time() - start_time,
                result_summary=self._summarize(result)
            )
            
            return result
            
        except Exception as e:
            self.telemetry.record_failure(
                phase=phase_name,
                error=str(e),
                duration=time.time() - start_time
            )
            raise
```

---

## 待决策事项

1. **编排框架选择**
   - 选项 A：纯自定义（推荐）
   - 选项 B：LlamaIndex AgentWorkflow
   - 选项 C：CrewAI
   - **建议**：A，控制力强，符合冻结原则

2. **并行粒度**
   - 选项 A：仅 CLD 提取层并行
   - 选项 B：CLD 提取 + FCM 评级都并行（推荐）
   - **建议**：B，最大化并行度

3. **失败重试次数**
   - 选项 A：0 次（失败即停止）
   - 选项 B：1 次（推荐）
   - 选项 C：2 次
   - **建议**：B，平衡可靠性

4. **人工介入点**
   - 选项 A：仅冲突检测后（推荐）
   - 选项 B：每层结束后都可介入
   - **建议**：A，减少打断

5. **是否支持动态重排**
   - 选项 A：固定流水线（推荐）
   - 选项 B：根据结果动态调整
   - **建议**：A，Phase 1 固定流程

---

## 代码模板

```python
import asyncio
from dataclasses import dataclass
from typing import List, Dict, Callable, Any
import time

@dataclass
class AgentTask:
    agent_id: str
    agent: Any  # Agent 实例
    input_data: Dict
    timeout: float = 30.0

@dataclass
class TaskResult:
    agent_id: str
    success: bool
    result: Any = None
    error: str = None
    duration: float = 0.0

class Conductor:
    """CLDFlow Conductor"""
    
    def __init__(self, max_retries=1, default_timeout=30.0):
        self.max_retries = max_retries
        self.default_timeout = default_timeout
        self.telemetry = []
    
    async def execute_parallel(
        self,
        tasks: List[AgentTask]
    ) -> List[TaskResult]:
        """并行执行多个 Agent 任务"""
        
        async def run_with_retry(task):
            for attempt in range(self.max_retries + 1):
                start = time.time()
                
                try:
                    result = await asyncio.wait_for(
                        task.agent.run(task.input_data),
                        timeout=task.timeout
                    )
                    
                    return TaskResult(
                        agent_id=task.agent_id,
                        success=True,
                        result=result,
                        duration=time.time() - start
                    )
                    
                except Exception as e:
                    if attempt == self.max_retries:
                        return TaskResult(
                            agent_id=task.agent_id,
                            success=False,
                            error=str(e),
                            duration=time.time() - start
                        )
                    await asyncio.sleep(1)  # 重试前等待
        
        # 并行执行
        coros = [run_with_retry(t) for t in tasks]
        results = await asyncio.gather(*coros)
        
        return results
    
    async def execute_sequential(
        self,
        tasks: List[AgentTask],
        accumulator: Callable = None
    ) -> List[TaskResult]:
        """串行执行，支持结果累积"""
        
        results = []
        accumulated = None
        
        for task in tasks:
            if accumulated is not None:
                task.input_data['previous_result'] = accumulated
            
            result = await self.execute_parallel([task])
            results.extend(result)
            
            if accumulator and result[0].success:
                accumulated = accumulator(accumulated, result[0].result)
        
        return results
```

---

## 下一步

等待用户阅读后决策 5 个事项。
