# 嵌入模型更换为 Qwen3-Embedding-0.6B

**日期**：2025-01-31  
**类型**：配置变更  
**状态**：✅ 已完成

---

## 📋 变更内容

将默认嵌入模型从 `BAAI/bge-base-zh-v1.5` 更换为 `Qwen/Qwen3-Embedding-0.6B`。

---

## 🔧 修改的文件

1. **src/config.py**
   - 第28行：更新默认嵌入模型
   ```python
   # 修改前
   self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-zh-v1.5")
   
   # 修改后
   self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
   ```

2. **env.template**
   - 第7行：更新模板文件中的默认值
   ```bash
   # 修改前
   EMBEDDING_MODEL=BAAI/bge-base-zh-v1.5
   
   # 修改后
   EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B
   ```

---

## 📊 模型对比

| 特性 | BAAI/bge-base-zh-v1.5 | Qwen/Qwen3-Embedding-0.6B |
|------|----------------------|---------------------------|
| **参数量** | 110M | 600M |
| **模型大小** | ~420MB | ~2.3GB |
| **支持语言** | 中英文 | 中英文（多语言） |
| **特点** | 轻量级，速度快 | 性能更强，支持query指令 |
| **HuggingFace路径** | BAAI/bge-base-zh-v1.5 | Qwen/Qwen3-Embedding-0.6B |

---

## ⚙️ 使用方法

### 方式1：使用默认值（已更新）
无需任何配置，直接使用新模型。

### 方式2：通过环境变量覆盖
如果已存在 `.env` 文件，需要手动更新：

```bash
# 编辑 .env 文件
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B
```

### 方式3：运行时通过环境变量设置
```bash
export EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B
python app.py
```

---

## ✅ 兼容性说明

1. **LlamaIndex 兼容性**：✅
   - `HuggingFaceEmbedding` 支持任何 HuggingFace 模型
   - 无需修改加载代码

2. **模型特性支持**：
   - Qwen3-Embedding 支持 query/instruction 模式
   - LlamaIndex 会自动处理这些特性

3. **首次使用**：
   - 首次运行会自动从 HuggingFace 下载模型（~2.3GB）
   - 使用 HF_MIRROR 镜像可加速下载
   - 下载后会缓存在 `~/.cache/huggingface/` 目录

---

## 🔍 验证步骤

1. **检查配置**：
   ```python
   from src.config import config
   print(config.EMBEDDING_MODEL)
   # 应该输出: Qwen/Qwen3-Embedding-0.6B
   ```

2. **测试模型加载**：
   - 启动应用或运行索引构建
   - 查看日志确认模型加载成功

3. **验证功能**：
   - 构建索引
   - 执行查询
   - 确认结果正常

---

## 📝 注意事项

1. **模型大小**：新模型更大（~2.3GB），首次下载需要更多时间和空间
2. **内存占用**：模型更大，可能需要更多内存
3. **性能影响**：
   - 推理速度可能略慢（但精度更高）
   - 可以使用 `EMBED_BATCH_SIZE` 调整批处理大小以平衡性能和速度

4. **现有索引**：
   - ⚠️ **重要**：更换模型后，**需要重新构建索引**
   - 不同模型的向量空间不兼容
   - 建议：备份或清理旧索引后重新构建

---

## 🚀 后续操作建议

1. **重新构建索引**：
   ```bash
   # 如果使用旧索引，需要清理后重新构建
   # 或者使用新的集合名称
   ```

2. **性能调优**（如需要）：
   ```bash
   # 根据实际情况调整批处理大小
   EMBED_BATCH_SIZE=10  # CPU: 5-10, GPU: 10-50
   EMBED_MAX_LENGTH=512  # 根据模型和硬件调整
   ```

3. **验证效果**：
   - 运行性能测试脚本
   - 测试查询质量
   - 对比新旧模型的表现

---

**变更完成时间**：2025-01-31  
**下一步**：重新构建索引以使用新模型

