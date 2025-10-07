# 文档导航

> 快速找到您需要的文档

## 🚀 我想...

### 快速开始使用
→ [快速开始指南](QUICKSTART.md) - 5分钟上手

### 了解如何使用这个应用
→ [README](../README.md) - 完整的使用指南
→ [快速开始](QUICKSTART.md) - 快速上手

### 理解系统架构和设计
→ [架构设计文档](ARCHITECTURE.md) ⭐ **强烈推荐先读这个**
  - 整体架构图
  - 模块设计思路
  - 数据流程详解
  - 核心技术选型说明
  - 扩展指南

### 开发和修改代码
→ [开发者指南](DEVELOPER_GUIDE.md) ⭐ **开发必读**
  - 详细的代码解析
  - 常见开发任务示例
  - 调试技巧
  - 最佳实践

### 编写和运行测试
→ [测试指南](TESTING_GUIDE.md) ⭐ **测试必读**
  - 完整的测试体系
  - 单元测试、集成测试、E2E测试
  - RAG特定测试策略
  - CI/CD集成

→ [测试快速开始](TEST_QUICKSTART.md) **快速上手**
  - 5分钟开始运行测试
  - 测试统计和清单
  - 常用命令速查

### 查看API接口
→ [API参考文档](API.md)
  - 所有模块的完整接口文档
  - 参数说明
  - 使用示例

### 了解技术决策
→ [技术决策记录](DECISIONS.md)
  - 为什么选择这些技术
  - 每个决策的原因和权衡

### 了解项目结构
→ [项目结构说明](PROJECT_STRUCTURE.md)
  - 完整的目录结构
  - 文件组织说明
  - 查找指南

### 查看项目进展
→ [开发日志](CHANGELOG.md)
→ [待办事项](TODO.md)

---

## 📖 按角色推荐

### 👤 普通用户
1. [README](../README.md) - 了解这是什么
2. [快速开始](QUICKSTART.md) - 开始使用

### 👨‍💻 开发者（第一次接触项目）
1. [README](../README.md) - 项目概览
2. [架构设计](ARCHITECTURE.md) - 理解整体架构 ⭐
3. [开发者指南](DEVELOPER_GUIDE.md) - 深入代码 ⭐
4. [API参考](API.md) - 查阅接口

