# 1. Workflow

```text
用户输入问题 / 来源材料
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│  1. 输入与增强                                                │
│  业务：把原始问题变成可分析任务                                 │
│  工程：Input Pipeline / 检索 / 解析 / 过滤                    │
│                                                              │
│  - HyDE + 多查询                                               │
│  - 来源分级 T1-T4                                              │
│  - 文档解析、质量过滤、饱和度检测                              │
│  输出：ParsedQuery                                             │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│  2. Lead Agent 编排                                            │
│  业务：决定先做什么、后做什么、哪些分析需要调用                 │
│  工程：LlamaIndex AgentWorkflow + Guardrails                   │
│                                                              │
│  - 持有完整研究上下文                                           │
│  - 先调用 CLD                                                  │
│  - 判断是否需要 FCM / D2D                                      │
│  - 控制预算、超时、重试、终止                                   │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│  3. 前置分析：CLD                                              │
│  业务：提取因果结构，形成共同根                                 │
│  工程：CLD Module（真多 Agent 子系统）                         │
│                                                              │
│  - 视角生成                                                    │
│  - Specialist × N 并行提取                                     │
│  - 节点归并 / 冲突检测                                         │
│  - 裁判 Agent / 自审                                           │
│  输出：SharedCLD                                               │
└──────────────────────────────────────────────────────────────┘
        │
        ├──────────────────────────────────────────────────────┐
        │                                                      │
        ▼                                                      ▼
┌──────────────────────────────┐                 ┌──────────────────────────────┐
│  4A. 衍生分析：FCM            │                 │  4B. 衍生分析：D2D            │
│  业务：半定量场景仿真         │                 │  业务：全定量杠杆点分析       │
│  工程：FCM Module             │                 │  工程：D2D Module             │
│                              │                 │                              │
│  - 单 Agent 批量评级          │                 │  - 扰动分析                   │
│  - 权重映射                   │                 │  - 不确定性计算               │
│  - Kosko 仿真                 │                 │  - 杠杆点排序                 │
│  输出：WeightedFCM            │                 │  输出：LeverageAnalysis       │
└──────────────────────────────┘                 └──────────────────────────────┘
        │                                                      │
        └──────────────────────────────┬───────────────────────┘
                                       ▼
┌──────────────────────────────────────────────────────────────┐
│  5. 结果融合与报告                                              │
│  业务：把多个分析结果整理成可读决策报告                         │
│  工程：Report Assembler / StructuredReport                    │
│                                                              │
│  - 汇总 CLD / FCM / D2D                                        │
│  - 语义融合，不做硬编码数据转换                                 │
│  - 引用来源、输出洞察、给出结论                                 │
│  - 输出内容包括：                                              │
│    1. 因果结构图（CLD 可视化）                                  │
│    2. 场景对比表（FCM 仿真结果，如调用）                       │
│    3. 杠杆点排序（D2D 结果，如调用）                           │
│    4. 综合洞察（Lead Agent 基于完整上下文生成）                │
│    5. 证据追溯（来源 Agent + 原文引用 + 来源层级）             │
│  输出：StructuredReport / StructuredFailureReport             │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
最终结果展示给用户
```

## 2. 目录结构 & Code Map

```
Creating-Systematology-RAG/
│
├── backend/                        # 后端核心（所有后端代码）
│   ├── fastapi/                   #   FastAPI API 层（前端唯一入口）
│   │   ├── main.py                #     应用入口（uvicorn backend.fastapi.main:app）
│   │   ├── deps.py                #     依赖注入
│   │   ├── schemas.py             #     请求/响应模型
│   │   └── routes/                #     路由（config, health）
│   │
│   ├── core/                      #   核心层（按架构图组织）
│   │   ├── input/                 #     ① 输入与增强
│   │   ├── orchestration/         #     ② Lead Agent 编排
│   │   ├── modules/               #     ③ 分析模块
│   │   │   ├── cld/              #       CLD（含 perspectives 视角系统）
│   │   │   ├── fcm/              #       FCM 仿真
│   │   │   └── d2d/              #       D2D 杠杆点分析
│   │   ├── reporting/             #     ④ 结果融合与报告
│   │   ├── models.py              #     核心数据模型
│   │   ├── service.py             #     应用服务层
│   │   ├── api.py                 #     CLDFlow API 路由
│   │   └── guardrails.py          #     守卫函数
│   │
│   ├── infrastructure/             #   基础设施层
│   │   ├── agent/                 #     通用 Agent 原语（从 research_kernel 沉淀）
│   │   ├── retrieval/             #     通用检索（从 rag_engine 沉淀）
│   │   ├── reranking/             #     通用重排序（从 rag_engine 沉淀）
│   │   ├── formatting/            #     通用输出格式化（从 rag_engine 沉淀）
│   │   ├── config/                #     配置管理
│   │   ├── llms/                  #     LLM 工厂（LiteLLM 统一接口）
│   │   ├── embeddings/            #     向量化
│   │   ├── indexer/               #     索引构建（Chroma）
│   │   ├── data_loader/           #     数据加载
│   │   ├── observers/             #     可观测性
│   │   └── initialization/        #     初始化系统
│   │
│   └── prompts/                   #   Prompt 模板
│
├── tests/                          # 测试（保留在根目录）
├── scripts/                        # 运维脚本
├── web/                            # Next.js / React 前端
├── docs/                           # 文档
├── data/                           # 数据目录
│
├── application.yml                 # 应用配置
├── pyproject.toml                  # Python 项目配置
├── Makefile                        # 构建脚本
├── ARCHITECTURE.md                 # 架构设计文档（本文档）
└── README.md                       # 项目说明
```


# 3. 数据统计

> 截至 2026-05-16，含 CLDFlow MVP 全部代码，Streamlit 前端已删除。

## 1. 总体规模

| 维度 | 数量 |
|------|------|
| Git 跟踪文件 | 1117 |
| 后端 Python 文件 | 203（~27,282 行） |
| Next.js/React 前端文件 | 40（~2,941 行） |
| 测试 Python 文件 | 118（~22,675 行） |
| 文档 Markdown 文件 | 105 |
| 总 Python 文件 | 338 |

## 2. 核心功能模块

| 功能领域 | 说明 |
|----------|------|
| RAG 引擎 | 传统 RAG + Agentic RAG，含 formatting/routing/utils |
| CLDFlow | CLD → FCM → D2D 因果分析流水线（34 个 Python 文件） |
| Research Kernel | 研究 Agent 内核（agent, state, tools） |
| 数据加载 | GitHub 同步 + 本地文件导入 |
| 向量化 | HuggingFace Embedding（local + API） |
| 索引构建 | Chroma 向量索引管理 |
| 可观测性 | structlog + LlamaIndex Observers + RAGAS 评估 |

## 3. 测试覆盖

| 类型 | 文件数 |
|------|--------|
| 单元测试 | 58 |
| 集成测试 | 15 |
| 性能测试 | 7 |
| E2E 测试 | 4 |
| 回归测试 | 2 |
| CLDFlow 专用 | 3 |
| 测试夹具 | 9 |
| 测试工具 | 12 |
