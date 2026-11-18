# Systematology MVP 子计划索引

> 原单一计划已拆分为 4 个按交付物组织的子计划。4 个相加 = 原计划完整范围。

## 子计划清单

| # | 子计划 | 文件 | 范围 | 关键产出 |
|---|--------|------|------|----------|
| A | 后端 Pipeline | [A-后端-Pipeline.md](A-后端-Pipeline.md) | 数据模型 + 输入 + CLD + FCM/D2D + 编排 + 报告 + API | models.py / cld/ / fcm/ / d2d/ / api.py |
| B | 前端 Demo | [B-前端-Demo.md](B-前端-Demo.md) | Next.js UI + Systematology 组件 + API 对接 | web/ |
| C | 测试体系 | [C-测试体系.md](C-测试体系.md) | 黄金样例 + 单测 + 集成 + 覆盖率 | tests/ |
| D | 部署与文档 | [D-部署与文档.md](D-部署与文档.md) | Dockerfile + HF Spaces + README + ARCHITECTURE | Dockerfile / start.sh / docs |

## 执行逻辑

```
A（后端）──→ 核心产品，其他全部依赖
B（前端）──→ 可与 A 并行，API 接口对齐即可
C（测试）──→ 可与 A/B 并行，A 完成后跑集成测试
D（部署）──→ A/B/C 全部完成后统一部署验证
```

4 个子计划可由不同人/Agent 并行推进，最终在 D 阶段汇合。

## 校验

```bash
# 全量校验（30 项）
bash docs/Systematology\ MVP\ Builder/tracks/verify-all.sh

# 可发布性门禁
bash docs/Systematology\ MVP\ Builder/tracks/verify-release.sh
```

## 归档

原始完整计划：`../Systematology-MVP-plan.md`
