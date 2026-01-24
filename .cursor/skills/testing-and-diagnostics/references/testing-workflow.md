# 测试工作流详细说明

## 1. 测试类型选择

| 代码变更类型 | 测试类型 | 说明 |
|--------------|----------|------|
| 后端变更（`backend/**`）| 单元测试 | `pytest` |
| 前端变更（`frontend/**`）| 浏览器测试 | Playwright |
| 全栈变更 | 先单元测试，再浏览器测试 | 按顺序执行 |

## 2. 单元测试工作流

### 2.1 选择测试

根据改动文件生成推荐测试列表：

```bash
# 示例：改动了 query_processor.py
python scripts/run_test_workflow.py --select src/query/processor.py

# 推荐测试：
# - tests/unit/test_query_processor.py
# - tests/integration/test_query_pipeline.py
```

### 2.2 执行测试

```bash
# 执行推荐测试
pytest tests/unit/test_query_processor.py -v

# 执行所有相关测试
pytest tests/ -k "query" -v
```

### 2.3 结果汇总

```markdown
## 测试结果

| 测试文件 | 通过 | 失败 | 跳过 |
|----------|------|------|------|
| test_query_processor.py | 10 | 0 | 0 |
| test_query_pipeline.py | 5 | 1 | 0 |

### 失败用例
- test_query_pipeline.py::test_complex_query
  - 原因：超时
  - 补救：增加超时时间
```

## 3. 测试优先级

| 优先级 | 测试类型 | 执行时机 |
|--------|----------|----------|
| 1 | 单元测试 | 每次提交前必须 |
| 2 | 集成测试 | 功能完成时 |
| 3 | E2E 测试 | 发布前 |

## 4. 脚本使用

### 4.1 完整工作流

```bash
# 执行完整测试工作流
python scripts/run_test_workflow.py --changed-files src/query/processor.py
```

### 4.2 参数说明

| 参数 | 说明 |
|------|------|
| `--changed-files` | 指定改动的文件 |
| `--select-only` | 只选择测试，不执行 |
| `--verbose` | 详细输出 |

## 5. 测试结果记录

测试结果应记录在任务日志中：

```markdown
## 测试执行

### 命令
```bash
pytest tests/unit/test_query_processor.py -v
```

### 结果
- 通过：10
- 失败：0
- 覆盖范围：query_processor 模块

### 补救动作
- 无
```
