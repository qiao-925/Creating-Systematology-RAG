# 三层架构详细指南

## 1. 架构概览

```
前端层（Presentation Layer）
    │
    │ 只访问 RAGService
    ↓
业务层（Business Layer）
    │
    │ 通过依赖注入获取基础设施能力
    ↓
基础设施层（Infrastructure Layer）
```

## 2. 层级职责

### 2.1 前端层

| 职责 | 禁止 |
|------|------|
| 用户交互 | 直接访问基础设施层 |
| UI 展示 | 包含业务逻辑 |
| 状态管理 | 直接操作数据库 |

**目录**：`frontend/`

### 2.2 业务层

| 职责 | 禁止 |
|------|------|
| 核心业务逻辑 | 夹带技术细节 |
| 流程编排 | 直接依赖具体实现 |
| 事务管理 | 反向依赖前端层 |

**目录**：`backend/business/`

### 2.3 基础设施层

| 职责 | 禁止 |
|------|------|
| 技术实现 | 包含业务逻辑 |
| 外部集成 | 依赖业务层或前端层 |
| 数据访问 | 定义业务规则 |

**目录**：`backend/infrastructure/`

## 3. 依赖方向检查

### 正确的依赖方向

```python
# frontend/main.py
from backend.business.rag_api import RAGService  # ✅ 前端 → 业务

# backend/business/rag_api/rag_service.py
from backend.infrastructure.indexer import IndexManager  # ✅ 业务 → 基础设施
```

### 错误的依赖方向

```python
# backend/infrastructure/indexer/manager.py
from backend.business.rag_api import RAGService  # ❌ 基础设施 → 业务

# frontend/main.py
from backend.infrastructure.indexer import IndexManager  # ❌ 前端 → 基础设施
```

## 4. 循环依赖检测

### 检测方法

```bash
# 使用 pycycle 检测循环依赖
pip install pycycle
pycycle --source src/
```

### 解决循环依赖

1. 提取公共接口到独立模块
2. 使用依赖注入
3. 使用事件驱动解耦

## 5. 设计变更检查清单

- [ ] 标注影响到的层级
- [ ] 标注上下游模块
- [ ] 确认无循环依赖
- [ ] 确认无跨层访问
