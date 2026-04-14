# FCM层 - 多专家权重聚合

> 架构概览见：`docs/CLDFlow-architecture.md` FCM层
> 默认参数见：`docs/CLDFlow-defaults.md` FCM层

---

## Phase 1：简单均值聚合

```python
final_weight = np.mean(weights)
```

**理由**：Phase 1无历史数据，所有Agent平等，加权无依据。

---

## Phase 2：贝叶斯分布估计

从点估计升级为分布估计，用权重分歧推断不确定性。

---

## 其他方案（未采用）

| 方案 | 优点 | 不采用理由 |
|------|------|-----------|
| 加权平均 | 考虑专家可信度 | Phase 1无可信度数据 |
| 中位数 | 稳健，抗异常值 | 3个Agent时中位数=中间值，信息损失 |
| Dempster-Shafer | 处理不确定性 | 复杂度高，Phase 1不需要 |

---

*整合自 issue-15-sub_docs: 15-fcm-aggregation.md*
