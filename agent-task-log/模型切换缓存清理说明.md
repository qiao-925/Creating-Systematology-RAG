# 模型切换缓存清理说明

**日期**：2025-01-31  
**问题**：切换嵌入模型后仍使用旧模型  
**状态**：✅ 已修复

---

## 🔍 问题原因

更换嵌入模型时出现两个问题：

1. **`.env` 文件覆盖**：`.env` 文件中仍然配置了旧模型 `BAAI/bge-base-zh-v1.5`，覆盖了代码中的默认值
2. **全局模型缓存**：Python 全局变量 `_global_embed_model` 缓存了旧模型实例

---

## ✅ 已修复内容

### 1. 更新 `.env` 文件
已自动将 `.env` 文件中的模型配置更新为：
```bash
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B
```

### 2. 增强模型加载逻辑
添加了自动检测和清理机制：

- ✅ **自动检测模型变更**：加载模型时自动检测配置是否变更
- ✅ **自动清理缓存**：模型名称不一致时自动清除旧缓存
- ✅ **强制重新加载**：新增 `force_reload` 参数支持强制重新加载
- ✅ **清理函数**：新增 `clear_embedding_model_cache()` 函数

---

## 🔧 使用方法

### 方法1：重启应用（推荐）

**最简单的方法**：重启应用即可自动加载新模型

```bash
# 停止当前应用（如果是 Streamlit）
# 然后重新启动
make run
# 或
uv run streamlit run app.py
```

**原理**：
- 应用重启后，全局变量会清空
- 下次加载时会从配置读取新模型名称
- 自动下载并加载新模型

---

### 方法2：使用清理函数（开发调试）

如果需要在不重启的情况下切换模型：

```python
from src.indexer import clear_embedding_model_cache, load_embedding_model

# 清除缓存
clear_embedding_model_cache()

# 重新加载（会自动使用新配置）
embed_model = load_embedding_model()

# 或者强制重新加载
embed_model = load_embedding_model(force_reload=True)
```

---

### 方法3：在 Streamlit 界面重置

如果是在 Streamlit 应用中，可以通过以下方式：

1. **清除会话状态并重新加载**：
   ```python
   # 在 Streamlit 中
   if st.button("🔄 重新加载模型"):
       from src.indexer import clear_embedding_model_cache
       clear_embedding_model_cache()
       st.session_state['embed_model'] = None
       st.rerun()
   ```

2. **或者直接刷新页面**：在浏览器中按 `Ctrl+R` 或 `F5`

---

## 📋 验证步骤

### 1. 检查配置
```python
from src.config import config
print(config.EMBEDDING_MODEL)
# 应该输出: Qwen/Qwen3-Embedding-0.6B
```

### 2. 检查环境变量
```bash
cat .env | grep EMBEDDING_MODEL
# 应该输出: EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B
```

### 3. 运行应用并查看日志
启动应用后，查看日志应该显示：
```
📦 开始加载 Embedding 模型（全新加载）: Qwen/Qwen3-Embedding-0.6B
```

而不是：
```
📦 开始加载 Embedding 模型（全新加载）: BAAI/bge-base-zh-v1.5
```

---

## ⚠️ 重要提示

### 1. 需要重新构建索引

⚠️ **不同嵌入模型的向量空间不兼容！**

切换模型后，**必须重新构建索引**，否则查询结果会不正确。

**操作步骤**：
1. 备份现有索引（如需保留）
2. 清理或删除旧索引
3. 重新加载文档并构建索引

### 2. 首次下载模型

首次使用新模型时会自动下载：
- **模型大小**：~2.3GB
- **下载时间**：取决于网络速度（使用镜像会更快）
- **缓存位置**：`~/.cache/huggingface/hub/`

### 3. 内存要求

新模型（Qwen3-Embedding-0.6B）比旧模型（bge-base-zh-v1.5）更大：
- **旧模型**：~420MB
- **新模型**：~2.3GB
- 需要更多内存和加载时间

---

## 🐛 故障排除

### 问题1：仍在使用旧模型

**检查清单**：
1. ✅ `.env` 文件是否已更新
2. ✅ 是否重启了应用
3. ✅ 日志中显示的是哪个模型名称

**解决方法**：
```bash
# 方法1：清除全局缓存并重启
# 重启应用即可

# 方法2：使用清理函数（Python环境）
from src.indexer import clear_embedding_model_cache
clear_embedding_model_cache()
```

### 问题2：模型加载失败

**可能原因**：
- 网络问题（无法访问 HuggingFace）
- 模型名称错误
- 磁盘空间不足

**解决方法**：
1. 检查网络连接和镜像配置
2. 确认模型名称正确：`Qwen/Qwen3-Embedding-0.6B`
3. 检查磁盘空间：`df -h ~/.cache/huggingface/`

### 问题3：查询结果异常

**可能原因**：
- 使用了旧索引（用旧模型构建的）

**解决方法**：
- **必须重新构建索引**，使用新模型生成向量

---

## 📊 代码变更总结

### 修改的文件

1. **src/indexer.py**：
   - `load_embedding_model()`: 添加 `force_reload` 参数和模型名称检测
   - 新增 `clear_embedding_model_cache()`: 清理全局缓存函数

2. **src/config.py**（之前已修改）：
   - 默认模型改为 `Qwen/Qwen3-Embedding-0.6B`

3. **env.template**（之前已修改）：
   - 模板默认值更新

4. **.env**（已自动更新）：
   - 实际配置文件更新

---

## ✅ 验证完成

运行以下命令验证配置：

```bash
# 检查 .env 配置
cat .env | grep EMBEDDING_MODEL

# 检查 Python 配置
python3 -c "from src.config import config; print(config.EMBEDDING_MODEL)"
```

两者都应该输出：`Qwen/Qwen3-Embedding-0.6B`

---

**修复完成时间**：2025-01-31  
**下一步**：重启应用，使用新模型重新构建索引

