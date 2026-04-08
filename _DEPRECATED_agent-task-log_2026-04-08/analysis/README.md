# Agent Task Log 分析

> 从 agent-task-log 中提取洞察的数据分析集合

---

## 1. 目录结构

```
analysis/
├── README.md           # 本文件
├── reports/           # 生成的分析报告
│   ├── bugs/         # Bug 分析报告
│   ├── tasks/        # 任务统计报告
│   └── debt/         # 技术债务报告
└── configs/          # 分析配置（如果需要）
```

---

## 2. 可用分析

### 2.1 Bug 健康度分析

**脚本**: `scripts/analyze_bugs.py`

**功能**:
- Bug 数量趋势（月度统计）
- 高频问题模块识别
- Bug 根因分类
- 自我审视建议

**使用方式**:
```bash
# 分析全部 bug
python scripts/analyze_bugs.py

# 分析指定月份
python scripts/analyze_bugs.py --month 2026-01

# 指定输出路径
python scripts/analyze_bugs.py --output agent-task-log/analysis/reports/bugs/2026-01.md
```

---

## 3. 设计原则

### 3.1 聚焦价值

- **不追求大而全**：只实现能产生实际改进的分析
- **行动导向**：分析结果必须能转化为具体行动
- **渐进式扩展**：从最有价值的维度开始，验证后再扩展

### 3.2 数据驱动自我迭代

- **定期回顾**：建议每月生成一次报告
- **趋势跟踪**：关注指标变化，而非绝对值
- **持续改进**：根据分析结果调整开发习惯和规则

---

## 4. 扩展计划（待实现）

### 4.1 技术债务看板
- 从优化分析中提取 ⚠️ 改进建议
- 按优先级（🔴/🟡/🟢）分类统计
- 追踪债务解决状态

### 4.2 任务统计
- 任务类型时间占比
- 月度工作节奏
- 单任务耗时分布

### 4.3 Aha-moment 洞察引擎
- Aha-moment 与任务类型的关联
- 主题聚类分析

---

## 5. 维护说明

- 分析脚本统一放在 `scripts/` 目录
- 生成的报告存放在 `analysis/reports/` 下
- 按照类型（bugs/tasks/debt）分子目录
- 报告文件命名：`YYYY-MM.md`

---

**最后更新**: 2026-01-22
