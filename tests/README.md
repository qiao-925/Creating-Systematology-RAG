# 测试使用指南

> 快速掌握项目测试体系

## 🚀 快速开始

### 最简单的方式

```bash
# 方式1: 使用Makefile（推荐）
make test              # 运行所有测试
make test-unit         # 只运行单元测试
make test-integration  # 只运行集成测试
make test-cov          # 生成覆盖率报告

# 方式2: 直接使用pytest
pytest tests/unit -v                        # 单元测试
pytest tests/integration -v                 # 集成测试
pytest --cov=src --cov-report=html          # 覆盖率
```

### GitHub端到端测试

```bash
# 默认测试仓库（octocat/Hello-World）
make test-github-e2e

# 自定义测试仓库（3种方式）
# 方式1: 环境变量（临时）
export TEST_GITHUB_OWNER=your_owner
export TEST_GITHUB_REPO=your_repo
pytest tests/integration/test_github_e2e.py -v

# 方式2: .env文件（推荐，持久）
echo "TEST_GITHUB_OWNER=your_owner" >> .env
echo "TEST_GITHUB_REPO=your_repo" >> .env

# 方式3: 编辑 tests/integration/test_github_e2e.py

# 无网络时跳过GitHub测试
pytest tests/integration -m "not github_e2e" -v
```

---

## 📂 测试结构

```
tests/
├── conftest.py              # 共享fixtures
├── unit/                    # 单元测试（~60个）
│   ├── test_config.py          # 配置管理（15个）
│   ├── test_data_loader.py     # 数据加载（20个）
│   ├── test_indexer.py         # 索引构建（15个）
│   ├── test_query_engine.py    # 查询引擎（8个）
│   └── test_chat_manager.py    # 对话管理（15个）
├── integration/             # 集成测试（~25个）
│   ├── test_data_pipeline.py      # 数据处理流程（8个）
│   ├── test_query_pipeline.py     # 查询流程（7个）
│   ├── test_phoenix_integration.py # Phoenix集成（5个）
│   └── test_github_e2e.py         # GitHub端到端（10个）
├── performance/             # 性能测试（~13个）
│   └── test_performance.py
└── tools/                   # 诊断工具
    ├── check_hf_config.py      # HF配置快速检查
    ├── test_hf_config.py       # HF配置完整测试
    ├── test_hf_mirror.py       # HF镜像测试
    └── download_model.py       # 手动下载模型
```

**测试覆盖统计:**

| 模块 | 测试数 | 覆盖率 | 说明 |
|------|--------|-------|------|
| 配置管理 | 15 | 95%+ | API密钥、参数验证 |
| 数据加载 | 20 | 90%+ | Markdown、Web、GitHub |
| 索引构建 | 15 | 90%+ | 向量化、检索 |
| 查询引擎 | 8 | 85%+ | 查询、引用溯源 |
| 对话管理 | 15 | 85%+ | 会话、历史管理 |
| 集成流程 | 25 | 关键路径 | 端到端流程 |
| 性能基准 | 13 | 基准测试 | 速度、扩展性 |
| **总计** | **88+** | **~92%** | - |

---

## 🎯 常用命令速查

### 按类型运行

```bash
pytest tests/unit            # 单元测试
pytest tests/integration     # 集成测试
pytest tests/performance     # 性能测试
```

### 按标记运行

```bash
pytest -m unit                   # 单元测试标记
pytest -m integration            # 集成测试标记
pytest -m github_e2e             # GitHub E2E
pytest -m "not slow"             # 跳过慢速测试
pytest -m "not github_e2e"       # 跳过GitHub E2E
```

### 调试命令

```bash
pytest --lf -v               # 只运行上次失败的
pytest --ff -v               # 先运行上次失败的
pytest --pdb                 # 失败时进入调试器
pytest -vv --tb=long         # 详细错误信息
pytest -s                    # 显示print输出
```

### 覆盖率命令

```bash
pytest --cov=src                              # 基础覆盖率
pytest --cov=src --cov-report=term-missing    # 显示未覆盖行
pytest --cov=src --cov-report=html            # HTML报告
# 然后打开 htmlcov/index.html
```

### 性能加速

```bash
pytest -m "not slow"         # 跳过慢速测试
pytest tests/unit            # 只运行单元测试
pytest -n auto               # 并行运行（需安装pytest-xdist）
```

---

## 🔧 诊断工具

模型加载超时时按顺序执行：

```bash
# 1. 检查配置
uv run python tests/tools/check_hf_config.py

# 2. 验证环境变量
uv run python tests/tools/test_env_vars.py

# 3. 测试镜像
uv run python tests/tools/test_hf_mirror.py

# 4. 手动下载模型
uv run python tests/tools/download_model.py

# 5. 完整测试
uv run python tests/tools/test_hf_config.py
```