### 🔧 开发者（需要添加功能）
1. [架构设计 - 扩展指南](ARCHITECTURE.md#扩展指南)
2. [开发者指南 - 常见开发任务](DEVELOPER_GUIDE.md#常见开发任务)
3. [API参考](API.md) - 了解现有接口

### 🎨 开发者（需要修改UI）
1. [app.py](../app.py) - Streamlit应用代码
2. [开发者指南 - Streamlit最佳实践](DEVELOPER_GUIDE.md)

### 📊 项目经理/产品经理
1. [README](../README.md) - 功能概览
2. [技术决策](DECISIONS.md) - 技术选型原因
3. [待办事项](TODO.md) - 未来规划

---

## 📝 按主题查找

### 配置管理
- [架构设计 - 配置管理模块](ARCHITECTURE.md#1-配置管理模块srconfigpy)
- [开发者指南 - 配置管理](DEVELOPER_GUIDE.md#1-配置管理srcconfigpy)
- [API - Config类](API.md#srcconfig)

### 数据加载
- [架构设计 - 数据加载模块](ARCHITECTURE.md#2-数据加载模块srcdata_loaderpy)
- [开发者指南 - 数据加载器](DEVELOPER_GUIDE.md#2-数据加载器srcdata_loaderpy)
- [API - DataLoader类](API.md#srcdata_loader)

### 索引构建
- [架构设计 - 索引构建模块](ARCHITECTURE.md#3-索引构建模块srcindexerpy)
- [开发者指南 - 索引构建器](DEVELOPER_GUIDE.md#3-索引构建器srcindexerpy)
- [API - IndexManager类](API.md#srcindexer)

### 查询引擎
- [架构设计 - 查询引擎模块](ARCHITECTURE.md#4-查询引擎模块srcquery_enginepy)
- [开发者指南 - 查询引擎](DEVELOPER_GUIDE.md#4-查询引擎srcquery_enginepy)
- [API - QueryEngine类](API.md#srcquery_engine)

### 对话管理
- [架构设计 - 对话管理模块](ARCHITECTURE.md#5-对话管理模块srcchat_managerpy)
- [开发者指南 - 对话管理器](DEVELOPER_GUIDE.md#5-对话管理器srcchat_managerpy)
- [API - ChatManager类](API.md#srcchat_manager)

### 扩展开发
- [架构设计 - 扩展指南](ARCHITECTURE.md#扩展指南)
- [开发者指南 - 常见开发任务](DEVELOPER_GUIDE.md#常见开发任务)

### 性能优化
- [架构设计 - 性能优化建议](ARCHITECTURE.md#性能优化建议)
- [开发者指南 - 调试技巧](DEVELOPER_GUIDE.md#调试技巧)

---

## 🔍 快速查找

### 关键词索引

**A**
- API密钥配置 → [快速开始](QUICKSTART.md)
- API接口 → [API参考](API.md)

**C**
- Chroma数据库 → [架构设计 - 索引构建](ARCHITECTURE.md#3-索引构建模块srcindexerpy)
- CLI工具 → [README - CLI工具](../README.md#方式二命令行工具)
- Citation（引用溯源）→ [架构设计 - 查询引擎](ARCHITECTURE.md#4-查询引擎模块srcquery_enginepy)

**D**
- DeepSeek集成 → [架构设计 - 查询引擎](ARCHITECTURE.md#4-查询引擎模块srcquery_enginepy)
- Debug（调试）→ [开发者指南 - 调试技巧](DEVELOPER_GUIDE.md#调试技巧)

**E**
- Embedding模型 → [技术决策 - ADR-004](DECISIONS.md#adr-004-使用本地embedding模型)
- 扩展功能 → [架构设计 - 扩展指南](ARCHITECTURE.md#扩展指南)

**L**
- LlamaIndex → [架构设计 - LlamaIndex架构集成](ARCHITECTURE.md#llamaindex-架构集成)

**M**
- Markdown加载 → [API - MarkdownLoader](API.md#markdownloader-类)
- 多轮对话 → [架构设计 - 对话管理](ARCHITECTURE.md#5-对话管理模块srcchat_managerpy)

**P**
- PDF支持 → [开发者指南 - 添加PDF支持](DEVELOPER_GUIDE.md#任务-1添加-pdf-支持)
- 性能优化 → [架构设计 - 性能优化](ARCHITECTURE.md#性能优化建议)

**Q**
- 查询引擎 → [API - QueryEngine](API.md#queryengine-类)

**S**
- Streamlit界面 → [开发者指南 - Streamlit](DEVELOPER_GUIDE.md)

**V**
- 向量数据库 → [技术决策 - ADR-003](DECISIONS.md#adr-003-选择chroma作为向量数据库)

**W**
- 网页抓取 → [API - WebLoader](API.md#webloader-类)

---

## 💡 常见问题快速查找

| 问题 | 文档位置 |
|------|---------|
| 如何安装和启动？ | [快速开始](QUICKSTART.md) |
| 如何添加新的数据源？ | [架构设计 - 扩展指南](ARCHITECTURE.md#1-添加新的数据源) |
| 如何切换LLM模型？ | [架构设计 - 切换LLM](ARCHITECTURE.md#3-切换-llm) |
| 如何调试查询结果？ | [开发者指南 - 调试技巧](DEVELOPER_GUIDE.md#调试技巧) |
| API密钥如何配置？ | [快速开始 - 配置API密钥](QUICKSTART.md#第二步配置-api-密钥) |
| 如何提高检索精度？ | [开发者指南 - Q2](DEVELOPER_GUIDE.md#q2如何优化检索精度) |
| 为什么选择这些技术？ | [技术决策](DECISIONS.md) |
| 各个模块的接口是什么？ | [API参考](API.md) |

---

## 📊 文档更新记录

| 文档 | 最后更新 | 状态 |
|------|---------|------|
| README.md | 2025-10-07 | ✅ 完整 |
| QUICKSTART.md | 2025-10-07 | ✅ 完整 |
| ARCHITECTURE.md | 2025-10-07 | ✅ 完整 |
| DEVELOPER_GUIDE.md | 2025-10-07 | ✅ 完整 |
| API.md | 2025-10-07 | ✅ 完整 |
| PROJECT_STRUCTURE.md | 2025-10-07 | ✅ 完整 |
| DECISIONS.md | 2025-10-07 | ✅ 完整 |
| CHANGELOG.md | 2025-10-07 | ✅ 完整 |
| TODO.md | 2025-10-07 | ✅ 完整 |

---

## 🎯 推荐阅读路径

### 路径1：快速使用（10分钟）
1. [README](../README.md) - 2分钟
2. [快速开始](QUICKSTART.md) - 8分钟
3. 开始使用！

### 路径2：深入理解（30分钟）
1. [README](../README.md) - 2分钟
2. [架构设计](ARCHITECTURE.md) - 20分钟 ⭐
3. [技术决策](DECISIONS.md) - 8分钟

### 路径3：开发准备（60分钟）
1. [README](../README.md) - 2分钟
2. [架构设计](ARCHITECTURE.md) - 20分钟 ⭐
3. [开发者指南](DEVELOPER_GUIDE.md) - 30分钟 ⭐
4. [API参考](API.md) - 8分钟（按需查阅）

---

**提示**：建议从 [架构设计文档](ARCHITECTURE.md) 开始，它能帮助你快速建立对整个系统的认知！

