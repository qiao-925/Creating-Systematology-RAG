# 诊断和配置工具

本目录包含用于验证配置、诊断问题的测试脚本和工具。

## 📁 文件说明

### HuggingFace 配置相关

| 文件 | 用途 | 使用场景 |
|------|------|---------|
| `check_hf_config.py` | 快速检查HF配置状态 | 首次配置、排查镜像问题 |
| `test_hf_config.py` | 完整测试HF配置和模型加载 | 验证镜像和离线模式 |
| `test_hf_mirror.py` | 测试HF镜像配置生效情况 | 排查镜像不生效问题 |
| `test_env_vars.py` | 验证环境变量设置 | 排查环境变量问题 |
| `download_model.py` | 手动从镜像下载模型 | 首次下载、网络问题 |

### Phoenix 集成相关

| 文件 | 用途 | 使用场景 |
|------|------|---------|
| `test_phoenix_integration.py` | 测试Phoenix集成 | 验证Phoenix功能 |

**注意**：`test_phoenix_integration.py` 已移至 `tests/integration/`

## 🚀 使用方法

### 快速检查配置

```bash
# 检查 HuggingFace 配置状态
uv run python tests/tools/check_hf_config.py

# 测试环境变量
uv run python tests/tools/test_env_vars.py
```

### 完整配置测试

```bash
# 测试镜像配置
uv run python tests/tools/test_hf_mirror.py

# 完整的HF配置和模型加载测试
uv run python tests/tools/test_hf_config.py
```

### 手动下载模型

```bash
# 从镜像下载 Embedding 模型
uv run python tests/tools/download_model.py
```

## 📝 故障排查流程

### 模型加载超时问题

1. **检查配置**：`check_hf_config.py`
2. **验证环境变量**：`test_env_vars.py`
3. **测试镜像**：`test_hf_mirror.py`
4. **手动下载**：`download_model.py`
5. **完整测试**：`test_hf_config.py`

### Phoenix 集成问题

```bash
# 测试 Phoenix 集成
uv run python tests/integration/test_phoenix_integration.py
```

## 🔗 相关文档

- [快速修复指南](../../QUICK_FIX.md)
- [HF镜像排查指南](../../TROUBLESHOOTING_HF_MIRROR.md)
- [测试文档](../README.md)

## 📌 注意事项

1. **执行顺序**：建议按照故障排查流程的顺序执行
2. **环境要求**：需要先配置 `.env` 文件
3. **网络环境**：镜像工具适用于国内网络环境
4. **缓存位置**：默认使用 `~/.cache/huggingface/hub`

---

**最后更新**: 2025-10-12

