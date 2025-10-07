# 快速开始指南

本指南将帮助你在 5 分钟内启动并运行系统科学知识库 RAG 应用。

## 前置要求

- Python 3.12 或更高版本
- DeepSeek API 密钥（从 [DeepSeek 开放平台](https://platform.deepseek.com/) 获取）
- 至少 2GB 可用磁盘空间（用于 embedding 模型）

## 步骤 1：安装依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -e .
```

## 步骤 2：配置 API 密钥

1. 复制环境变量模板：

```bash
cp env.template .env
```

2. 编辑 `.env` 文件，添加你的 DeepSeek API 密钥：

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 步骤 3：启动应用

```bash
streamlit run app.py
```

应用会自动在浏览器中打开（默认地址：`http://localhost:8501`）

## 步骤 4：加载示例文档

在 Streamlit 界面的左侧边栏：

1. 点击 **"📂 从目录加载"** 部分
2. 点击 **"📖 加载 data/raw 目录"** 按钮
3. 等待文档加载和索引构建（首次运行会下载 embedding 模型，可能需要几分钟）

## 步骤 5：开始对话

在主界面的输入框中提问，例如：

- "什么是系统科学？"
- "钱学森在系统科学领域有什么贡献？"
- "什么是开放的复杂巨系统？"

系统会返回答案并显示引用来源。

## 常见问题

### Q1：首次运行很慢？

**A**：首次运行时需要下载 embedding 模型（bge-base-zh-v1.5，约 400MB），这是正常的。模型下载后会被缓存，后续运行会快很多。

### Q2：提示 "未设置 DEEPSEEK_API_KEY"？

**A**：请确保：
1. 已创建 `.env` 文件
2. 文件中正确设置了 `DEEPSEEK_API_KEY=your_key`
3. 重启应用以加载新的环境变量

### Q3：如何添加自己的文档？

**A**：有三种方式：

1. **上传文件**：在侧边栏使用文件上传功能
2. **放入目录**：将 Markdown 文件放入 `data/raw/` 目录，然后点击"加载 data/raw 目录"
3. **从网页加载**：在侧边栏输入网页 URL

### Q4：索引构建失败？

**A**：可能的原因和解决方案：

- **磁盘空间不足**：确保有足够空间
- **网络问题**：如果下载模型失败，可以手动下载后放入缓存目录
- **内存不足**：减少批量处理的文档数量

### Q5：回答质量不理想？

**A**：可以尝试：

1. 调整参数（在 `.env` 文件中）：
   ```env
   CHUNK_SIZE=1024  # 增大分块大小
   SIMILARITY_TOP_K=5  # 增加检索数量
   ```

2. 改进文档质量：确保文档内容清晰、结构良好

3. 优化提问方式：提供更具体的问题

## 下一步

- 📖 阅读 [README.md](../README.md) 了解更多功能
- 🔧 查看 [架构设计](ARCHITECTURE.md) 了解系统架构
- 📚 查看 [开发日志](CHANGELOG.md) 了解项目进展
- 💻 使用 CLI 工具进行批量操作：`python main.py --help`

## 获取帮助

如果遇到问题：

1. 查看 [开发日志](CHANGELOG.md)
2. 查看 [待办事项](TODO.md)
3. 查看 [架构设计](ARCHITECTURE.md) 了解技术细节
4. 提交 Issue

---

祝使用愉快！🎉

