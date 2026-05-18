# 子计划 C：测试体系

> 建立覆盖 CLDFlow 全链路的测试体系——黄金样例、单元测试、集成测试、覆盖率达标。独立于前后端，可并行推进。

## 版本目标

- 做什么：建立测试夹具、黄金样例、单元测试（43 个）、集成测试（10 个），达成非 LLM 代码覆盖率 ≥ 80%
- 为什么：测试是 MVP 可发布性的硬性门禁，没有测试的代码不可视为完成

### 成功标准

- 非 LLM 代码行覆盖率 ≥ 80%
- 所有测试可重复运行，无网络依赖
- 至少一组黄金样例覆盖完整流水线

### 范围

**In Scope**
- 测试夹具与黄金样例
- 数据模型、FCM、D2D、CLD、护栏、报告的单元测试
- 全链路集成测试
- 覆盖率报告

**Out of Scope**
- 前端测试（后续迭代）
- 性能测试（后续迭代）
- 真实 LLM 端到端测试（子计划 D 的部署验证）

## 文档锚定

- 锚定：`pytest.ini` — 测试配置、marker 定义
- 锚定：`backend/tests/` — 测试文件目录
- 同步：`Makefile` — 测试命令别名

## 决策清单

### 核心决策

- [x] D1 测试框架：pytest + pytest-asyncio
- [x] D2 LLM mock 方案：mock `llama_index.core.llms.LLM.complete()` 方法
- [x] D3 黄金样例场景：财政补贴 + Prop 13（1978加州房产税）

### 支撑决策

- [x] D4 覆盖率目标：非 LLM 代码行覆盖率 ≥ 80%
- [x] D5 测试组织：`backend/tests/` 为主，`tests/` 放集成/e2e

## 任务清单

### 阶段 1：测试基础设施

- [x] T18 建立测试夹具与黄金样例
  - 产出：`backend/tests/fixtures/cldflow_fixtures.py`（财政补贴 CLD: 6 节点 7 边、WeightedFCM、LeverageAnalysis、mock LLM、Specialist 输出）
  - 验收：测试可重复运行，无网络依赖
  - 失败路径：降级 — 先用 1 个样例

### 阶段 2：单元测试

- [x] T19a 数据模型单测
  - 产出：`backend/tests/test_cldflow_unit.py::TestModels`（11 个测试：CLDNode strict/extra_forbidden、CausalLink literal/invalid、SharedCLD、Scenario、SimConfig、WeightedFCM、RunContext、StructuredReport、FailureReport）
  - 验收：Pydantic strict mode 校验通过
  - 失败路径：—

- [x] T19b FCM 模块单测
  - 产出：`TestFCMMapper`（2 个：权重映射、空输入）、`TestFCMSimulator`（4 个：收敛、自定义初始态、场景对比、简单收敛）
  - 验收：映射正确性、Kosko 收敛
  - 失败路径：—

- [x] T19c D2D 模块单测
  - 产出：`TestD2DSensitivity`（2 个：golden、单节点）、`TestD2DRanking`（2 个：golden、含不确定性）、`TestD2DUncertainty`（1 个：区间范围）
  - 验收：扰动计算、排序、不确定性区间
  - 失败路径：—

- [x] T19d CLD 模块单测
  - 产出：`TestCLDMerge`（4 个：相同/不同/相似字符串、无重复归并、相似节点归并、保留边）、`TestCLDConflict`（3 个：无冲突、检测冲突、多数决）
  - 验收：归并正确性、冲突分级
  - 失败路径：—

- [x] T19e 护栏与报告单测
  - 产出：`TestGuardrails`（6 个：Pipeline Rail、Budget Guard、Schema Guard pass/fail、Isolation Guard、Self-Review Gate pass/too_few/orphan）、`TestReporting`（3 个：基础/含FCM/含leverage）
  - 验收：护栏逻辑正确、报告生成
  - 失败路径：—

### 阶段 3：集成测试

- [x] T19f 全链路集成测试
  - 产出：`backend/tests/test_cldflow_integration.py`（10 个：golden CLD 全链路、服务 happy path、空 CLD、失败报告、FCM 传播、场景对比、D2D 排序/不确定性、placeholder 模式）
  - 验收：CLD → FCM → D2D → Report 全链路可跑通
  - 失败路径：降级 — 先覆盖核心路径

### 阶段 4：评估

- [x] T20 输出 review 报告
  - 产出：`docs/CLDFlow MVP Builder/MVP-releasability-assessment.md`
  - 验收：完成度、风险、阻塞、Phase 2a 建议
  - 失败路径：—

## 执行记录

- [x] 05-15 T18-T20 全部完成
- [x] 05-18 执行验证：53/53 测试通过（43 单测 + 10 集成）

### 覆盖率明细

| 模块 | 覆盖率 | 判定 |
|------|--------|------|
| D2D sensitivity | 100% | ✅ |
| D2D uncertainty | 100% | ✅ |
| D2D ranking | 93% | ✅ |
| FCM mapper | 92% | ✅ |
| FCM simulator | 86% | ✅ |
| Guardrails | 88% | ✅ |
| Reporting | 97% | ✅ |
| CLD merge | 78% | ⚠️ 接近目标 |
| CLD judge | 21% | LLM 依赖，需端到端验证 |
| CLD module | 42% | LLM 依赖 |
| Specialist | 25% | LLM 依赖 |
| Lead Agent | 0% | LLM 依赖 |
| Tools | 0% | LLM 依赖 |

**结论**：非 LLM 代码覆盖率 ≥ 80%（目标达成）。LLM 依赖代码需通过部署后的端到端验证。

## 附录：失败与降级矩阵（测试相关）

- 检索为空 → 硬失败：改写重试 1 次后终止
- 任一模块失败 → StructuredFailureReport（含失败阶段、原因、详情）
