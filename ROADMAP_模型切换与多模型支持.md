# 模型切换与多模型支持 - Roadmap

**创建日期**: 2025-12-08  
**状态**: 📋 规划中（未来扩展）  
**优先级**: P1（重要但非紧急）

---

## 1. 背景与目标

### 1.1 问题背景

1. **HF Inference API 服务不稳定**：某些模型可能未部署或暂时不可用（404错误）
2. **模型效果差异**：不同模型在不同场景下效果不同，需要能够切换测试
3. **向量兼容性问题**：不同模型的向量空间不互通，切换模型需要重建索引

### 1.2 核心目标

- ✅ **多模型共存**：支持同时保留多个模型的索引，无需重建
- ✅ **自动 Fallback**：模型不可用时自动切换到备选模型
- ✅ **无缝切换**：切换模型时自动使用对应的 collection，无需手动重建索引
- ✅ **可插拔架构**：模型切换功能设计为可插拔，不影响现有功能

---

## 2. 核心设计

### 2.1 Collection 命名策略

**设计原则**：通过 collection 名称区分不同模型，实现多模型共存

**命名规则**：
```
{base_name}_{embedding_type}_{model_slug}
```

**示例**：
- `default_hf-inference_qwen-embedding-0.6b` - HF Inference API 模型
- `default_local_bge-base-zh-v1.5` - 本地模型
- `user_xxx_hf-inference_qwen-embedding-0.6b` - 用户专属 collection

**模型名称转换规则**：
- 将模型名称转换为有效的标识符
- 去除特殊字符（`/`, `.`, `_` 等）
- 统一转小写，用 `-` 连接
- 例如：`Qwen/Qwen3-Embedding-0.6B` → `qwen-embedding-0.6b`

### 2.2 模型列表配置

**配置位置**：`application.yml`

```yaml
embedding:
  type: hf-inference  # 或 local
  # 模型优先级列表（按顺序尝试）
  model_priority:
    - Qwen/Qwen3-Embedding-0.6B
    - BAAI/bge-base-zh-v1.5
    - sentence-transformers/all-MiniLM-L6-v2
  # 自动 fallback 开关
  auto_fallback: true
```

### 2.3 自动 Fallback 机制

**实现位置**：`src/infrastructure/embeddings/factory.py`

**工作流程**：
1. 按配置的模型优先级列表顺序尝试创建模型
2. 如果某个模型初始化失败（404/服务不可用），自动尝试下一个
3. 记录最终成功使用的模型
4. 确保索引和查询使用同一模型

**错误处理**：
- 404 错误：模型未部署，尝试下一个
- 503 错误：服务不可用，尝试下一个
- 其他错误：记录日志，尝试下一个
- 所有模型都失败：抛出异常，提示用户检查配置

### 2.4 模型一致性检查

**检查时机**：
- 查询时：验证当前模型与索引时模型是否匹配
- 索引时：记录使用的模型名称和维度到 metadata

**实现方式**：
- 在 Chroma collection metadata 中记录：
  - `embedding_model`: 模型名称
  - `embedding_type`: 模型类型（hf-inference/local）
  - `embedding_dimension`: 向量维度
- 查询时检查：如果不匹配，给出警告或自动切换

---

## 3. 实施计划

### 阶段1：基础功能（当前已完成）

- ✅ 简化 HF Inference Embedding 代码
- ✅ 统一错误处理（全部重试）
- ✅ 修复 timeout 参数传递

### 阶段2：Collection 命名策略（待实施）

**任务清单**：
- [ ] 创建 collection 名称生成工具函数
  - 文件：`src/infrastructure/indexer/utils/collection_name.py`
  - 函数：`generate_collection_name(embedding_type, model_name, base_name="default")`
- [ ] 修改 `IndexManager` 使用自动生成的 collection 名称
  - 文件：`src/infrastructure/indexer/core/manager.py`
  - 逻辑：如果没有明确指定 `collection_name`，自动根据 embedding 类型和模型名称生成
- [ ] 保持向后兼容：如果明确指定了 `collection_name`，优先使用

**预期效果**：
- 不同模型自动使用不同的 collection
- 切换模型时自动切换到对应 collection，无需重建索引
- 可以同时保留多个模型的索引

### 阶段3：模型列表与自动 Fallback（待实施）

**任务清单**：
- [ ] 在配置中添加模型优先级列表
  - 文件：`application.yml`
  - 配置项：`embedding.model_priority`
- [ ] 修改 `factory.py` 实现自动 fallback
  - 文件：`src/infrastructure/embeddings/factory.py`
  - 逻辑：按列表顺序尝试创建模型，失败时自动切换下一个
- [ ] 改进错误提示
  - 文件：`src/infrastructure/embeddings/hf_inference_embedding.py`
  - 说明：明确说明是 HF API 服务端问题，建议尝试其他模型

**预期效果**：
- 模型不可用时自动切换到备选模型
- 减少因服务端问题导致的失败
- 提高系统可用性

### 阶段4：模型一致性保障（待实施）

**任务清单**：
- [ ] 在向量存储 metadata 中记录模型信息
  - 文件：`src/infrastructure/indexer/core/init.py`
  - 记录：模型名称、类型、维度
