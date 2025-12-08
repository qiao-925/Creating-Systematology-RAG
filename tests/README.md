# 测试使用指南

> 快速掌握项目测试体系

---

## 📑 目录

- [快速开始](#速开始)
- [测试结构](#测试结构)
- [常用命令](#常用命令)
- [快速场景](#快速场景)
- [常见问题](#常见问题)
- [子模块文档](#子模块文档)

---

## 快速开始

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

---

## 测试结构

```
tests/
├── README.md                # 本文件（总入口）
├── conftest.py              # 核心共享fixtures
├── fixtures/                # Fixtures 模块化目录
│   ├── data.py              # 测试数据 fixtures
│   ├── indexer.py           # 索引相关 fixtures
│   ├── github.py            # GitHub 相关 fixtures
│   ├── embeddings.py        # Embedding 相关 fixtures
│   ├── llm.py               # LLM 相关 fixtures
│   └── mocks.py             # Mock 工具 fixtures
├── unit/                    # 单元测试（~100+个）
│   └── README.md
├── integration/             # 集成测试（~80+个）
│   └── README.md
├── performance/             # 性能测试
├── tools/                   # 诊断工具和Agent工具
│   └── README.md
└── agent/                   # Agent测试体系
    └── README.md
```

**测试覆盖**: ~92% | **测试总数**: 200+

---

## 常用命令

### 运行测试

```bash
pytest tests/unit            # 单元测试
pytest tests/integration     # 集成测试
pytest tests/performance     # 性能测试
pytest -m unit               # 按标记运行
pytest -m "not slow"         # 跳过慢速测试
```

### 调试和覆盖率

```bash
pytest --lf -v               # 只运行上次失败的
pytest -vv --tb=long         # 详细错误信息
pytest --cov=src --cov-report=html  # 生成覆盖率报告
```

### 性能加速

```bash
pytest -m "not slow"         # 跳过慢速测试
pytest tests/unit            # 只运行单元测试
pytest -n auto               # 并行运行（需安装pytest-xdist）
```

---

## 快速场景

### 修改代码后

```bash
# 运行相关单元测试
pytest tests/unit/test_xxx.py -v

# 查看覆盖率
pytest tests/unit/test_xxx.py --cov=src/xxx --cov-report=term
```

### 添加新功能后

```bash
# 单元测试
pytest tests/unit/test_xxx.py -v

# 集成测试
pytest tests/integration/test_xxx_integration.py -v
```

### 发布前检查

```bash
make test              # 运行所有测试
make test-cov          # 生成覆盖率报告
```

---

## 常见问题

### Q: 如何跳过需要真实API的测试？

**A**: 测试会自动检测API密钥。没有设置相关环境变量时测试会自动跳过。

```bash
pytest tests/ -v -rs  # 查看跳过的测试
```

### Q: 测试运行很慢怎么办？

**A**: 
```bash
pytest -m "not slow"   # 跳过慢速测试
pytest tests/unit      # 只运行单元测试
pytest --lf            # 只运行失败的测试
```

### Q: 如何调试失败的测试？

**A**: 
```bash
pytest tests/unit/test_xxx.py -vv --tb=long  # 详细错误
pytest tests/unit/test_xxx.py -s             # 显示print
pytest tests/unit/test_xxx.py --pdb          # 进入调试器
```

---

## 子模块文档

| 模块 | 文档 | 说明 |
|------|------|------|
| **单元测试** | [unit/README.md](unit/README.md) | 单元测试文件列表、编写规范、最佳实践 |
| **集成测试** | [integration/README.md](integration/README.md) | 集成测试文件列表、编写规范、注意事项 |
| **Agent测试** | [agent/README.md](agent/README.md) | Agent测试索引、源文件映射表、工具使用指南 |
| **诊断工具** | [tools/README.md](tools/README.md) | HuggingFace配置检查、环境验证、故障排查 |

---

## 提交前检查清单

- [ ] `make test` 全部通过
- [ ] 覆盖率 > 80% (`make test-cov`)
- [ ] 新功能有对应测试
- [ ] 修复的Bug有回归测试
- [ ] 测试命名清晰易懂
- [ ] 清理临时文件 (`make clean`)

---

## 相关文档

- **架构设计**: [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) - 系统架构
- **API参考**: [../docs/API.md](../docs/API.md) - 接口文档

---

**提示**: 
- 🚀 新手从"快速开始"和"常用命令"开始
- 💡 日常开发查看"快速场景"
- 📚 详细内容请查看对应的子模块文档

好的测试是代码质量的保障！🎯
