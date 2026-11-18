# Systematology V2 迁移协议

> 本规则定义新旧系统（V1 CLD→FCM→D2D 流水线 → V2 DDC×Workflow）在同一个仓库中并存的约束。适用于 Phase 0 所有 SP 的执行。

**来源**
- [Parallel Change / Expand-Contract](https://martinfowler.com/bliki/ParallelChange.html) — Martin Fowler
- [V1/V2 同仓库重写实践](https://developers.redhat.com/articles/2026/04/22/how-we-rewrote-production-ui-without-stopping-it) — Red Hat, 2026
- [Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/strangler-fig.html) — AWS

---

## 1. 三阶段结构

采用 Expand-Contract 模式管理整个迁移生命周期：

| 阶段 | 对应项目阶段 | 行为 |
|------|------------|------|
| **Expand** | Phase 0（当前） | V2 在隔离目录中完整构建，V1 原地不动。两套系统共存，不交叉 |
| **Contract** | Phase 0 终验后 | V2 验证通过后，删除 V1 旧代码。一次 git rm，不渐进式移除 |

> 没有 Migrate 阶段——因为 V1 和 V2 是两套独立的架构，没有调用关系。V1 的输出（SharedCLD）作为参考而非依赖。Contract 直接执行。

**Contract 不执行的风险**：新旧代码永久共存，维护负担翻倍，后续开发者混淆。Phase 0 结束时必须设定明确的 Contract 时间点或触发条件。

---

## 2. 物理目录隔离

新旧代码不得在同一个目录树中混合。隔离规则：

```
V1 代码（只读参考源，待删除）：
  backend/core/modules/           CLD/FCM/D2D 模块
  backend/core/orchestration/     Lead Agent 编排
  backend/core/input/             输入与增强
  backend/core/reporting/         结果融合
  backend/core/api.py             旧 API 路由
  backend/core/service.py         测试脚手架
  旧对应的 tests/                 旧测试
  旧对应的 fastapi/routes/       旧路由（与 V2 分属不同文件）

V2 代码（agent 写区域）：
  backend/ddc/                    新 DDC 知识树模块
  backend/core/new_workflow/      新事件驱动 Workflow
  新对应的 fastapi/routes/        新路由
  新对应的 tests/                 新测试
  新对应的 web/ 组件              新前端组件

共享层（不属于任何一方，永久保留）：
  backend/infrastructure/         LLM 工厂、配置、检索、向量化等基础设施
  backend/core/models.py          共享 Pydantic 数据模型
  backend/fastapi/main.py         应用入口
  backend/fastapi/deps.py         依赖注入
  docs/                           项目文档
  web/                            前端（新旧页面共存于同一应用）
  根目录配置文件                    Makefile, pyproject.toml, application.yml
```

**目录隔离规则：**
- V1 文件：**不可修改**。SubAgent 以只读方式参考。
- V2 文件：**SubAgent 写区域**。创建和修改仅限于 V2 目录。
- 共享层文件：**可读可写**，但修改时需注意不影响 V1 和 V2 任何一方。

---

## 3. 导入边界

V2 代码在 import 时受到以下约束：

```
V2 代码 → V1 业务逻辑（modules, orchestration, input, reporting）
   ❌ 禁止 import
   原因：V2 是新架构，不应依赖 V1 的业务层。
   替代：通过共享层的数据模型间接引用，或直接读取 V1 代码做参考后自主实现。

V2 代码 → 共享基础设施（infrastructure/llms, infrastructure/config, ...）
   ✅ 允许 import
   原因：基础设施层是跨版本共享的稳定层。

V2 代码 → 共享数据模型（core/models.py）
   ✅ 允许 import
   原因：SharedCLD 等模型是中心数据契约，V2 需要引用。

V1 代码 → V2 代码
   ❌ 禁止 import
   原因：V1 是待删除的旧系统，不应产生对 V2 的新依赖。
```

---

## 4. 并发变更纪律

Red Hat 实践的核心教训：**一次只做一种变更。**

```
单一 SP 内：
  ✅ 创建新文件（V2 代码）
  ✅ 在新文件中实现业务逻辑
  ❌ 同时修改共享层接口
  ❌ 同时重命名 V1 文件
  ❌ 同时将旧代码移动到 V1/ 目录

正确做法：
  第一步：写 V2 新代码（纯新增，不触动其他）
  第二步：验证 V2 独立正确
  第三步：如有必要，再单独处理共享层的变更
```

---

## 5. Contract 条件

V1 系统可被删除的条件（所有条件必须满足）：

```
[ ] V2 系统所有单元测试通过
[ ] V2 端到端链路跑通（frontend → API → Workflow → DDC → 约束 → 输出）
[ ] V2 能处理 V1 覆盖的所有代表性输入场景
[ ] V2 无任何对 V1 业务层的 import 依赖
[ ] 部署入口已切换到 V2（如有必要）
```

Contract 执行方式：

```
git rm -r \
  backend/core/modules/ \
  backend/core/orchestration/ \
  backend/core/input/ \
  backend/core/reporting/ \
  backend/core/api.py \
  backend/core/service.py
```

如有需要保留的参考代码（如算法核心），在 Contract 前移至 `docs/references/archive/`。

---

## 6. SubAgent 注意事项

执行各 SP 的 SubAgent 在开始工作前应确认：

1. 当前 SP 写的是 V2 还是共享层代码？
2. 是否涉及引入 V1 的依赖？（如果是，违反规则 3）
3. 是否在修改非当前 SP 负责的目录？（如果是，检查目录隔离规则）
4. 是否在同一步骤内包含了多种类型的变更？（如果是，违反规则 4）

每个 SP 的文件改动清单应当与本节中的目录隔离规则一致。
