# 项目缓存机制分析

> **分析日期**: 2025-11-04  
> **目的**: 列出项目中所有缓存机制，便于批量清理和持久化管理

---

## 📋 缓存分类总览

项目中的缓存主要分为以下几类：

1. **内存缓存**（运行时缓存，程序退出后清除）
2. **文件缓存**（持久化到磁盘，程序重启后保留）
3. **外部缓存**（第三方库自动管理）

---

## 1. 内存缓存（运行时缓存）

### 1.1 Embedding 模型缓存

**位置**: 
- `src/indexer/embedding_utils.py`
- `src/indexer.py` (向后兼容层)

**机制**:
- 全局变量 `_global_embed_model` 存储模型实例
- 单例模式，避免重复加载
- 模型名称变更时自动清除

**清理方法**:
```python
from src.indexer import clear_embedding_model_cache
clear_embedding_model_cache()
```

**文件**: `src/indexer/embedding_utils.py:225`

---

### 1.2 Reranker 模型缓存

**位置**: `src/rerankers/factory.py`

**机制**:
- 全局字典 `_reranker_cache` 存储重排序器实例
- Key: `"{reranker_type}:{model}:{top_n}"`
- 支持按需清理

**清理方法**:
```python
from src.rerankers.factory import clear_reranker_cache
clear_reranker_cache()
```

**文件**: `src/rerankers/factory.py:82`

---

### 1.3 Streamlit Session State 缓存

**位置**: `app.py`, `pages/`

**机制**:
- Streamlit 的 `st.session_state` 存储会话状态
- 包括：用户信息、索引管理器、对话管理器、模型实例等

**清理方法**:
- 程序退出时自动清除
- 可通过 `st.session_state.clear()` 手动清除

**主要缓存项**:
- `embed_model` - Embedding 模型实例
- `index_manager` - 索引管理器
- `chat_manager` - 对话管理器
- `rag_service` - RAG 服务实例
- `boot_ready` - 启动状态

---

## 2. 文件缓存（持久化缓存）

### 2.1 任务缓存系统（CacheManager）

**位置**: 
- `data/cache_state.json` - 缓存状态文件
- `src/cache_manager.py` - 缓存管理器（需要确认是否存在）

**机制**:
- 多步骤缓存：`step_clone`、`step_parse`、`step_vectorize`
- 每个任务有唯一的 `task_id`
- 使用哈希值验证缓存有效性

**缓存文件路径**:
- 状态文件: `data/cache_state.json`
- 解析结果: `data/processed/{task_id}/documents.pkl`
- 配置路径: `config.CACHE_STATE_PATH` (默认: `data/cache_state.json`)

**配置**:
- `ENABLE_CACHE` - 是否启用缓存（默认: `true`）
- `CACHE_STATE_PATH` - 缓存状态文件路径

**文件**: `src/config/settings.py:52-53`

---

### 2.2 GitHub 仓库本地缓存

**位置**: `data/github_repos/`

**机制**:
- Git 仓库本地克隆
- 支持增量更新（git pull）
- 按 `owner/repo_branch` 组织目录

**目录结构**:
```
data/github_repos/
├── {owner}/
│   ├── {repo}_{branch}/
│   │   └── [仓库文件]
```

**配置**:
- `GITHUB_REPOS_PATH` - 仓库存储路径（默认: `data/github_repos`）

**文件**: `src/config/settings.py:48`

**清理方法**:
- 直接删除对应目录
- 或通过 `GitRepositoryManager` 管理

---

### 2.3 解析文档缓存（Pickle 文件）

**位置**: `data/processed/{task_id}/documents.pkl`

**机制**:
- 使用 pickle 序列化已解析的文档
- 每个任务有独立的缓存目录
- 文件名: `documents.pkl`

**目录结构**:
```
data/processed/
├── {owner}_{repo}_{branch}_{commit_hash}/
│   └── documents.pkl
```

**文件**: `src/data_parser/modules/cache.py:67-71`

**清理方法**:
- 删除 `data/processed/` 下的对应目录
- 或通过 `CacheManager` 管理

---

### 2.4 向量数据库缓存（Chroma）

**位置**: `vector_store/`

**机制**:
- Chroma 向量数据库持久化存储
- SQLite 数据库文件: `chroma.sqlite3`
- 向量索引文件: `{collection_id}/` 目录

**目录结构**:
```
vector_store/
├── chroma.sqlite3          # 元数据数据库
├── {collection_id}/        # 向量索引文件
│   ├── data_level0.bin
│   ├── header.bin
│   ├── length.bin
│   └── link_lists.bin
└── version_*/              # 版本化集合（可选）
```