详细说明: [tests/tools/README.md](tools/README.md)

---

## 💡 实战场景

### 场景1: 修改配置模块后

```bash
pytest tests/unit/test_config.py -v         # 验证配置模块
pytest tests/unit -k "config" -v            # 相关模块
pytest tests/unit/test_config.py --cov=src/config --cov-report=term
```

### 场景2: 添加新数据加载功能

```bash
pytest tests/unit/test_data_loader.py -v           # 单元测试
pytest tests/integration/test_data_pipeline.py -v  # 集成测试
pytest tests/unit/test_data_loader.py --cov=src/data_loader --cov-report=html
```

### 场景3: 优化索引性能

```bash
pytest tests/performance/test_performance.py::test_indexing_speed -v
# ... 修改代码 ...
pytest tests/performance/test_performance.py::test_indexing_speed -v
pytest tests/unit/test_indexer.py -v  # 确保功能正常
```

### 场景4: GitHub集成测试

```bash
pytest tests/integration/test_github_e2e.py -v                      # 全部
pytest tests/integration/test_github_e2e.py::TestGitHubImportFlow -v  # 导入流程
pytest tests/integration/test_github_e2e.py::TestGitHubQueryFlow -v   # 查询流程

# 使用自定义仓库
TEST_GITHUB_OWNER=your_owner TEST_GITHUB_REPO=your_repo \
  pytest tests/integration/test_github_e2e.py -v
```

### 场景5: 发布前完整检查

```bash
make test              # 运行所有测试
make test-cov          # 生成覆盖率报告
make clean             # 清理临时文件

# 或一次性完成
make test-all
```

---

## ❓ 常见问题

### Q1: 如何跳过需要真实API的测试？

**A**: 测试会自动检测API密钥。没有设置`DEEPSEEK_API_KEY`时相关测试会自动跳过。

```bash
pytest tests/ -v -rs  # 查看跳过的测试
```

### Q2: 测试运行很慢怎么办？

**A**: 使用以下方法加速：

```bash
pytest -m "not slow"   # 跳过慢速测试
pytest tests/unit      # 只运行单元测试
pytest -n auto         # 并行运行（需安装pytest-xdist）
pytest --lf            # 只运行失败的测试
```

### Q3: 如何调试失败的测试？

**A**: 逐步排查：

```bash
pytest tests/unit/test_xxx.py -vv --tb=long  # 详细错误
pytest tests/unit/test_xxx.py -s             # 显示print
pytest tests/unit/test_xxx.py --pdb          # 进入调试器
pytest --lf -vv                              # 只运行失败的
```

### Q4: 如何查看未覆盖代码？

**A**: 生成详细报告：

```bash
pytest --cov=src --cov-report=html           # 生成HTML
pytest --cov=src --cov-report=term-missing   # 终端显示未覆盖行
# 浏览器打开 htmlcov/index.html
```

### Q5: 如何编写新测试？

**A**: 参考现有测试，遵循AAA模式（Arrange-Act-Assert）：准备数据 → 执行函数 → 验证结果。详见 `tests/unit/` 中的示例。

---

## 🤖 Agent 测试索引

Agent 可以使用以下资源快速理解和使用测试体系：

- **主索引文档**: `tests/AGENTS-TESTING-INDEX.md` - 完整的测试体系索引和映射表
- **元数据说明**: `tests/METADATA.md` - 测试元数据结构说明
- **元数据索引**: `tests/test_index.json` - 测试文件元数据（使用 `generate_test_index.py` 生成）

**Agent 工具**:
- `tests/tools/agent_test_selector.py` - 根据修改的文件选择相关测试
- `tests/tools/agent_test_info.py` - 查询测试详细信息
- `tests/tools/agent_test_summary.py` - 生成测试执行摘要

---

## 📚 相关文档

- [架构设计](../docs/ARCHITECTURE.md) - 系统架构
- [API参考](../docs/API.md) - 接口文档
- [诊断工具](tools/README.md) - 工具使用说明
- [Agent测试索引](AGENTS-TESTING-INDEX.md) - Agent 测试体系索引（**推荐 Agent 查阅**）

---

## ✅ 提交前检查清单

- [ ] `make test` 全部通过
- [ ] 覆盖率 > 80% (`make test-cov`)
- [ ] 新功能有对应测试
- [ ] 修复的Bug有回归测试
- [ ] 测试命名清晰易懂
- [ ] 清理临时文件 (`make clean`)

---

**💡 提示**: 
- 新手从"快速开始"和"常用命令"开始
- 日常开发查看"实战场景"
- 遇到问题查看"常见问题"

好的测试是代码质量的保障！🎯
