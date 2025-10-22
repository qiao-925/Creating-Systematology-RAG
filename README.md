# 系统科学知识库 RAG 应用

基于 LlamaIndex 和 DeepSeek API 构建的系统科学领域知识问答系统，支持引用溯源和多轮对话。

## ✨ 核心特性

- 🎯 **引用溯源**：每个回答都标注具体的来源文档和段落
- 💬 **多轮对话**：支持上下文追问，智能理解对话历史
- 📚 **多数据源**：支持 Markdown 文件、网页内容和 GitHub 仓库
- 🌐 **维基百科增强**：自动补充背景知识，智能触发，分区展示来源
- 💾 **自动持久化**：会话自动保存，刷新页面后恢复对话历史
- 📜 **历史会话**：侧边栏显示历史会话列表，一键加载恢复
- 👤 **用户隔离**：每个用户独立的知识库和会话数据
- 📊 **行为追踪**：记录用户操作日志，支持数据分析
- 🔍 **RAG可观测性**：集成Phoenix和LlamaDebugHandler，实时追踪检索和生成流程
- 🚀 **简洁界面**：基于 Streamlit 的现代化 Web 界面
- 🔧 **灵活配置**：支持本地 embedding 模型和 API 切换

## 🛠️ 技术栈

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

## 🚀 快速开始

### 一、环境准备

#### 1. 克隆项目

```bash
git clone <repository-url>
cd Creating-Systematology-RAG
```

#### 2. 系统要求

- **Git**: 用于克隆GitHub仓库（首次加载和增量更新）
  ```bash
  # 检查是否安装
  git --version
  
  # 如未安装（Ubuntu/Debian）
  sudo apt install git
  
  # 如未安装（macOS）
  brew install git
  ```

#### 3. 配置 API 密钥

复制并编辑环境变量文件：

```bash
cp env.template .env
# 编辑 .env 文件，添加你的 DeepSeek API 密钥
# DEEPSEEK_API_KEY=your_api_key_here
```


#### 4. 一键安装和启动

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

## 🚀 在线部署

### Zeabur 一键部署（推荐）

