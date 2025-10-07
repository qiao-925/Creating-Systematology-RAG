# 项目结构说明

> 详细的目录和文件组织说明

## 📁 完整项目结构

```
Creating-Systematology-RAG/
│
├── README.md                       # 📖 项目主文档（项目概览、功能介绍、使用指南）
├── env.template                    # 🔐 环境变量模板（API密钥配置示例）
├── pyproject.toml                  # 📦 Python项目配置（依赖管理）
├── uv.lock                         # 🔒 依赖锁定文件（uv生成）
├── .python-version                 # 🐍 Python版本指定
│
├── app.py                          # 🖥️ Streamlit Web应用（用户界面）
├── main.py                         # ⌨️ CLI命令行工具（批量操作、管理）
├── streamlit-test.py              # 🧪 Streamlit测试文件
│
├── docs/                          # 📚 文档中心
│   ├── README.md                  # 📖 文档中心首页
│   ├── INDEX.md                   # 🗂️ 文档索引和导航
│   │
│   ├── QUICKSTART.md              # 🚀 快速开始指南（5分钟上手）
│   ├── ARCHITECTURE.md            # 🏗️ 架构设计文档（系统架构、设计思路）
│   ├── DEVELOPER_GUIDE.md         # 👨‍💻 开发者指南（代码详解、开发任务）
│   ├── API.md                     # 📚 API参考文档（接口文档）
│   ├── PROJECT_STRUCTURE.md       # 📁 项目结构说明（本文件）
│   │
│   ├── DECISIONS.md               # 💡 技术决策记录（ADR）
│   ├── CHANGELOG.md               # 📋 开发日志（变更记录）
│   └── TODO.md                    # ✅ 待办事项（未来计划）
│
├── src/                           # 💻 源代码（核心业务逻辑）
│   ├── __init__.py                # 📦 包初始化文件
│   ├── config.py                  # ⚙️ 配置管理（环境变量、参数）
│   ├── data_loader.py             # 📥 数据加载（Markdown、网页）
│   ├── indexer.py                 # 🗂️ 索引构建（向量化、存储）
│   ├── query_engine.py            # 🔍 查询引擎（问答、引用溯源）
│   └── chat_manager.py            # 💬 对话管理（多轮对话、会话）
│
├── data/                          # 📁 数据目录
│   ├── raw/                       # 📄 原始文档存储
│   │   ├── 系统科学基础/          # 系统科学基础知识
│   │   │   └── 系统科学简介.md
│   │   ├── 钱学森-创建系统学/     # 钱学森系统学理论
│   │   │   ├── 钱学森生平.md
│   │   │   └── 开放的复杂巨系统理论.md
│   │   └── 论系统工程/            # 系统工程方法
│   │       └── 系统工程概述.md
│   └── processed/                 # 📊 处理后的数据
│
├── vector_store/                  # 🗄️ Chroma向量数据库
│   └── chroma.sqlite3             # SQLite数据库文件（自动生成）
│
├── sessions/                      # 💾 对话会话记录（自动生成）
│   └── session_*.json             # 会话文件
│
├── .git/                          # 🔧 Git版本控制
├── .gitignore                     # 🚫 Git忽略文件
└── .idea/                         # 💡 IDE配置（PyCharm/IDEA）
```

---

## 📂 目录详细说明

### 根目录文件

| 文件 | 用途 | 是否必需 |
|------|------|---------|
| `README.md` | 项目主文档，包含项目介绍、安装、使用说明 | ✅ 必需 |
| `app.py` | Streamlit Web应用主文件 | ✅ 必需 |
| `main.py` | CLI命令行工具 | ✅ 必需 |
| `pyproject.toml` | Python项目配置文件，定义依赖 | ✅ 必需 |
| `uv.lock` | 依赖锁定文件，确保环境一致性 | ✅ 必需 |
| `env.template` | 环境变量模板，需复制为`.env`使用 | ✅ 必需 |
| `.python-version` | 指定Python版本（3.12+） | 推荐 |
| `streamlit-test.py` | Streamlit测试文件 | 可选 |

### docs/ - 文档中心

完整的项目文档，包括：

