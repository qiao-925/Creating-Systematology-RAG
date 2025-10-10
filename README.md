# 系统科学知识库 RAG 应用

基于 LlamaIndex 和 DeepSeek API 构建的系统科学领域知识问答系统，支持引用溯源和多轮对话。

## ✨ 核心特性

- 🎯 **引用溯源**：每个回答都标注具体的来源文档和段落
- 💬 **多轮对话**：支持上下文追问，智能理解对话历史
- 📚 **多数据源**：支持 Markdown 文件、网页内容和 GitHub 仓库
- 🚀 **简洁界面**：基于 Streamlit 的现代化 Web 界面
- 🔧 **灵活配置**：支持本地 embedding 模型和 API 切换

## 🛠️ 技术栈

- **Python 3.12+** - 编程语言
- **uv** - 依赖管理
- **LlamaIndex** - RAG 框架
- **DeepSeek API** - 大语言模型
- **Chroma** - 向量数据库
- **Streamlit** - Web 界面
- **HuggingFace Embeddings** - 本地向量模型
- **pytest** - 测试框架（88个测试用例）

## 🚀 快速开始

### 一、环境准备

#### 1. 克隆项目

```bash
git clone <repository-url>
cd Creating-Systematology-RAG
```

#### 2. 配置 API 密钥

复制并编辑环境变量文件：

```bash
cp env.template .env
# 编辑 .env 文件，添加你的 DeepSeek API 密钥
# DEEPSEEK_API_KEY=your_api_key_here

# 可选：如需从 GitHub 私有仓库导入
# GITHUB_TOKEN=your_github_token_here
```

> 💡 **提示**: DEEPSEEK_API_KEY 是必需的，GITHUB_TOKEN 仅在访问私有仓库时需要

#### 3. 一键安装和启动

```bash
make              # 安装依赖 + 运行测试（验证环境）
make run          # 启动 Web 应用
```

> **Windows 用户**: 需先安装 Make 工具 → `choco install make -y` ([安装 Chocolatey](https://chocolatey.org/install))

---

### 二、使用 Makefile（推荐）

**查看所有命令**：
```bash
make help
```

**常用命令**：
```bash
make install      # 安装依赖
make test         # 运行所有测试
make test-fast    # 快速测试
make test-cov     # 测试+覆盖率报告
make run          # 启动 Web 应用
make clean        # 清理生成文件
```

**完整工作流**：
```bash
make              # = make install + make test（推荐首次运行）
make start        # = make + make run（一键启动）
```

---

### 三、使用方式

#### 方式 A：Web 界面（推荐）⭐

```bash
make run
# 或直接运行
streamlit run app.py
```

在浏览器打开 `http://localhost:8501`，即可使用！

**功能**：
- 📤 上传文档或从目录加载
- 💬 多轮对话
- 📚 查看引用来源

#### 方式 B：命令行工具

**导入文档**：

```bash
# 从目录导入
python main.py import-docs ./data/raw --recursive

# 从 URL 导入
python main.py import-urls https://example.com/article1 https://example.com/article2

# 从 GitHub 仓库导入
python main.py import-github microsoft TypeScript --branch main
python main.py import-github yourorg yourrepo --token YOUR_GITHUB_TOKEN
```

**单次查询**：
```bash
python main.py query "什么是系统科学？"
```

**交互式对话**：
```bash
python main.py chat --show-sources
```

**查看索引统计**：
```bash
python main.py stats
```

---

### 四、示例数据

项目包含示例文档（`data/raw/` 目录）：

- `系统科学基础/` - 系统科学基础知识
- `钱学森-创建系统学/` - 钱学森的系统学理论
- `论系统工程/` - 系统工程相关内容

可直接加载开始测试！

---

### 五、测试

```bash
make test         # 运行所有测试（88个测试用例）
make test-fast    # 快速测试
make test-cov     # 查看覆盖率报告
```

详见 [测试使用指南](tests/README.md)

---

## 🎯 使用场景

### 场景 1：深化系统科学理解

上传系统科学相关书籍和论文，通过对话深入理解概念和理论。

### 场景 2：文献研究助手

快速检索大量文献中的相关内容，并查看原始出处。

### 场景 3：知识整合

将分散的知识资料整合，通过对话获得综合性的理解。

## 📁 项目结构

```
Creating-Systematology-RAG/
├── src/                    # 源代码
│   ├── config.py          # 配置管理
│   ├── data_loader.py     # 数据加载器
│   ├── indexer.py         # 索引构建
│   ├── query_engine.py    # 查询引擎
│   └── chat_manager.py    # 对话管理
├── data/                   # 数据目录
│   ├── raw/               # 原始文档
│   └── processed/         # 处理后数据
├── vector_store/          # Chroma 向量数据库
├── sessions/              # 会话记录
├── docs/                  # 项目文档
│   └── DECISIONS.md       # 技术决策记录
├── app.py                 # Streamlit 应用
├── main.py                # CLI 工具
├── CHANGELOG.md           # 开发日志
├── TODO.md                # 待办事项
└── README.md              # 本文件
```

## ⚙️ 配置说明

主要配置项（在 `.env` 文件中设置）：

```env
# DeepSeek API
DEEPSEEK_API_KEY=your_key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# Embedding 模型
EMBEDDING_MODEL=BAAI/bge-base-zh-v1.5

# 索引参数
CHUNK_SIZE=512
CHUNK_OVERLAP=50
SIMILARITY_TOP_K=3
```

## 🔧 高级功能

### 切换 Embedding 模型

编辑 `.env` 文件：

```env
# 使用其他本地模型
EMBEDDING_MODEL=moka-ai/m3e-base

# 或切换到 API（需修改代码）
```

### 自定义分块策略

调整 `CHUNK_SIZE` 和 `CHUNK_OVERLAP` 参数。

### 会话管理

会话自动保存在 `sessions/` 目录，可以加载历史会话继续对话。

## 📚 文档

### 核心文档
- [README.md](README.md) - 本文件，项目概览和使用指南
- [文档中心](docs/README.md) - 完整的文档导航（按角色、主题、关键词查找）⭐

### 技术文档
- [架构设计](docs/ARCHITECTURE.md) - 系统架构和设计思路 ⭐
- [API参考](docs/API.md) - 完整的API接口文档
- [技术决策](docs/DECISIONS.md) - 技术选型的原因和考量

### 项目管理
- [开发日志](docs/CHANGELOG.md) - 项目进展记录
- [项目结构](docs/PROJECT_STRUCTURE.md) - 目录和文件组织说明

### 测试文档
- [测试使用指南](tests/README.md) - 完整的测试体系和使用方法

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可

本项目采用 MIT 许可证。

## 💡 致谢

本项目的知识库聚焦于钱学森先生的系统学思想和系统科学领域，向这位伟大的科学家致敬！

---

**注意**：首次运行时会下载 embedding 模型（约 400MB），请耐心等待
