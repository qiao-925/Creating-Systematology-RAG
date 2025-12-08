# Zeabur 部署方案文档

**创建日期**: 2025-12-09  
**方案类型**: 双服务分离部署（Streamlit + FastAPI）

---

## 1. 部署架构

### 1.1 服务分离策略

项目包含两个服务，需要在 Zeabur 上分别部署：

- **Streamlit 服务**（Web UI）：默认服务，端口 8501
- **FastAPI 服务**（REST API）：通过自定义启动命令部署，端口 8000

### 1.2 部署方式

使用 **Zeabur 自定义启动命令** 功能实现服务分离：
- **默认 Dockerfile**：启动 Streamlit（8501）
- **FastAPI 服务**：在 Zeabur 控制台自定义启动命令

---

## 2. 服务配置

### 2.1 Streamlit 服务（默认）

**配置方式**：使用默认 Dockerfile，无需额外配置

**启动命令**（Dockerfile 默认）：
```bash
streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0
```

**端口**：8501

**访问地址**：`https://rag-app.zeabur.app`（示例）

**环境变量**：
- 所有必需的环境变量（DEEPSEEK_API_KEY、CHROMA_CLOUD_API_KEY 等）
- `APP_MODE`：不设置或设置为其他值（默认启动 Streamlit）

### 2.2 FastAPI 服务（自定义命令）

**配置方式**：在 Zeabur 控制台设置自定义启动命令

**启动命令**（在 Zeabur 控制台设置）：
```bash
uvicorn src.business.rag_api.fastapi_app:app --host 0.0.0.0 --port ${PORT:-8000}
```

**端口**：8000

**访问地址**：`https://rag-api.zeabur.app`（示例）

**环境变量**：
- 所有必需的环境变量（与 Streamlit 服务相同）
- `APP_MODE`：不需要设置（启动命令已明确指定）

---

## 3. Zeabur 部署步骤

### 3.1 部署 Streamlit 服务

1. **创建新服务**
   - 在 Zeabur 控制台创建新服务
   - 连接到你的 Git 仓库

2. **配置服务**
   - **启动命令**：留空（使用 Dockerfile 默认）
   - **端口**：8501
   - **环境变量**：配置所有必需的环境变量

3. **部署**
   - 点击部署，等待构建完成
   - 获得 Streamlit 服务的域名（如 `rag-app.zeabur.app`）

### 3.2 部署 FastAPI 服务

1. **创建新服务**
   - 在 Zeabur 控制台创建新服务
   - 连接到**同一个** Git 仓库（同一套代码）

2. **配置服务**
   - **启动命令**（关键）：
     ```bash
     uvicorn src.business.rag_api.fastapi_app:app --host 0.0.0.0 --port ${PORT:-8000}
     ```
   - **端口**：8000
   - **环境变量**：配置所有必需的环境变量（与 Streamlit 服务相同）

3. **部署**
   - 点击部署，等待构建完成
   - 获得 FastAPI 服务的域名（如 `rag-api.zeabur.app`）

---

## 4. 环境变量配置

两个服务需要配置相同的环境变量：

### 4.1 必需环境变量

- `DEEPSEEK_API_KEY`：DeepSeek API 密钥
- `JWT_SECRET_KEY`：JWT 密钥（至少32字符）
- `CHROMA_CLOUD_API_KEY`：Chroma Cloud API 密钥
- `CHROMA_CLOUD_TENANT`：Chroma Cloud Tenant
- `CHROMA_CLOUD_DATABASE`：Chroma Cloud Database

### 4.2 可选环境变量

- `EMBEDDING_MODEL`：默认 `BAAI/bge-base-zh-v1.5`
- `HF_ENDPOINT`：默认 `https://hf-mirror.com`
- `CORS_ORIGINS`：默认 `*`

---

## 5. 验证部署

### 5.1 Streamlit 服务验证

访问 Streamlit 服务域名：
- 应显示 Web UI 界面
- 可以正常进行对话查询

### 5.2 FastAPI 服务验证

1. **健康检查**：
   ```bash
   curl https://rag-api.zeabur.app/health
   ```
   应返回：`{"status": "healthy"}`

2. **API 文档**：
   访问 `https://rag-api.zeabur.app/docs`
   应显示 Swagger UI 文档

3. **测试接口**：
   ```bash
   curl -X POST https://rag-api.zeabur.app/chat/stream \
     -H "Content-Type: application/json" \
     -d '{"message": "测试"}'
   ```

---

## 6. 故障排查

### 6.1 服务无法启动

**检查项**：
1. 启动命令是否正确（FastAPI 服务）
2. 端口配置是否正确
3. 环境变量是否完整配置

### 6.2 FastAPI 服务无法访问

**检查项**：
1. 确认启动命令已正确设置
2. 检查端口是否为 8000
3. 查看 Zeabur 日志确认服务已启动

### 6.3 Streamlit 服务无法访问

**检查项**：
1. 确认未设置自定义启动命令（使用默认）
2. 检查端口是否为 8501
3. 查看 Zeabur 日志确认服务已启动

---

## 7. 文件说明

### 7.1 Dockerfile

- **默认行为**：启动 Streamlit（8501）
- **支持环境变量**：`APP_MODE=api` 可切换为 FastAPI（但推荐使用自定义命令）

### 7.2 zeabur.json

- 当前配置为 FastAPI（可忽略，因为使用自定义命令）
- 主要用于环境变量定义和端口配置参考

---

## 8. 注意事项

1. **同一套代码**：两个服务使用相同的代码仓库和 Dockerfile
2. **环境变量同步**：两个服务的环境变量应保持一致
3. **启动命令**：FastAPI 服务必须通过 Zeabur 控制台设置自定义启动命令
4. **端口配置**：确保两个服务使用不同的端口（8501 和 8000）

---

## 9. 更新记录

- **2025-12-09**：创建文档，记录双服务分离部署方案
- 使用自定义启动命令方式实现服务分离