[![Deploy on Zeabur](https://zeabur.com/button.svg)](https://zeabur.com/templates)

点击按钮，按提示配置 `DEEPSEEK_API_KEY`，即可完成部署。

详见：[部署指南](docs/DEPLOYMENT.md)

### Railway 一键部署（备选）

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

---

**注意**：
- 首次启动需下载 Embedding 模型（约 5-10 分钟）
- 演示版本数据不持久化，重启后会丢失

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

# 从 GitHub 仓库导入（本地克隆方式）
python main.py import-github microsoft TypeScript --branch main
python main.py import-github yourorg yourrepo --token YOUR_GITHUB_TOKEN

# 注：GitHub仓库会被克隆到 data/github_repos/ 目录
# 后续更新使用 git pull 增量同步，速度更快
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
make test         # 运行所有测试（158个测试用例）
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

# HuggingFace 镜像配置（解决国内网络访问慢的问题）
HF_ENDPOINT=https://hf-mirror.com     # 国内镜像加速，默认启用
HF_OFFLINE_MODE=false                  # 离线模式（强制使用本地缓存）

# 索引参数
CHUNK_SIZE=512
CHUNK_OVERLAP=50
SIMILARITY_TOP_K=3
```

### 🌐 HuggingFace 模型加载配置

#### `HF_ENDPOINT` - 镜像加速

**功能**：配置 HuggingFace 模型下载镜像，解决国内访问 huggingface.co 超时问题。

**可选值**：
- `https://hf-mirror.com` （默认，推荐）- HF-Mirror 国内镜像
- `https://www.modelscope.cn/models` - ModelScope 镜像
- 留空 - 使用官方地址 huggingface.co（国内较慢）

**工作原理**：
- 首次运行时，从配置的镜像下载模型到本地缓存 `~/.cache/huggingface/`
- 后续运行直接从本地缓存加载，无需联网
- 即使需要联网检查更新，也会访问镜像地址（速度快）

#### `HF_OFFLINE_MODE` - 离线模式

**功能**：强制仅使用本地缓存，完全不联网。

**可选值**：
- `false` （默认）- 在线模式，优先使用缓存，必要时联网
- `true` - 离线模式，仅使用本地缓存

**行为说明**：
- `true` + 本地有缓存 = ✅ 正常加载，完全离线
- `true` + 本地无缓存 = ⚠️ 自动切换到在线模式并警告（下载后可离线）
- `false` = 正常在线模式（推荐）

#### 查看模型状态

在 Web 界面底部点击 "🔧 Embedding 模型状态" 可查看：
- ✅ 模型是否已加载到内存
- 💾 本地缓存是否存在
- 🌐 当前使用的镜像地址
- 📴 离线模式是否启用

## 🔧 高级功能

### 开发模式热加载 🔥

**适用场景**：开发调试时，无需频繁重启应用

**功能说明**：
- ✅ 修改 `app.py` → 点击浏览器"Rerun"即可生效
- ✅ 修改 `src/` 模块（如 `chat_manager.py`、`data_loader.py` 等）→ 点击"Rerun"即可生效
- ✅ **默认已启用**，无需配置

**使用方法**：
1. 启动应用：`streamlit run app.py`
2. 修改任意 Python 文件（`app.py` 或 `src/*.py`）
3. 保存文件
4. 浏览器会提示 "Source file changed"
5. **点击 "Rerun" 按钮或按 `R` 键**
6. ✨ 代码更新立即生效，无需重启！

**开发模式标识**：
- 开发模式下，页面标题下方会显示 "🔧 开发模式（热加载已启用）"

**配置切换**（可选）：
```env
# .env 文件
DEV_MODE=true   # 开发模式（默认）- 支持热加载
DEV_MODE=false  # 生产模式 - 性能更好，但需重启才能更新代码
```

> 💡 **提示**：生产环境部署时建议设置 `DEV_MODE=false` 以获得更好的性能

---

### 切换 Embedding 模型

编辑 `.env` 文件：

```env
# 使用其他本地模型
EMBEDDING_MODEL=moka-ai/m3e-base

# 或切换到 API（需修改代码）
```

### 自定义分块策略

调整 `CHUNK_SIZE` 和 `CHUNK_OVERLAP` 参数。

### 维基百科知识增强 🌐

**功能概述**：
- 当本地知识库结果不足时，自动从维基百科补充背景知识
- 支持中英文维基百科自动切换
- 分区展示本地和维基百科来源，便于溯源

**使用方法**：

1. **启用功能**（默认已启用）
```env
# .env 文件
ENABLE_WIKIPEDIA=true
WIKIPEDIA_THRESHOLD=0.6  # 触发阈值（0-1）
WIKIPEDIA_MAX_RESULTS=2  # 最多返回结果数
```

2. **预索引核心概念**（可选，提升速度）
- 在 Web 界面侧边栏找到"🌐 维基百科增强"
- 输入核心概念（如：系统科学、钱学森、控制论）
- 选择语言（中文/English）
- 点击"📖 预索引维基百科"

3. **查询时自动触发**
   - 本地结果相关度 < 阈值时自动触发
   - 或查询中包含"维基百科"、"wikipedia"等关键词

**查询结果展示**：
```
💬 回答
综合本地知识库和维基百科的答案...

📚 本地知识库来源 (2)
[1] 钱学森生平 | 📁 钱学森生平.md | 相似度: 0.85
[2] 系统工程概述 | 📁 系统工程概述.md | 相似度: 0.72

🌐 维基百科补充 (1)
[W1] 钱学森 | 🔗 https://zh.wikipedia.org/wiki/钱学森 | 相似度: 0.68
```

**配置选项**：
```env
# 维基百科配置
ENABLE_WIKIPEDIA=true              # 是否启用
WIKIPEDIA_AUTO_LANG=true           # 自动检测语言
WIKIPEDIA_THRESHOLD=0.6            # 触发阈值
WIKIPEDIA_MAX_RESULTS=2            # 最多结果数
WIKIPEDIA_PRELOAD_CONCEPTS=系统科学,钱学森,系统工程,控制论,信息论,复杂系统
```

**工作原理**：
1. 用户提问 → 检索本地知识库
2. 判断是否需要维基百科补充（相关度 < 阈值）
3. 提取关键词 → 查询维基百科
4. 合并本地和维基百科答案
5. 分区展示来源（本地 vs 维基百科）

### 会话管理

**自动持久化**：
- 每次对话后自动保存，无需手动操作
- 刷新页面后自动恢复最近会话
- 会话按用户分类存储在 `sessions/{user_email}/` 目录

**历史会话**：
- 侧边栏显示最近10个会话
- 显示对话轮数、时间、首问题摘要
- 一键加载恢复任意历史会话
- 活跃会话标记（🟢）

**行为日志**：
- 记录用户所有操作（登录、查询、会话、文档上传等）
- 日志存储在 `logs/activity/{user_email}/activity.jsonl`
- 支持数据分析和审计

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

## 🔍 RAG可观测性与调试

### Phoenix可视化平台（推荐）

Phoenix是开源的LLM可观测性平台，专为RAG系统设计：

**启动方式**：
1. 在Web界面侧边栏点击 "🔍 调试模式" → "📊 Phoenix可视化平台"
2. 点击"🚀 启动Phoenix UI"
3. 访问 `http://localhost:6006` 查看可视化界面

**功能特性**：
- 📊 **实时追踪**：查看完整的RAG查询流程（检索→上下文构建→生成）
- 🔍 **向量可视化**：探索embedding空间，理解检索机制
- 📈 **性能分析**：统计检索时间、LLM调用时间、相似度分布
- 🐛 **问题诊断**：定位检索失败、生成质量等问题

### LlamaDebugHandler调试

轻量级的控制台调试工具：

**启用方式**：
在侧边栏 "🔍 调试模式" → "🐛 LlamaDebugHandler调试" 中勾选"启用调试日志"

**输出内容**：
- LLM调用的完整prompt和响应
- 检索到的所有chunk和相似度分数
- 内部事件和执行流程

调试日志会输出到：
- 控制台（运行streamlit的终端）
- 日志文件（`logs/YYYY-MM-DD.log`）

### 查询追踪信息

收集每次查询的详细指标：

**启用方式**：
在侧边栏 "🔍 调试模式" → "📈 查询追踪信息" 中勾选"启用追踪信息收集"

**显示内容**：
- ⏱️ 各环节耗时（检索、生成）
- 📊 相似度分数统计
- 📝 召回的chunk数量和内容

### 使用建议

1. **日常开发**：使用LlamaDebugHandler快速查看日志
2. **深度调试**：启动Phoenix进行可视化分析
3. **性能优化**：开启追踪信息收集关键指标
4. **问题诊断**：结合Phoenix和日志定位问题

## 📄 许可

本项目采用 MIT 许可证。

## 💡 致谢

本项目的知识库聚焦于钱学森先生的系统学思想和系统科学领域，向这位伟大的科学家致敬！

---

**注意**：首次运行时会下载 embedding 模型（约 400MB），请耐心等待
