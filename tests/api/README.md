# FastAPI API 测试说明

## 测试文件结构

```
tests/
├── unit/
│   ├── test_api_auth.py          # 认证模块单元测试
│   └── test_api_dependencies.py  # 依赖注入单元测试
└── integration/
    └── test_api_integration.py   # API 集成测试
```

## 测试覆盖

### 1. 单元测试 - 认证模块 (`test_api_auth.py`)

#### 密码哈希测试
- ✅ bcrypt 密码哈希生成
- ✅ bcrypt 密码验证
- ✅ SHA256 密码验证（向后兼容）

#### JWT Token 测试
- ✅ Token 创建
- ✅ 带过期时间的 Token 创建
- ✅ 有效 Token 验证
- ✅ 无效 Token 验证
- ✅ 过期 Token 验证

#### 用户认证测试
- ✅ 成功认证
- ✅ 错误密码认证
- ✅ 不存在用户认证
- ✅ bcrypt 密码认证（新注册用户）

### 2. 单元测试 - 依赖注入 (`test_api_dependencies.py`)

#### UserManager 依赖注入
- ✅ UserManager 单例模式
- ✅ UserManager 数据持久化

#### 当前用户获取
- ✅ 有效 Token 获取用户
- ✅ 无效 Token 处理
- ✅ 不存在用户处理

#### RAGService 依赖注入
- ✅ RAGService 用户隔离
- ✅ 不同用户使用不同的 RAGService

### 3. 集成测试 - API 端点 (`test_api_integration.py`)

#### 认证端点
- ✅ 成功注册
- ✅ 重复邮箱注册
- ✅ 无效邮箱格式
- ✅ 成功登录
- ✅ 错误密码登录
- ✅ 不存在用户登录
- ✅ 获取当前用户信息
- ✅ 无 Token 访问
- ✅ 无效 Token 访问

#### 查询端点
- ✅ 未认证查询请求
- ✅ 已认证查询请求

#### 对话端点
- ✅ 未认证对话请求
- ✅ 已认证对话请求

#### 健康检查端点
- ✅ 根路径
- ✅ 健康检查

#### 错误处理
- ✅ 验证错误格式
- ✅ 统一错误响应格式

## 运行测试

### 运行所有 API 测试

```bash
# 运行所有 API 相关测试
pytest tests/unit/test_api_*.py tests/integration/test_api_integration.py -v

# 运行单元测试
pytest tests/unit/test_api_*.py -v

# 运行集成测试
pytest tests/integration/test_api_integration.py -v
```

### 运行特定测试文件

```bash
# 认证模块测试
pytest tests/unit/test_api_auth.py -v

# 依赖注入测试
pytest tests/unit/test_api_dependencies.py -v

# API 集成测试
pytest tests/integration/test_api_integration.py -v
```

### 运行特定测试用例

```bash
# 测试密码哈希
pytest tests/unit/test_api_auth.py::TestPasswordHashing -v

# 测试 JWT Token
pytest tests/unit/test_api_auth.py::TestJWTToken -v

# 测试注册端点
pytest tests/integration/test_api_integration.py::TestAuthEndpoints::test_register_success -v
```

## 测试注意事项

### 1. 环境变量

测试会自动设置必要的环境变量：
- `JWT_SECRET_KEY` - 测试用密钥
- `DEEPSEEK_API_KEY` - 测试用密钥

### 2. 用户数据隔离

每个测试使用临时用户文件，确保测试之间不相互影响。

### 3. Mock 使用

- 集成测试中的查询和对话端点使用 Mock 避免真实 API 调用
- 如果 RAGService 初始化失败，测试会允许 500 状态码（主要测试认证和路由）

### 4. 依赖注入 Mock

集成测试中会临时替换 `get_user_manager` 函数，使用临时文件存储用户数据。

## 测试覆盖率目标

- 认证模块：100%
- 依赖注入模块：100%
- API 端点：核心流程 100%，边界情况 80%+

## 持续集成

这些测试应该包含在 CI/CD 流程中，确保：
1. 每次代码提交都运行测试
2. 测试失败阻止合并
3. 定期检查测试覆盖率

