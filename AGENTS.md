# AGENTS.md

此文档用于构建执行 Agent 的全局地图理解。

## 文档地图

```
ARCHITECTURE.md                   ← 架构设计（工作流 + 技术栈 + 目录结构 + 数据统计）
README.md                         ← 项目说明 + 快速开始 + CLDFlow 使用指南
AGENTS.md                         ← 本文件：Agent 全局地图

docs/
├── CLDFlow-MVP-plan.md           ← CLDFlow 可执行计划书（T1-T20 + G1-G8，全部完成）
├── CLDFlow-MVP-review.md         ← CLDFlow MVP 审查报告
├── CONFIG_SETUP.md               ← 配置管理指南（gh token 同步 + .env 说明）
├── KeyDecision-list.md           ← 关键决策记录（D1-D12）
└── research with brainstorm/     ← 研究与头脑风暴材料（论文 + 架构设计）
```
## Current Focus
构建可发布的mvp版本
迁移旧应用
- 前端实现，使用react改造 ✅（Streamlit 前端已删除）
- 后端实现迁移：先更新一下架构文档中的技术栈并做决策，再迁移老代码到新结构中
- 测试体系
- 文档更新整理
  - 核心文档设计
  - 存档和记录 C:\Users\nonep\Desktop\Creating-Systematology-RAG\.agent\runtime\working-memory-boost.md 
    - 更新动作的checkpoint和路线演进图，checkpoint更微观，路线图更宏观
- 统一性监测
- 对今天的会话操作做一个统计和总结

## 后续迭代计划

-  加州32号法案 作为系统动力学研究demo
- 工作流优化
  - 计划的生命周期管理
    - 目标定义
    - 执行进度
    - 执行日志，关键checkpoint，强化可观测性
    - 决策日志
    - 任务列表
    - 变更统计
    - review建议
    - 完成存档
  - 参考：C:\Users\nonep\Desktop\Creating-Systematology-RAG\.agent\runtime\working-memory-boost.md
