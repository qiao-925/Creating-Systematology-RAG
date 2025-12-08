# Commit Log

## 主要更改

### feat: 实现 FastAPI + JWT 认证功能

**新增功能：**
- 实现基于 FastAPI 的 REST API 服务
- 集成 JWT 认证机制，支持用户注册、登录和身份验证
- 实现用户数据隔离，每个用户使用独立的 collection
- 提供 RAG 查询和对话接口（需认证）

**新增文件：**
- `src/api/main.py` - FastAPI 应用入口（CORS、统一错误处理）
- `src/api/auth.py` - JWT 认证逻辑（Token 创建、验证、密码哈希）
- `src/api/dependencies.py` - FastAPI 依赖注入
- `src/api/routers/auth.py` - 认证路由（登录、注册、获取用户信息）
- `src/api/routers/query.py` - 查询路由（异步处理）
- `src/api/routers/chat.py` - 对话路由（异步处理）
- `src/api/models/auth.py` - 认证相关 Pydantic 模型
- `src/api/models/responses.py` - 统一错误响应模型
- `tests/unit/test_api_auth.py` - 认证模块单元测试
- `tests/unit/test_api_dependencies.py` - 依赖注入单元测试
- `tests/integration/test_api_integration.py` - API 集成测试

**修改文件：**
- `pyproject.toml` - 添加 FastAPI、JWT 相关依赖
- `src/config/settings.py` - 添加 JWT 配置项
- `env.template` - 添加 JWT_SECRET_KEY 和 CORS_ORIGINS 环境变量
- `Dockerfile` - 支持 FastAPI 和 Streamlit 双模式启动
- `railway.toml` - 更新启动命令为 FastAPI 服务
- `zeabur.json` - 添加 JWT 相关环境变量配置

**技术特性：**
- JWT Token 认证，30 天过期时间
- 密码哈希使用 bcrypt，兼容旧格式 SHA256
- 异步处理，使用 `asyncio.to_thread()` 包装同步调用
- 统一错误处理机制
- 自动生成 Swagger UI 和 ReDoc 文档

**API 端点：**
- `POST /auth/login` - 用户登录
- `POST /auth/register` - 用户注册
- `GET /auth/me` - 获取当前用户信息
- `POST /query` - RAG 查询（需认证）
- `POST /chat` - 对话接口（需认证）
- `GET /health` - 健康检查
- `GET /docs` - Swagger UI 文档
- `GET /redoc` - ReDoc 文档

---

## 建议的 Commit Message

```
feat: 实现 FastAPI + JWT 认证功能

新增功能：
- 实现基于 FastAPI 的 REST API 服务
- 集成 JWT 认证机制，支持用户注册、登录和身份验证
- 实现用户数据隔离，每个用户使用独立的 collection
- 提供 RAG 查询和对话接口（需认证）

新增文件：
- src/api/main.py - FastAPI 应用入口
- src/api/auth.py - JWT 认证逻辑
- src/api/dependencies.py - FastAPI 依赖注入
- src/api/routers/auth.py - 认证路由
- src/api/routers/query.py - 查询路由
- src/api/routers/chat.py - 对话路由
- src/api/models/auth.py - 认证相关 Pydantic 模型
- src/api/models/responses.py - 统一错误响应模型
- tests/unit/test_api_*.py - API 单元测试
- tests/integration/test_api_integration.py - API 集成测试

修改文件：
- pyproject.toml - 添加 FastAPI 依赖
- src/config/settings.py - 添加 JWT 配置
- env.template - 添加 JWT 和 CORS 环境变量
- Dockerfile - 支持双模式启动
- railway.toml - 更新 FastAPI 启动命令
- zeabur.json - 添加 JWT 环境变量

技术特性：
- JWT Token 认证，30 天过期时间
- 密码哈希使用 bcrypt，兼容旧格式 SHA256
- 异步处理，避免阻塞 FastAPI 事件循环
- 统一错误处理机制
- 自动生成 API 文档

API 端点：
- POST /auth/login - 用户登录
- POST /auth/register - 用户注册
- GET /auth/me - 获取当前用户信息
- POST /query - RAG 查询（需认证）
- POST /chat - 对话接口（需认证）
- GET /health - 健康检查
- GET /docs - Swagger UI 文档
- GET /redoc - ReDoc 文档
```
