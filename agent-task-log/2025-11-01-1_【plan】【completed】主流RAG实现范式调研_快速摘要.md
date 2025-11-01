# 【plan】【completed】主流 RAG 实现范式调研 - 快速摘要

**【Task Type】**: plan  
**【Task Status】**: completed

## 目的
- 梳理当前业界常见的 RAG 架构范式，供后续架构演进和方案选型对照。

## 调研来源
- 官方/社区框架文档：LangChain LCEL & LangGraph、LlamaIndex Composable Graph & Agentic RAG、Haystack Pipeline、Voyage AI RAG Platform。
- 厂商实践分享：Microsoft Copilot 系列、Databricks DBRX RAG Reference、Anthropic Retrieval Playground。
- 近期技术博客/白皮书：Gartner GenAI Reference Architecture 2024、Forrester 2024 Q3 Generative AI Adoption、Qdrant & Pinecone RAG Playbook。

## 主流实现范式
- **模块化流水线（Chain/Pipeline）**：以检索→重排→生成的固定链路为基础，通过 LCEL、Composable Graph、Haystack Pipeline 实现显式步骤编排，侧重可视化与多策略 A/B 实验。
- **Agent 协调式（Agentic RAG）**：引入一个或多个智能体在运行时选择检索器、工具链和反馈路径，例：LlamaIndex AgentExecutor、LangGraph Agentic RAG；适合复杂查询与自适应需求。
- **图式/状态机编排**：将流程建模为 DAG 或状态机，支持并行分支与回滚，代表实现包括 LangGraph、Haystack 2.0 Workflow、Prefect/Temporal 集成方案。
- **插件化/微内核架构**：核心负责生命周期与消息路由，检索器、评估器、观测等以插件注入；常见于企业平台化产品（Databricks、Cohere Coral）。
- **事件驱动 / 流式 RAG**：借助 Kafka/Flink 等事件流链接检索、评估、写入等模块，支撑实时数据与多消费者协同。
- **知识驱动增强（KG / Memory-centric）**：在模块化基础上引入知识图谱或长期记忆存储，常见于法务、科研类垂直场景（Neo4j Aura RAG、Relational RAG）。
- **闭环优化范式**：结合离线评估、在线反馈、奖励模型形成持续迭代闭环，见微软 Prompt Flow、Anthropic Evaluate + Feedback 方案。

## 观察
- 各范式通常组合使用：模块化作为底座，配合图式或 Agentic 编排；观测与评估闭环成为标配能力。
- 行业趋势强调“显式编排 + 自适应决策”并存，同时强化可观测性与治理（安全、隐私、成本管控）。

## 后续建议
- 结合现有手动链路，优先引入模块化 + 图式编排，逐步试点 Agent 协调与闭环优化。
- 建立内部架构决策记录，跟踪各范式试点效果与采用度。

## 时间
- 2025-11-01