**配置**:
- `VECTOR_STORE_PATH` - 向量库路径（默认: `vector_store`）

**文件**: `src/config/settings.py:36`

**清理方法**:
- 删除 `vector_store/` 目录（会清除所有向量数据）
- 或通过 `IndexManager.clear_index()` 清除特定集合

---

### 2.5 会话记录缓存

**位置**: `sessions/`

**机制**:
- JSON 文件存储对话会话
- 按用户组织：`sessions/{user_email}/`
- 文件名: `{session_id}.json`

**目录结构**:
```
sessions/
├── {user_email}/
│   ├── {session_id}.json
│   └── ...
```

**配置**:
- `SESSIONS_PATH` - 会话路径（默认: `sessions`）

**文件**: `src/config/settings.py:44`

**清理方法**:
- 删除对应会话文件
- 或通过 `ChatManager` 管理

---

### 2.6 用户数据缓存

**位置**: `data/users.json`

**机制**:
- JSON 文件存储用户信息
- 包含用户邮箱、密码哈希等

**清理方法**:
- 删除 `data/users.json`（会清除所有用户数据）

---

### 2.7 GitHub 元数据缓存

**位置**: `data/github_metadata.json`

**机制**:
- JSON 文件存储 GitHub 仓库元数据
- 包含最后同步的 commit SHA、文件哈希等

**清理方法**:
- 删除 `data/github_metadata.json`（会清除所有元数据）

---

### 2.8 活动日志缓存

**位置**: `logs/activity/`

**机制**:
- 日志文件记录用户操作
- 按日期组织：`logs/activity/{date}.log`

**配置**:
- `ACTIVITY_LOG_PATH` - 活动日志路径（默认: `logs/activity`）

**文件**: `src/config/settings.py:45`

**清理方法**:
- 删除对应日志文件

---

## 3. 外部缓存（第三方库自动管理）

### 3.1 HuggingFace 模型缓存

**位置**: `~/.cache/huggingface/` (系统默认)

**机制**:
- HuggingFace Transformers 自动管理
- 下载的模型文件缓存在此目录
- 支持离线模式

**配置**:
- `HF_ENDPOINT` - HuggingFace 镜像地址（默认: `https://hf-mirror.com`）
- `HF_OFFLINE_MODE` - 离线模式（默认: `false`）

**文件**: `src/indexer/embedding_utils.py:20-40`

**清理方法**:
- 删除 `~/.cache/huggingface/` 目录
- 或通过环境变量 `HF_HOME` 指定其他路径

---

### 3.2 Python 字节码缓存

**位置**: `__pycache__/` (各目录下)

**机制**:
- Python 自动生成 `.pyc` 文件
- 加速模块导入

**清理方法**:
- 删除所有 `__pycache__/` 目录
- 或使用 `find . -type d -name __pycache__ -exec rm -r {} +`

---

### 3.3 pytest 测试缓存

**位置**: `.pytest_cache/`

**机制**:
- pytest 测试框架缓存测试结果

**清理方法**:
- 删除 `.pytest_cache/` 目录

---

### 3.4 Streamlit 缓存装饰器

**位置**: `pages/3_🔎_Chroma_Viewer.py`

**机制**:
- `@st.cache_resource` 装饰器缓存资源
- Streamlit 自动管理

**文件**: `pages/3_🔎_Chroma_Viewer.py:12`

**清理方法**:
- Streamlit 自动管理，或通过 UI 清除

---

## 📊 缓存统计

### 按类型统计

| 类型 | 数量 | 总大小（估算） | 清理难度 |
|------|------|--------------|---------|
| 内存缓存 | 3 | - | 简单（程序退出自动清除） |
| 文件缓存 | 8 | 较大（取决于数据量） | 中等 |
| 外部缓存 | 4 | 很大（模型文件） | 简单（可手动删除） |

### 按重要性分类

**高重要性**（不建议删除）:
- 向量数据库 (`vector_store/`)
- 用户数据 (`data/users.json`)
- 会话记录 (`sessions/`)

**中等重要性**（可选择性清理）:
- 任务缓存 (`data/cache_state.json`, `data/processed/`)
- GitHub 仓库缓存 (`data/github_repos/`)
- GitHub 元数据 (`data/github_metadata.json`)

**低重要性**（可安全清理）:
- HuggingFace 模型缓存 (`~/.cache/huggingface/`)
- Python 字节码缓存 (`__pycache__/`)
- 测试缓存 (`.pytest_cache/`)
- 活动日志 (`logs/`)

