# 文档中心

> 欢迎来到系统科学知识库RAG应用的文档中心！快速找到您需要的文档。

## 📚 文档列表

### 核心技术文档

| 文档 | 说明 | 推荐度 |
|------|------|--------|
| [架构设计](ARCHITECTURE.md) | 系统架构、模块设计、数据流程 | ⭐⭐⭐ |
| [API参考](API.md) | 完整的API接口文档 | ⭐⭐ |

### 用户文档

| 文档 | 说明 |
|------|------|
| [快速开始](QUICKSTART.md) | 5分钟快速上手指南 |

### 项目管理

| 文档 | 说明 |
|------|------|
| [项目追踪](TRACKER.md) | 任务管理与进度追踪 |
| [项目结构](PROJECT_STRUCTURE.md) | 目录和文件组织说明 |

---

## 🚀 快速导航

### 我想...

- **理解架构** → [架构设计](ARCHITECTURE.md) ⭐ **强烈推荐**
  - 整体架构图
  - 模块设计思路
  - 数据流程详解
  - 核心技术选型说明
  - 扩展指南
- **查询接口** → [API参考](API.md)
  - 所有模块的完整接口文档
  - 参数说明和使用示例
- **了解项目结构** → [项目结构](PROJECT_STRUCTURE.md)
  - 完整的目录结构
  - 文件组织说明
- **查看进展** → [项目追踪](TRACKER.md)

---

## 📖 按角色推荐

### 👤 普通用户
1. [项目主页](../README.md) - 了解这是什么
2. [快速开始](QUICKSTART.md) - 开始使用

### 👨‍💻 开发者（第一次接触项目）
1. [项目主页](../README.md) - 项目概览
2. [架构设计](ARCHITECTURE.md) - 理解整体架构 ⭐
3. [API参考](API.md) - 查阅接口

### 🔧 开发者（需要添加功能）
1. [架构设计 - 扩展指南](ARCHITECTURE.md#扩展指南)
2. [API参考](API.md) - 了解现有接口

### 🎨 开发者（需要修改UI）
1. [app.py](../app.py) - Streamlit应用代码
2. [架构设计](ARCHITECTURE.md) - 理解系统架构

### 📊 项目经理/产品经理
1. [项目主页](../README.md) - 功能概览
2. [项目追踪](TRACKER.md) - 任务管理与进度追踪

---

## 📝 按主题查找

### 配置管理
- [架构设计 - 配置管理模块](ARCHITECTURE.md#1-配置管理模块srconfigpy)
- [API - Config类](API.md#srcconfig)

### 数据加载
- [架构设计 - 数据加载模块](ARCHITECTURE.md#2-数据加载模块srcdata_loaderpy)
- [API - DataLoader类](API.md#srcdata_loader)

### 索引构建
- [架构设计 - 索引构建模块](ARCHITECTURE.md#3-索引构建模块srcindexerpy)
- [API - IndexManager类](API.md#srcindexer)

### 查询引擎
- [架构设计 - 查询引擎模块](ARCHITECTURE.md#4-查询引擎模块srcquery_enginepy)
- [API - QueryEngine类](API.md#srcquery_engine)

### 对话管理
- [架构设计 - 对话管理模块](ARCHITECTURE.md#5-对话管理模块srcchat_managerpy)
- [API - ChatManager类](API.md#srcchat_manager)

### 扩展开发
- [架构设计 - 扩展指南](ARCHITECTURE.md#扩展指南)

### 性能优化
- [架构设计 - 性能优化建议](ARCHITECTURE.md#性能优化建议)

---

## 🔍 快速查找

### 关键词索引

**A**
- API密钥配置 → [快速开始](QUICKSTART.md)
- API接口 → [API参考](API.md)

**C**
- Chroma数据库 → [架构设计 - 索引构建](ARCHITECTURE.md#3-索引构建模块srcindexerpy)
- CLI工具 → [项目主页 - CLI工具](../README.md#方式二命令行工具)
- Citation（引用溯源）→ [架构设计 - 查询引擎](ARCHITECTURE.md#4-查询引擎模块srcquery_enginepy)

**D**
- DeepSeek集成 → [架构设计 - 查询引擎](ARCHITECTURE.md#4-查询引擎模块srcquery_enginepy)

**E**
- Embedding模型 → [架构设计 - 索引构建](ARCHITECTURE.md#3-索引构建模块srcindexerpy)
- 扩展功能 → [架构设计 - 扩展指南](ARCHITECTURE.md#扩展指南)

**L**
- LlamaIndex → [架构设计 - LlamaIndex架构集成](ARCHITECTURE.md#llamaindex-架构集成)

**M**
- Markdown加载 → [API - MarkdownLoader](API.md#markdownloader-类)
- 多轮对话 → [架构设计 - 对话管理](ARCHITECTURE.md#5-对话管理模块srcchat_managerpy)

**P**
- 性能优化 → [架构设计 - 性能优化](ARCHITECTURE.md#性能优化建议)

**Q**
- 查询引擎 → [API - QueryEngine](API.md#queryengine-类)

**V**
- 向量数据库 → [架构设计 - 索引构建](ARCHITECTURE.md#3-索引构建模块srcindexerpy)

**W**
- 网页抓取 → [API - WebLoader](API.md#webloader-类)

---

## 💡 常见问题快速查找

| 问题 | 文档位置 |
|------|---------|
| 如何安装和启动？ | [项目主页](../README.md#🚀-快速开始-quick-start) |
| 如何添加新的数据源？ | [架构设计 - 扩展指南](ARCHITECTURE.md#1-添加新的数据源) |
| 如何切换LLM模型？ | [架构设计 - 切换LLM](ARCHITECTURE.md#3-切换-llm) |
| API密钥如何配置？ | [项目主页 - 配置API密钥](../README.md#2-配置-api-密钥) |
| 各个模块的接口是什么？ | [API参考](API.md) |

---

## 📖 推荐阅读路径

### 路径1：快速使用（10分钟）
1. [项目主页](../README.md) - 了解项目（10分钟）

### 路径2：深入理解（30分钟）
1. [项目主页](../README.md) - 项目概览（5分钟）
2. [架构设计](ARCHITECTURE.md) - 理解架构（20分钟）⭐
3. [项目追踪](TRACKER.md) - 了解进展（5分钟）

### 路径3：开发准备（40分钟）
1. [项目主页](../README.md) - 项目概览（5分钟）
2. [架构设计](ARCHITECTURE.md) - 理解架构（20分钟）⭐
3. [API参考](API.md) - 接口文档（15分钟）

---

## 📊 文档统计

- **总文档数**: 7个
- **总字数**: 约22,000+字
- **代码示例**: 90+个
- **最后更新**: 2025-10-09

---

## 🤝 贡献文档

如果您发现文档有任何问题或需要改进的地方，欢迎：
- 提交Issue
- 提交Pull Request
- 直接联系维护者

---

**💡 提示**: 建议从 [架构设计文档](ARCHITECTURE.md) 开始，它能帮助你快速建立对整个系统的认知！

