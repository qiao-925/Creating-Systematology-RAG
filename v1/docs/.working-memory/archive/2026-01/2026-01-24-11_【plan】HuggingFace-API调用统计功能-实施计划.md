# HuggingFace API 调用统计功能 - 实施计划

> 创建时间：2026-01-24
> 状态：规划中

---

## Checkpoint 状态表

| CP | 内容 | 状态 | 完成时间 |
|----|------|------|----------|
| CP1 | 统计数据模型设计 | ✅ | 2026-01-24 |
| CP2 | 统计收集器实现 | ✅ | 2026-01-24 |
| CP3 | 集成到 HF API 客户端 | ✅ | 2026-01-24 |
| CP4 | 查询接口与日志输出 | ✅ | 2026-01-24 |

---

## 1. 背景与目标

### 1.1 背景

当前 HF API 调用只有基础日志（DEBUG 级别），缺乏：
- 累计调用统计
- 按任务（session_id）维度的统计
- 费用追踪参考

### 1.2 目标

实现 HF API 调用统计功能：
1. **全局统计**：总调用次数、总文本数、总耗时
2. **任务级统计**：按 session_id 维度统计
3. **日志输出**：定期输出统计摘要

---

## 2. 技术方案

### 2.1 统计数据模型

```python
@dataclass
class HFAPIStats:
    """单次统计记录"""
    call_count: int = 0        # API 调用次数
    text_count: int = 0        # 处理文本数
    total_time: float = 0.0    # 总耗时（秒）
    last_call_time: Optional[datetime] = None

@dataclass  
class HFAPIStatsCollector:
    """统计收集器（单例）"""
    global_stats: HFAPIStats
    session_stats: Dict[str, HFAPIStats]  # session_id -> stats
```

### 2.2 收集点

在 `HFAPIClient.make_request()` 完成后收集：
- 调用次数 +1
- 文本数量 += len(texts)
- 耗时累加

### 2.3 session_id 传递

**方案 A**：通过 `contextvars` 传递（无侵入）
**方案 B**：在 API 客户端构造时传入

推荐方案 A，对现有代码改动最小。

---

## 3. 实施步骤

### CP1: 统计数据模型设计

**交付物**：
- [ ] `backend/infrastructure/embeddings/hf_stats.py` - 统计模型和收集器

**验收标准**：
- 模型定义完整
- 单元测试通过

### CP2: 统计收集器实现

**交付物**：
- [ ] 全局单例收集器
- [ ] session_id 上下文变量
- [ ] 统计方法（record/get_stats/reset）

**验收标准**：
- 线程安全
- 支持按 session 查询

### CP3: 集成到 HF API 客户端

**交付物**：
- [ ] 修改 `hf_api_client.py` 在请求完成后记录统计
- [ ] 可选：在 QueryContext 设置 session_id 到 contextvars

**验收标准**：
- 不影响现有功能
- 统计数据准确

### CP4: 查询接口与日志输出

**交付物**：
- [ ] 获取统计的辅助函数
- [ ] 定期日志输出（可选）

**验收标准**：
- 可通过代码获取统计信息

---

## 4. 文件改动清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `backend/infrastructure/embeddings/hf_stats.py` | 新增 | 统计模型和收集器 |
| `backend/infrastructure/embeddings/hf_api_client.py` | 修改 | 添加统计收集 |
| `backend/infrastructure/embeddings/__init__.py` | 修改 | 导出统计接口 |

---

## 5. 决策记录

| 问题 | 决策 |
|------|------|
| session_id 传递 | 方案 A: contextvars |
| 持久化 | 单独日志文件 `logs/hf_api_stats.log` |
| 展示方式 | 仅日志输出 |

### 日志触发时机

1. **阶段记录**：每次批量请求完成后记录明细
2. **定期汇总**：若有活跃任务，每 10 秒输出汇总
3. **任务完成**：任务结束时输出该任务的总统计

---

## 6. 风险与注意事项

- **线程安全**：使用 threading.Lock 保护统计数据
- **性能影响**：统计收集轻量，定时器独立线程
- **日志轮转**：日志文件使用 RotatingFileHandler
