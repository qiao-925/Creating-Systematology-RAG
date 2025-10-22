# 待办事项

> 项目入口 - 一眼看清要做什么

---

## 🔥 当前主要任务

**部署到 Zeabur 测试** (2025-10-22)
- 推送代码到 GitHub
- 配置环境变量 (DEEPSEEK_API_KEY)
- 测试应用功能
- 收集首批用户反馈

**相关文档**:
- 📄 [部署实施方案](agent-task-log/2025-10-22-1_最小化PaaS部署_实施方案.md)
- 📄 [部署指南](docs/DEPLOYMENT.md)
- 📄 [Dockerfile](Dockerfile) | [zeabur.json](zeabur.json) | [railway.toml](railway.toml)

---

## 📋 重要任务

### 回答质量优化 ⭐⭐⭐
- [ ] 提升检索精度（调整 similarity_top_k、相似度阈值）
- [ ] 优化 prompt 设计（更好的引导和约束）
- [ ] 添加答案质量评估（用户反馈机制）
- [ ] 测试不同问题类型的回答效果
- [ ] 收集用户反馈并迭代优化

**相关文档**:
- 📄 [查询引擎](src/query_engine.py) - 核心检索逻辑
- 📄 [对话管理](src/chat_manager.py) - 多轮对话优化
- 📄 [配置管理](src/config.py) - 相似度阈值等参数
- 📄 [RAG推理增强日志](agent-task-log/2025-10-14-1_RAG推理能力增强_详细过程.md)

### 部署方案持续优化 ⭐⭐
- [ ] 数据持久化（添加 Zeabur Volume 配置）
- [ ] 密码安全加固（bcrypt 替代 SHA256）
- [ ] 模型预打包到镜像（加快启动速度）
- [ ] 监控和日志优化（添加错误追踪）
- [ ] 成本优化（降低资源消耗）

**相关文档**:
- 📄 [用户管理](src/user_manager.py) - 密码哈希逻辑
- 📄 [索引管理](src/indexer.py) - Embedding 模型加载
- 📄 [部署指南](docs/DEPLOYMENT.md) - 后续优化方向
- 📄 [Dockerfile](Dockerfile) - 镜像构建配置

### UI/UX 优化 ⭐
- [ ] 移动端适配（响应式布局）
- [ ] 加载动画优化（Embedding 模型下载提示）
- [ ] 错误提示优化（更友好的错误信息）
- [ ] 暗色模式支持
- [ ] 快捷键支持

**相关文档**:
- 📄 [主应用](app.py) - Streamlit UI 配置
- 📄 [UI组件](src/ui_components.py) - 界面组件
- 📄 [Claude风格UI日志](agent-task-log/2025-10-15-2_Claude风格UI大改造_实施总结.md)
- 📄 [设置页面](pages/1_⚙️_设置.py) - 功能页面

---

## 💡 想法池

- 多模态支持（PDF 解析、图片识别、表格提取）
- 知识图谱可视化（概念关系展示）
- 协作功能（团队知识库、权限管理）
- API 接口开放（供第三方集成）
- 导出功能（Markdown、PDF）
- 批量导入优化（并行处理、断点续传）

---

## ✅ 最近完成

- [2025-10-22] **最小化 PaaS 部署配置完成**（Zeabur + Railway）
  - 📄 [实施方案](agent-task-log/2025-10-22-1_最小化PaaS部署_实施方案.md)
  - 📄 [部署指南](docs/DEPLOYMENT.md)

- [2025-10-15] **Claude 风格 UI 大改造**（温暖米色系 + 衬线字体）
  - 📄 [实施总结](agent-task-log/2025-10-15-2_Claude风格UI大改造_实施总结.md)

- [2025-10-14] **RAG 推理能力增强**（相似度阈值 + 温度调整）
  - 📄 [详细过程](agent-task-log/2025-10-14-1_RAG推理能力增强_详细过程.md)

---

**更新时间**: 2025-10-22  
**快速导航**: [项目 README](README.md) | [架构文档](docs/ARCHITECTURE.md) | [任务日志](agent-task-log/README.md)

