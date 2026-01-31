# 高级配置指南

> 本文档包�?GPU 配置、Windows 特殊处理、Chroma Cloud 详细配置等高级设置�?

---

## 1. Chroma Cloud 配置

本项目使�?**Chroma Cloud** 作为向量数据库，需要配置以下环境变量：

### 1.1 必需配置

| 环境变量 | 说明 |
|---------|------|
| `CHROMA_CLOUD_API_KEY` | Chroma Cloud API 密钥 |
| `CHROMA_CLOUD_TENANT` | Chroma Cloud 租户 ID |
| `CHROMA_CLOUD_DATABASE` | Chroma Cloud 数据库名�?|

### 1.2 配置步骤

1. �?Chroma Cloud 平台创建账户并获取连接信�?
2. �?`.env` 文件中设置上述三个环境变�?
3. 启动应用后会自动连接�?Chroma Cloud

### 1.3 注意事项

- Chroma Cloud 需要网络连接，确保网络畅�?
- 配置错误时会直接抛出错误，不会回退到本地模�?
- 向量数据存储在云端，无需本地存储目录

---

## 2. GPU 配置（可选）

项目支持 **GPU优先、CPU兜底** 模式�?

### 2.1 为什么需要手动配�?

由于 `uv` �?Windows 平台上默认锁�?CPU 版本�?PyTorch�?*需要手动安�?CUDA 版本** 以获�?GPU 加速�?

### 2.2 安装步骤

```bash
# 1. 安装基础依赖（首次运行会自动执行�?
make install

# 2. 手动安装 CUDA 版本�?PyTorch（覆�?CPU 版本�?
uv pip install --force-reinstall --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio

# 3. 验证安装
uv run --no-sync python -c "import torch; print(f'版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}')"
```

### 2.3 性能对比

| 模式 | 索引构建时间 |
|------|-------------|
| 🚀 **GPU模式** | �?5 分钟 |
| 🐌 **CPU模式** | �?30 分钟+ |

### 2.4 注意事项

- 项目可以在纯 CPU 环境运行，但性能较慢
- �?Windows 平台上需要手动安�?GPU 版本以获得最佳性能
- **安装 CUDA 版本后，避免再次运行 `make install`、`make ready`、`make start` 等会触发 `uv sync` 的命�?*（会覆盖 CUDA 版本�?
- 日常使用只需 `make run` 启动应用，已自动配置 `--no-sync` 选项

---

## 3. Windows 特殊配置

### 3.1 安装 Make 工具

Windows 用户需先安�?Make 工具�?

```powershell
choco install make -y
```

> 详细安装过程 �?[Windows Make 工具安装指南](../agent-task-log/2025-10-09-3_Windows-Make工具安装与Makefile配置_快速摘�?md)

### 3.2 PowerShell 编码问题

如果遇到乱码，使�?PowerShell 包装脚本�?

```powershell
.\Makefile.ps1 run   # 使用PowerShell包装脚本（已修复UTF-8编码�?
```

---

## 4. 配置系统详解

应用提供统一的配置管理系统�?

### 4.1 侧边栏配�?

常用配置（实时生效）�?
- 模型选择
- LLM 预设
- 检索策�?
- Agentic RAG 开�?

### 4.2 设置弹窗

高级配置�?
- RAG 参数（Top-K、相似度阈值、重排序开关）
- 显示设置

### 4.3 LLM 预设

| 预设 | Temperature | Max Tokens | 适用场景 |
|------|-------------|------------|---------|
| 精确 | 0.1 | 2048 | 事实性查�?|
| 平衡 | 0.5 | 4096 | 通用场景 |
| 创意 | 0.9 | 8192 | 开放性问�?|

### 4.4 RAG 参数

- **Top-K**：检索返回的文档数量
- **相似度阈�?*：过滤低相似度结�?
- **重排序开�?*：启�?禁用重排�?

---

## 5. 主题切换

应用支持 **Light/Dark 模式** 切换�?

- 点击右上�?"�? �?"Settings" �?选择主题
- 或使用系统主题偏好自动切�?
- 所有组件（包括自定义组件）都会自动适配主题

---

## 6. 常用命令

```bash
make              # 安装依赖 + 运行测试（推荐首次运行）
make run          # 启动 Web 应用
make start        # = make + make run（一键启动）
make help         # 查看所有命�?
make test         # 运行所有测�?
make clean        # 清理生成文件
```

---

## 7. Serena (MCP ���������������) ����

Serena �ṩ���� LSP �ķ��ż������ͱ༭���������ʺϴ��ģ�����Ķ�λ�����ļ�������ع���

### 7.1 VSCode / Cursor (MCP) ����

����Ŀ��Ŀ¼���� `.vscode/mcp.json`�����ֿ�����ɱ������ã���

```json
{
  "servers": {
    "serena": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena-mcp",
        "--context",
        "ide-assistant",
        "--project",
        "${workspaceFolder}"
      ]
    }
  }
}
```

> ע�⣺��ǰ `.gitignore` Ĭ�Ϻ��� `.vscode/`�������ύ�����ã�����Ӧ���� `.gitignore` �ĺ��Թ���

### 7.2 ��Ŀ��������������ѡ��

����Ŀ��Ŀ¼������ Serena CLI �Զ����� `.serena/project.yml`����ѡ�񴴽�������

```bash
uvx --from git+https://github.com/oraios/serena serena project create --index
```

�������¹�����������ֱ��ִ�У�

```bash
uvx --from git+https://github.com/oraios/serena serena project index
```

---

**������**: 2026-01-31
