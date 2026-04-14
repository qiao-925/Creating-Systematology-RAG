# CLDFlow 不变量

> 不可变约束。违反即架构错误。由 Pydantic 验证 + 结构测试强制执行。
> 信念来源：`docs/core-beliefs.md` #5（执行不变量，不微管实现）
> 实现选择见：`docs/CLDFlow-defaults.md`

---

## I-1. 三层依赖方向

前端层 → 业务层 → 基础设施层，单向依赖。

- 禁止反向依赖：基础设施层不能依赖业务层或前端层
- 禁止跨层访问：前端层不能直接访问基础设施层
- 新增 CLDFlow 模块遵循同样规则：`backend/business/cldflow/` 可依赖 `backend/infrastructure/`，反之不可

**验证方式**：结构测试 + import 检查

## I-2. CLD 输出必须符合 JSON Schema

所有 CLD 提取 Agent 的输出必须通过 `SharedCLD` Pydantic model 验证。

- 字段：`nodes: list[CLDNode]`、`links: list[CausalLink]`
- `CLDNode` 必须有：`id`、`name`、`polarity`（+/-/0）
- `CausalLink` 必须有：`source_id`、`target_id`、`polarity`（+/−）
- 不合规输出 = 提取失败，不进入下游

**验证方式**：Pydantic strict mode

## I-3. CLD→FCM→D2D 流水线不可拆

三层必须顺序执行，不可跳层。

- CLD 是 FCM 的输入（节点和边）
- FCM 是 D2D 的输入（权重矩阵和收敛状态）
- 不允许"直接做 FCM"或"跳过 FCM 做 D2D"

**验证方式**：Conductor 编排器的状态机强制顺序

## I-4. 全自动协作，无人工介入点

Phase 1 全程自动，不设人工介入点。

- 3 Agent 并行提取 + 自动融合
- 高分歧由裁判 Agent 消解
- 人只在运行结束后审查最终产出

**验证方式**：Conductor 编排器无 `pause_for_human` 分支

## I-5. 数据边界解析（Parse, Don't Validate）

每层输入必须在边界处解析和验证，不允许模糊数据穿透。

- CLD 层输出 → FCM 层输入：必须通过 FCM 层的 Pydantic model 验证
- FCM 层输出 → D2D 层输入：必须通过 D2D 层的 Pydantic model 验证
- 不允许"假设上游数据格式正确"

**验证方式**：每层入口的 Pydantic validator

## I-6. 研究运行隔离

每次研究运行是隔离的，不依赖前次运行的残留状态。

- 运行内状态在运行内维护
- 运行结束即归档
- 运行间无隐式状态共享

**验证方式**：Conductor 编排器的运行初始化逻辑

## I-7. 自审通过才传递

每层 agent 产出必须经过自审才传递到下游。

- CLD 提取后：自审（节点数合理性、边连通性、Schema 合规）
- FCM 仿真后：自审（收敛性检查）
- D2D 分析后：自审（杠杆点排序合理性）
- 自审不通过 = 该层失败，不污染下游

**验证方式**：每层 agent 的 `validate_output()` 方法

---

*共 7 个不变量。新增不变量需满足：被违反 ≥1 次或有明确证据表明不执行会导致架构错误。*
*实现选择（非不变量）见 `docs/CLDFlow-defaults.md`*