**核心技术文档**（必读）：
- `ARCHITECTURE.md` - 系统架构和设计思路 ⭐
- `DEVELOPER_GUIDE.md` - 详细的代码说明和开发指南 ⭐
- `API.md` - 完整的API接口文档

**用户文档**：
- `QUICKSTART.md` - 5分钟快速上手
- `README.md` - 文档中心首页
- `INDEX.md` - 文档导航和索引

**管理文档**：
- `DECISIONS.md` - 技术决策记录
- `CHANGELOG.md` - 开发日志
- `TODO.md` - 待办事项
- `PROJECT_STRUCTURE.md` - 本文件

### src/ - 源代码

核心业务逻辑模块，采用分层架构：

| 模块 | 职责 | 依赖关系 |
|------|------|---------|
| `config.py` | 配置管理 | 基础模块，无依赖 |
| `data_loader.py` | 数据加载 | 依赖 config |
| `indexer.py` | 索引构建 | 依赖 config, data_loader |
| `query_engine.py` | 查询引擎 | 依赖 config, indexer |
| `chat_manager.py` | 对话管理 | 依赖 config, indexer |

**依赖关系图**：
```
config.py (基础)
    ↓
data_loader.py
    ↓
indexer.py
    ↓
    ├── query_engine.py
    └── chat_manager.py
```

### data/ - 数据目录