- [ ] 实现模型一致性检查
  - 文件：`src/infrastructure/indexer/utils/consistency.py`
  - 检查：查询时验证当前模型与索引时模型是否匹配
- [ ] 模型切换工作流
  - 检测模型变更
  - 警告需要重建索引（如果使用不同 collection 则无需重建）
  - 提供重建选项

**预期效果**：
- 防止模型不匹配导致的查询错误
- 提供清晰的模型切换指引
- 支持无缝模型切换

### 阶段5：完整工作流与文档（待实施）

**任务清单**：
- [ ] 编写模型切换文档
  - 说明切换影响、最佳实践、注意事项
- [ ] 添加模型切换的 UI 支持（可选）
  - 在设置页面显示当前模型
  - 提供模型切换选项
- [ ] 性能优化
  - 模型实例缓存
  - Collection 预加载

---

## 4. 技术细节

### 4.1 Collection 名称生成函数

```python
def generate_collection_name(
    embedding_type: str,
    model_name: str,
    base_name: str = "default"
) -> str:
    """生成基于模型信息的 collection 名称
    
    Args:
        embedding_type: 模型类型（"hf-inference" 或 "local"）
        model_name: 模型名称（如 "Qwen/Qwen3-Embedding-0.6B"）
        base_name: 基础名称（默认 "default"）
        
    Returns:
        collection 名称（如 "default_hf-inference_qwen-embedding-0.6b"）
    """
    # 将模型名称转换为有效的标识符
    model_slug = model_name.lower().replace("/", "-").replace("_", "-").replace(".", "-")
    # 去除连续的分隔符
    model_slug = "-".join(filter(None, model_slug.split("-")))
    
    return f"{base_name}_{embedding_type}_{model_slug}"
```

### 4.2 自动 Fallback 实现

```python
def create_embedding_with_fallback(
    embedding_type: str,
    model_priority: List[str],
    **kwargs
) -> BaseEmbedding:
    """创建 Embedding 实例（带自动 fallback）
    
    按优先级列表尝试创建模型，失败时自动切换下一个
    """
    last_error = None
    
    for model_name in model_priority:
        try:
            logger.info(f"尝试创建模型: {model_name}")
            return create_embedding(
                embedding_type=embedding_type,
                model_name=model_name,
                **kwargs
            )
        except Exception as e:
            logger.warning(f"模型 {model_name} 创建失败: {e}")
            last_error = e
            continue
    
    # 所有模型都失败
    raise RuntimeError(
        f"所有模型都创建失败。最后一个错误: {last_error}"
    ) from last_error
```

### 4.3 模型一致性检查

```python
def check_model_consistency(
    index_manager: IndexManager,
    current_embedding: BaseEmbedding
) -> bool:
    """检查当前模型与索引时模型是否一致
    
    Returns:
        True 如果一致，False 如果不一致
    """
    # 从 collection metadata 获取索引时使用的模型
    collection_metadata = index_manager.chroma_collection.metadata or {}
    indexed_model = collection_metadata.get("embedding_model")
    indexed_type = collection_metadata.get("embedding_type")
    
    # 获取当前模型信息
    current_model = current_embedding.get_model_name()
    current_type = get_embedding_type(current_embedding)
    
    # 检查是否一致
    if indexed_model and indexed_model != current_model:
        logger.warning(
            f"模型不匹配：索引使用 {indexed_model}，当前使用 {current_model}"
        )
        return False
    
    return True
```

---

## 5. 注意事项

### 5.1 向量兼容性

**重要**：不同嵌入模型的向量空间不互通

- ❌ 用模型A生成的向量，不能用模型B查询
- ✅ 每个模型需要独立的 collection
- ✅ 切换模型时，确保使用对应的 collection

### 5.2 索引重建

**场景1：使用不同 collection（推荐）**
- ✅ 无需重建索引
- ✅ 可以同时保留多个模型的索引
- ✅ 切换模型只需切换 collection

**场景2：使用相同 collection**
- ⚠️ 需要重建索引
- ⚠️ 会覆盖旧模型的向量
- ⚠️ 需要重新向量化所有文档

### 5.3 性能考虑

- Collection 数量：每个模型一个 collection，注意管理
- 存储空间：多个模型会占用更多存储空间
- 查询性能：切换 collection 的开销很小

---

## 6. 未来扩展

### 6.1 模型效果对比

- 支持同时使用多个模型进行查询
- 对比不同模型的效果
- 自动选择效果最好的模型

### 6.2 模型版本管理

- 支持模型版本管理
- 记录模型切换历史
- 支持回滚到之前的模型

### 6.3 动态模型加载

- 支持运行时动态加载新模型
- 无需重启服务即可切换模型
- 支持模型热更新

---

## 7. 相关文档

- [Embedding 可插拔架构文档](./agent-task-log/2025-11/2025-11-01-4_【implementation】Embedding可插拔架构-完整实施总结.md)
- [索引管理器文档](./src/infrastructure/indexer/README.md)
- [HF Inference API 集成文档](./2025-12-06-HF-Inference-API集成-进度存档.md)

---

## 8. 更新日志

- **2025-12-08**: 创建 roadmap 文档，记录设计方案
