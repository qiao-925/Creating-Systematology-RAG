# CLDFlow 文档中心

> 渐进式披露：从核心原则到层细节，按需深入。

---

## 文档结构

```
docs/
├── 核心文档（根目录，必读）
│   ├── core-beliefs.md              # 15命题，三层结构
│   ├── CLDFlow-invariants.md        # 7个不可变约束
│   ├── CLDFlow-defaults.md          # 实现默认值（可调）
│   ├── CLDFlow-architecture.md      # 业务架构全景（流程图+五层+接口）
│   └── architecture.md              # 系统架构设计
│
├── cldflow/                         # 各层详细设计
│   ├── input-enhancement.md         # 输入层
│   ├── cld-extraction.md            # CLD 提取
│   ├── cld-node-merging.md          # CLD 节点归并
│   ├── cld-conflict-resolution.md   # CLD 冲突消解
│   ├── cld-data-format.md           # CLD 数据格式+Pydantic模型
│   ├── dynamic-agent.md             # CLD 动态视角Agent
│   ├── fcm-weight-conversion.md     # FCM 权重转换
│   ├── fcm-simulation.md            # FCM 仿真算法
│   ├── fcm-aggregation.md           # FCM 权重聚合
│   ├── d2d-sensitivity-analysis.md  # D2D 敏感性分析
│   ├── d2d-uncertainty.md           # D2D 不确定区间
│   ├── conductor-orchestration.md   # 跨层 Conductor编排
│   ├── code-quality-evaluator.md    # 跨层 代码质量评估
│   └── perspectives-implementation.md # 跨层 已实现视角模板
│
├── research/                        # 调研与探索
│   ├── insights/                    # 产品/竞品/生态/架构洞察
│   ├── harness-engineering/         # Harness Engineering文章拆解
│   └── orient-report.md             # 研究Agent MVP能力评估
│
└── engineering/                     # 工程参考
    ├── frontend-layout-stability.md
    ├── performance-optimization-ragservice.md
    └── quick-start-advanced.md
```

---

## 阅读路径

### 入门（5分钟）

1. `core-beliefs.md` — 理解工作信念和优先级
2. `CLDFlow-invariants.md` — 理解硬性边界
3. `CLDFlow-architecture.md` — 看业务流程图，理解五层流转

### 实现某层功能

1. 先看 `CLDFlow-architecture.md` 对应层的职责和接口契约
2. 再看 `cldflow/` 下对应层的详细设计
3. 查 `CLDFlow-defaults.md` 确认可调参数

### 调研参考

`research/insights/` 下的文档是历史调研，结论已吸收到核心文档中，仅作参考。

---

*最后更新：2026-04-15*
