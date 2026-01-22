# 2025-10-29 【bugfix】修复 coverage 依赖问题 - 快速摘要

**【Task Type】**: bugfix
**日期**: 2025-10-29  
**任务类型**: Bug修复  
**优先级**: 高

## 问题描述

在运行 `make test-cov` 时，出现以下错误：
```
ModuleNotFoundError: No module named 'coverage.data'
```

## 根本原因

`pytest-cov` 插件依赖 `coverage` 包，但 `coverage` 没有被显式声明在测试依赖中。在某些情况下，`coverage` 包可能被误删除或未正确安装。

## 解决方案

在 `pyproject.toml` 的测试依赖中显式添加 `coverage` 包：

```toml
[project.optional-dependencies]
test = [
    "pytest>=7.4.0",
    "coverage>=7.3.0",  # 添加了 coverage
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "pytest-benchmark>=4.0.0",
    "pytest-asyncio>=0.21.0",
]
```

## 修复步骤

1. 在 `pyproject.toml` 中添加 `coverage>=7.3.0` 到测试依赖
2. 清理损坏的 coverage 安装文件
3. 重新安装测试依赖
4. 运行测试验证修复

## 验证结果

✅ 测试成功运行，生成覆盖率报告
- 测试总数: 159
- 通过: 135
- 失败: 15
- 错误: 7
- 覆盖率: 35%

## 影响范围

- ✅ 修复了 `make test-cov` 命令
- ✅ 修复了覆盖率报告生成
- ✅ 不影响其他功能

## 备注

- 选择 `coverage>=7.3.0` 是因为 coverage 8.0.0 在 Windows + Python 3.12 上不可用
- 需要手动清理了损坏的 coverage 包残留文件

