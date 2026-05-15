# CLDFlow MVP 执行计划

> 来源：`docs/ARCHITECTURE.md`
>
> 本计划只覆盖 **CLDFlow Phase 0 / MVP**：先把 `question → CLD → report` 这条最小闭环跑通，暂不进入 FCM / D2D。

## 1. 本轮目标

验证一个最小但可信的判断链路：

- 输入一个研究问题
- 生成一个可检查的 `SharedCLD`
- 输出一个可追溯的结构化报告
- 当输入不合法或护栏失败时，输出结构化失败报告

## 2. 当前冻结边界

### 保留

- `ARCHITECTURE.md` 作为唯一事实源
- `backend/business/cldflow/` 作为新架构落位
- `CLD → report` 的单主线
- 不变量：
  - CLD 前置
  - 数据边界解析
  - 自审通过才传递
  - 研究运行隔离
  - 硬失败终止

### 暂不做

- FCM
- D2D
- 多 Agent 真正编排
- 前端大改
- 历史 RAG 架构重写

## 3. MVP 交付物

### 3.1 代码交付

1. `backend/business/cldflow/models.py`
   - `CLDNode`
   - `SharedCLD`
   - `CLDFlowRunContext`
   - `CLDFlowReport`
   - `CLDFlowFailureReport`

2. `backend/business/cldflow/modules/cld/schema.py`
   - `CLDAnalysisInput`
   - `CLDAnalysisOutput`

3. `backend/business/cldflow/modules/cld/module.py`
   - 最小 CLD 生成逻辑
   - 可审计元数据

4. `backend/business/cldflow/guardrails.py`
   - 问题校验
   - 预算校验
   - CLD 就绪校验

5. `backend/business/cldflow/service.py`
   - 统一入口
   - 成功 / 失败结构化返回

6. 单元测试
   - 正常输出
   - 空问题拒绝
   - 护栏失败
   - 结构化报告字段完整性

### 3.2 文档交付

- `docs/cldflow/mvp-execution-plan.md` 本文件
- 必要时在 `README.md` / 主导航中增加一个轻量入口

## 4. 执行步骤

### Step 1. 冻结 MVP 边界

确认本轮只做：

- `question → SharedCLD → report`
- 失败时返回 `CLDFlowFailureReport`

### Step 2. 固化 schema

确保以下对象稳定：

- `CLDNode`
- `SharedCLD`
- `CLDFlowRunContext`
- `CLDFlowReport`
- `CLDFlowFailureReport`

### Step 3. 固化 guardrails

最少需要三类护栏：

- 问题合法性
- 预算合法性
- CLD 是否已准备好

### Step 4. 固化 CLDModule 最小行为

当前阶段不追求真实多 Agent，只要求：

- 输入可追踪
- 输出结构稳定
- metadata 可审计

### Step 5. 补测试

必须覆盖：

- 成功路径
- 空输入拒绝
- 结构化失败
- shared_cld 非空

### Step 6. 连接主入口

把 `CLDFlowService` 作为新架构入口保留下来，后续再决定是否接入 UI。

## 5. 验收标准

MVP 完成的标准是：

- [ ] 给一个正常问题，返回 `CLDFlowReport`
- [ ] `shared_cld.nodes` 非空
- [ ] `synthesized_insights` 非空
- [ ] 给空问题，返回 `CLDFlowFailureReport`
- [ ] 报告中包含可审计 metadata
- [ ] 测试通过

## 6. 失败与降级策略

- 空问题：立即失败，不进入后续步骤
- CLD 生成失败：返回失败报告，不继续推理
- 护栏失败：中止本次 run，保留 diagnostics
- 未来再接 FCM / D2D 时，必须保持当前失败语义不变

## 7. 当前状态判断

当前仓库已经具备 MVP 骨架，下一步不是重构大体系，而是：

1. 补齐护栏与 schema
2. 固化测试
3. 再考虑把新入口接到更高层服务
