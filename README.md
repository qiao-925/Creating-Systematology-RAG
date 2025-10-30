# 创建系统学知识库RAG应用 (Creating Systematology RAG Application)

> 面向系统科学领域的智能知识问答系统，整合 LlamaIndex、DeepSeek API 和 Chroma 向量数据库，提供引用溯源、多轮对话、知识增强等功能。

## 1. 功能描述 (Features)

### 核心特性 (Core Features)

**基础功能**
- 🎯 **引用溯源**：每个回答都标注具体的来源文档和段落
- 💬 **多轮对话**：支持上下文追问，智能理解对话历史
- 🚀 **简洁界面**：基于 Streamlit 的现代化 Web 界面

**数据能力**
- 📚 **多数据源**：支持 Markdown 文件、网页内容和 GitHub 仓库
- 🌐 **维基百科增强**：自动补充背景知识，智能触发，分区展示来源

**用户体验**
- 💾 **自动持久化**：会话自动保存，刷新页面后恢复对话历史
- 📜 **历史会话**：侧边栏显示历史会话列表，一键加载恢复
- 👤 **用户隔离**：每个用户独立的知识库和会话数据

**开发调试**
- 📊 **行为追踪**：记录用户操作日志，支持数据分析
- 🔍 **RAG可观测性**：集成Phoenix和LlamaDebugHandler，实时追踪检索和生成流程
- 🔧 **灵活配置**：支持本地 embedding 模型和 API 切换

### 技术栈 (Tech Stack)

- **Python 3.12+** - 编程语言
- **uv** - 依赖管理和包管理
- **LlamaIndex** - RAG 核心框架
- **LangChain** - 文档加载器（GitHub集成）
- **DeepSeek API** - 大语言模型
- **Chroma** - 向量数据库
- **Streamlit** - Web 界面
- **HuggingFace Embeddings** - 本地向量模型（支持镜像和离线）
- **Git** - GitHub仓库本地克隆和增量更新
- **pytest** - 测试框架（158个测试用例）
- **Phoenix** - RAG可观测性平台

---

## 2. 🚀 快速开始 (Quick Start)

### 环境准备 (Environment Setup)

**1. 克隆项目**
```bash
git clone <repository-url>
cd Creating-Systematology-RAG
```

**2. 配置 API 密钥**
```bash
cp env.template .env
# 编辑 .env 文件，添加 DEEPSEEK_API_KEY=your_api_key
```

**3. 安装并启动**
```bash
make              # 安装依赖 + 运行测试（推荐首次运行）
make run          # 启动 Web 应用

# Windows PowerShell用户如果遇到乱码：
.\Makefile.ps1 run   # 使用PowerShell包装脚本（已修复UTF-8编码）

# 其他常用命令
make start        # = make + make run（一键启动）
make help         # 查看所有命令
make test         # 运行所有测试
make clean        # 清理生成文件
```

**GPU加速设置（可选但推荐）**：

项目支持**GPU优先、CPU兜底**模式。由于 `uv` 在 Windows 平台上默认锁定 CPU 版本的 PyTorch，**需要手动安装 CUDA 版本**以获得 GPU 加速：

```bash
# 1. 安装基础依赖（首次运行会自动执行）
make install

# 2. 手动安装 CUDA 版本的 PyTorch（覆盖 CPU 版本）
uv pip install --force-reinstall --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio

# 3. 验证安装
uv run --no-sync python -c "import torch; print(f'版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}')"
```

**性能对比**：
- 🚀 **GPU模式**：索引构建约5分钟
- 🐌 **CPU模式**：索引构建约30分钟+

> 💡 **注意**：
> - 项目可以在纯CPU环境运行，但性能较慢
> - 在 Windows 平台上需要手动安装 GPU 版本以获得最佳性能
> - **安装 CUDA 版本后，避免再次运行 `make install`、`make ready`、`make start` 等会触发 `uv sync` 的命令**（会覆盖 CUDA 版本）
> - 日常使用只需 `make run` 启动应用，已自动配置 `--no-sync` 选项

> 💡 **Windows 用户**：需先安装 Make 工具 → `choco install make -y`  
> 详细安装过程 → [Windows Make 工具安装指南](agent-task-log/2025-10-09-3_Windows-Make工具安装与Makefile配置_快速摘要.md)

---

## 3. 📁 项目结构 (Project Structure)

```
Creating-Systematology-RAG/
│
├── app.py                          # 🖥️ Streamlit Web应用主页（聊天界面）
├── main.py                         # ⌨️ CLI命令行工具（批量操作、管理）
├── pages/                          # 📄 Streamlit多页面应用
│   └── 1_⚙️_设置.py               # ⚙️ 设置页面（详细配置）
│
├── docs/                          # 📚 文档中心
│   ├── README.md                  # 📖 文档中心首页（整合导航）
│   ├── ARCHITECTURE.md            # 🏗️ 架构设计文档
│   ├── API.md                     # 📚 API参考文档
│   ├── DECISIONS.md               # 💡 技术决策记录
│   └── PROJECT_STRUCTURE.md       # 📁 项目结构说明
│
├── src/                           # 💻 源代码（核心业务逻辑）
│   ├── config.py                  # ⚙️ 配置管理
│   ├── data_loader.py             # 📥 数据加载（Markdown、网页、GitHub）
│   ├── indexer.py                 # 🗂️ 索引构建（向量化、存储）
│   ├── query_engine.py            # 🔍 查询引擎（问答、引用溯源）
│   ├── chat_manager.py            # 💬 对话管理（多轮对话、会话）
│   ├── user_manager.py            # 👤 用户管理（注册、登录）
│   ├── phoenix_utils.py           # 🔍 Phoenix工具（RAG可观测性）
│   └── ui_components.py           # 🎨 UI共用组件
│
├── data/                          # 📁 数据目录
│   ├── processed/                 # 📊 处理后的数据
│   └── github_repos/               # 📦 GitHub仓库
│
├── vector_store/                  # 🗄️ Chroma向量数据库
├── sessions/                      # 💾 对话会话记录
├── logs/                          # 📋 日志目录
├── agent-task-log/                # 📝 AI Agent任务记录
│   └── README.md                  # 📖 任务归档
│
└── Makefile                       # 🛠️ 构建脚本
```

> 📖 详细结构 → [项目结构](docs/PROJECT_STRUCTURE.md)

---

## 4. 📚 相关文档 (Related Documents)

### 核心文档

- [📖 文档中心](docs/README.md) - 文档导航和索引
- [📖 架构设计](docs/ARCHITECTURE.md) - 系统架构和设计思路
- [📖 API参考](docs/API.md) - 完整的API接口文档
- [📖 项目结构](docs/PROJECT_STRUCTURE.md) - 详细的目录组织说明
- [📖 项目追踪](docs/TRACKER.md) - 任务管理与进度追踪

### AI Agent 任务记录

- [📖 任务归档](agent-task-log/README.md) - AI Agent 执行任务的完整记录
- [📖 人机协作范式](agent-task-log/人机协作范式.md) - 协作经验总结

---

## 💡 致谢

本项目的知识库聚焦于钱学森先生的系统学思想和系统科学领域，向这位伟大的科学家致敬！

---

**最后更新**: 2025-10-22  
**License**: MIT