---

## 🧹 批量清理建议

### 清理脚本示例

```python
"""批量清理缓存脚本"""
from pathlib import Path
import shutil

def clear_all_caches():
    """清理所有缓存"""
    # 1. 任务缓存
    cache_state = Path("data/cache_state.json")
    if cache_state.exists():
        cache_state.unlink()
    
    processed_dir = Path("data/processed")
    if processed_dir.exists():
        shutil.rmtree(processed_dir)
        processed_dir.mkdir()
    
    # 2. GitHub 仓库缓存（可选）
    # repos_dir = Path("data/github_repos")
    # if repos_dir.exists():
    #     shutil.rmtree(repos_dir)
    #     repos_dir.mkdir()
    
    # 3. Python 字节码缓存
    for pycache in Path(".").rglob("__pycache__"):
        shutil.rmtree(pycache)
    
    # 4. 测试缓存
    pytest_cache = Path(".pytest_cache")
    if pytest_cache.exists():
        shutil.rmtree(pytest_cache)
    
    # 5. 活动日志（可选）
    # logs_dir = Path("logs")
    # if logs_dir.exists():
    #     shutil.rmtree(logs_dir)
    #     logs_dir.mkdir()

if __name__ == "__main__":
    clear_all_caches()
    print("✅ 缓存清理完成")
```

### 清理命令（Makefile）

```makefile
.PHONY: clean-cache
clean-cache:
	@echo "清理缓存..."
	rm -rf data/cache_state.json
	rm -rf data/processed/*
	rm -rf __pycache__
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	rm -rf .pytest_cache
	@echo "✅ 缓存清理完成"

.PHONY: clean-all
clean-all: clean-cache
	@echo "清理所有生成文件..."
	rm -rf vector_store/*/  # 保留目录结构
	rm -rf sessions/*
	rm -rf logs/*
	@echo "✅ 全部清理完成"
```

---

## 🔍 缓存文件位置汇总

| 缓存类型 | 路径 | 配置文件 | 清理函数 |
|---------|------|---------|---------|
| 任务缓存状态 | `data/cache_state.json` | `config.CACHE_STATE_PATH` | 手动删除 |
| 解析文档缓存 | `data/processed/{task_id}/documents.pkl` | - | 手动删除 |
| GitHub 仓库 | `data/github_repos/{owner}/{repo}_{branch}/` | `config.GITHUB_REPOS_PATH` | 手动删除 |
| 向量数据库 | `vector_store/` | `config.VECTOR_STORE_PATH` | `IndexManager.clear_index()` |
| 会话记录 | `sessions/{user_email}/{session_id}.json` | `config.SESSIONS_PATH` | `ChatManager` |
| 用户数据 | `data/users.json` | - | 手动删除 |
| GitHub 元数据 | `data/github_metadata.json` | - | 手动删除 |
| 活动日志 | `logs/activity/{date}.log` | `config.ACTIVITY_LOG_PATH` | 手动删除 |
| Embedding 模型（内存） | 全局变量 | - | `clear_embedding_model_cache()` |
| Reranker 模型（内存） | 全局字典 | - | `clear_reranker_cache()` |
| HuggingFace 模型 | `~/.cache/huggingface/` | `HF_ENDPOINT`, `HF_OFFLINE_MODE` | 手动删除 |
| Python 字节码 | `__pycache__/` | - | 手动删除 |
| pytest 缓存 | `.pytest_cache/` | - | 手动删除 |

---

## 📝 注意事项

1. **向量数据库清理**: 删除 `vector_store/` 会清除所有索引，需要重新构建
2. **用户数据清理**: 删除 `data/users.json` 会清除所有用户，需要重新注册
3. **会话记录清理**: 删除 `sessions/` 会清除所有对话历史
4. **GitHub 缓存清理**: 删除 `data/github_repos/` 需要重新克隆仓库
5. **HuggingFace 缓存**: 删除后首次使用需要重新下载模型（可能很慢）

---

## 🎯 推荐清理策略

### 日常清理（推荐）
- Python 字节码缓存 (`__pycache__/`)
- pytest 测试缓存 (`.pytest_cache/`)
- 活动日志（保留最近7天）

### 定期清理（每月）
- 任务缓存状态（`data/cache_state.json`）
- 解析文档缓存（`data/processed/`）
- 旧的活动日志

### 谨慎清理（需确认）
- 向量数据库（会丢失索引）
- 用户数据（会丢失用户信息）
- 会话记录（会丢失对话历史）
- GitHub 仓库缓存（需要重新克隆）

---

**最后更新**: 2025-11-04