**data/raw/**：存放原始文档
- 支持任意深度的子目录
- 当前包含4个示例Markdown文档
- 用户可以添加自己的文档到这里

**data/processed/**：存放处理后的数据
- 自动生成
- 用于缓存处理结果（如果需要）

### vector_store/ - 向量数据库

**Chroma数据库存储目录**：
- `chroma.sqlite3` - SQLite数据库文件
- 存储文档向量和元数据
- 自动创建和管理

**特点**：
- 持久化存储
- 支持增量更新
- 可以删除重建

### sessions/ - 会话记录

**对话会话持久化**：
- 自动创建目录
- 每个会话一个JSON文件
- 格式：`session_YYYYMMDD_HHMMSS.json`

**用途**：
- 保存对话历史
- 恢复会话
- 分析对话记录

---

## 📊 文件统计

### 代码文件

| 类型 | 数量 | 总行数（约） |
|------|------|-------------|
| Python源码 | 6个 | 2,000+ |
| Python应用 | 2个 | 700+ |
| 配置文件 | 2个 | 100+ |
| **合计** | **10个** | **2,800+** |

### 文档文件

| 类型 | 数量 | 总字数（约） |
|------|------|-------------|
| 技术文档 | 4个 | 19,000+ |
| 用户文档 | 3个 | 3,000+ |
| 管理文档 | 3个 | 3,000+ |
| **合计** | **10个** | **25,000+** |

### 示例数据

| 类型 | 数量 |
|------|------|
| Markdown文档 | 4个 |
| 文档分类 | 3个 |

---

## 🔍 文件查找指南

### 我想修改...

| 需求 | 文件位置 |
|------|---------|
| **配置参数** | `src/config.py` 或 `.env` |
| **添加新数据源** | `src/data_loader.py` |
| **修改索引逻辑** | `src/indexer.py` |
| **调整查询行为** | `src/query_engine.py` |
| **改进对话功能** | `src/chat_manager.py` |
| **修改Web界面** | `app.py` |
| **修改CLI命令** | `main.py` |
| **更新文档** | `docs/` 目录 |

### 我想查看...

| 需求 | 文件位置 |
|------|---------|
| **如何使用** | `README.md` |
| **快速开始** | `docs/QUICKSTART.md` |
| **系统架构** | `docs/ARCHITECTURE.md` |
| **代码详解** | `docs/DEVELOPER_GUIDE.md` |
| **API接口** | `docs/API.md` |
| **技术选型原因** | `docs/DECISIONS.md` |
| **项目进展** | `docs/CHANGELOG.md` |
| **未来计划** | `docs/TODO.md` |

---

## 🎯 目录设计原则

### 1. 关注点分离
- **源码** (`src/`) - 业务逻辑
- **应用** (`app.py`, `main.py`) - 用户界面
- **文档** (`docs/`) - 说明文档
- **数据** (`data/`) - 原始和处理数据
- **存储** (`vector_store/`, `sessions/`) - 持久化数据

### 2. 模块化
- 每个模块职责单一
- 清晰的依赖关系
- 易于测试和维护

### 3. 可扩展性
- 添加新模块：在 `src/` 目录创建新文件
- 添加新数据源：扩展 `data_loader.py`
- 添加新命令：扩展 `main.py`

### 4. 约定优于配置
- 配置文件在根目录
- 源码在 `src/`
- 文档在 `docs/`
- 数据在 `data/`

---

## 🔧 自动生成的文件/目录

以下文件和目录会在运行时自动创建，无需手动创建：

### 运行时生成

| 路径 | 生成时机 | 说明 |
|------|---------|------|
| `.env` | 用户首次配置时 | 从 `env.template` 复制 |
| `vector_store/` | 首次构建索引时 | Chroma数据库目录 |
| `sessions/` | 首次保存会话时 | 对话记录目录 |
| `data/processed/` | 处理数据时 | 处理后数据缓存 |

### Python生成

| 路径 | 生成时机 | 说明 |
|------|---------|------|
| `__pycache__/` | 运行Python代码时 | Python字节码缓存 |
| `*.pyc` | 运行Python代码时 | 编译后的Python文件 |

### 依赖工具生成

| 路径 | 工具 | 说明 |
|------|------|------|
| `uv.lock` | uv | 依赖锁定文件 |
| `.venv/` | uv/pip | 虚拟环境（如使用） |

---

## 🚫 忽略的文件

`.gitignore` 配置忽略以下内容：

```gitignore
# Python
__pycache__/
*.py[cod]
*.so
.Python

# 虚拟环境
venv/
.venv/
env/

# IDE
.idea/
.vscode/
*.swp

# 环境变量
.env

# 数据
vector_store/
sessions/
data/processed/

# 系统
.DS_Store
Thumbs.db
```

---

## 📝 目录使用建议

### 开发时

1. **源码修改**：只修改 `src/` 目录下的文件
2. **文档更新**：修改 `docs/` 目录下的对应文档
3. **测试数据**：在 `data/raw/` 添加测试文档
4. **配置调整**：修改 `.env` 文件，不要修改 `env.template`

### 部署时

1. **必需文件**：
   - 所有 Python 源码
   - `pyproject.toml` 和 `uv.lock`
   - `env.template`（用户需要配置）
   - `README.md`

2. **可选文件**：
   - `docs/` - 文档（建议包含）
   - `data/raw/` - 示例数据
   - `streamlit-test.py` - 测试文件

3. **不需要的**：
   - `vector_store/` - 运行时生成
   - `sessions/` - 运行时生成
   - `.env` - 用户配置
   - `__pycache__/` - Python缓存

### 备份时

**建议备份**：
- 所有源码和配置
- 所有文档
- 原始数据（`data/raw/`）
- 重要的会话记录（`sessions/`）

**可以不备份**：
- `vector_store/` - 可以重建
- `__pycache__/` - 自动生成
- `.venv/` - 可以重建

---

## 🔄 目录演进

### 当前版本（v0.1.0）

完整的MVP版本，包含所有核心功能和完善的文档。

### 可能的扩展

未来可能添加的目录/文件：

```
tests/              # 单元测试
├── test_config.py
├── test_data_loader.py
└── ...

scripts/            # 工具脚本
├── backup.sh
├── deploy.sh
└── ...

logs/               # 日志文件
└── app.log

docker/             # Docker配置
├── Dockerfile
└── docker-compose.yml

examples/           # 示例代码
├── basic_usage.py
└── advanced_usage.py
```

---

## 📖 相关文档

- [README.md](../README.md) - 项目概览
- [架构设计](ARCHITECTURE.md) - 系统架构详解
- [开发者指南](DEVELOPER_GUIDE.md) - 开发说明
- [文档导航](INDEX.md) - 所有文档索引

---

**最后更新**: 2025-10-07

**维护者**: 项目团队

如有任何关于项目结构的问题，欢迎查看相关文档或提交Issue！

