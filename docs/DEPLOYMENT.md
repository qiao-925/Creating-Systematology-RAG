# 部署指南

## Zeabur 部署（推荐，国内友好）

### 前置准备
1. 注册 Zeabur 账号
2. 准备 DeepSeek API 密钥
3. GitHub 仓库推送代码

### 部署步骤
1. 登录 Zeabur Dashboard
2. 点击 "New Project" → "Deploy from GitHub"
3. 选择本仓库
4. 配置环境变量：
   - DEEPSEEK_API_KEY（必填）
5. 点击 "Deploy"
6. 等待构建完成（约 5-10 分钟）

### 访问应用
部署完成后，Zeabur 会自动分配域名，点击访问即可。

---

## Railway 部署（备选）

### 前置准备
同 Zeabur

### 部署步骤
1. 登录 Railway Dashboard
2. 点击 "New Project" → "Deploy from GitHub repo"
3. 选择本仓库
4. 配置环境变量（同上）
5. 点击 "Deploy"

### 访问应用
Railway 会自动分配域名，在项目详情页查看。

---

## 环境变量说明

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| DEEPSEEK_API_KEY | ✅ | - | DeepSeek API 密钥 |
| EMBEDDING_MODEL | ❌ | BAAI/bge-base-zh-v1.5 | Embedding 模型 |
| HF_ENDPOINT | ❌ | https://hf-mirror.com | HuggingFace 镜像 |
| APP_PORT | ❌ | 8501 | 应用端口 |

---

## 注意事项

1. **首次启动慢**：需下载 Embedding 模型（约 400MB），耐心等待
2. **数据不持久化**：重启后索引和会话数据会丢失（演示阶段可接受）
3. **用户数据**：多用户认证数据存储在容器内，重启后丢失
4. **成本预估**：
   - Zeabur：免费层足够（开发版）
   - Railway：免费层 $5 额度/月，约可运行 500 小时

---

## 后续优化方向

1. 添加持久卷（存储向量数据和用户数据）
2. 切换到外部向量数据库（Qdrant Cloud）
3. 模型预打包到镜像（加快启动速度）
4. 配置自定义域名
5. 添加监控和日志服务
