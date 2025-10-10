# GitHub 仓库数据源集成实施方案

**日期**: 2025-10-10  
**任务编号**: #1  
**类型**: 实施方案（前置准备）  
**Agent**: Claude Sonnet 4.5  
**预估时长**: 3-4 小时

---

## 🎯 任务目标

使 RAG 系统支持从 GitHub 仓库导入文档，与现有的 Markdown 和 Web 数据源并列，保持架构一致性。

---

## 📦 方案概览

### 核心原则

- ✅ **参考现有实现**：复用 `MarkdownLoader` 和 `WebLoader` 的设计模式
- ✅ **最小改动**：遵循用户规则第 6 条，仅添加必要功能
- ✅ **渐进式开发**：按依赖关系分步实施
- ✅ **文档先行**：更新完整文档体系

---

## 🛠️ 实施步骤（按依赖关系排序）

### 步骤 1: 依赖管理 ⭐

**文件**: `pyproject.toml`

添加依赖：
```toml
"llama-index-readers-github>=0.2.0",
```

**完成标准**: `uv sync` 成功安装

---

### 步骤 2: 配置管理 ⭐⭐

**文件**: 
- `env.template`
- `src/config.py`

**env.template 新增**:
```env
# GitHub数据源配置（可选）
GITHUB_TOKEN=your_github_token_here
GITHUB_DEFAULT_BRANCH=main
```

**config.py 新增配置项**:
```python
# GitHub配置
self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
self.GITHUB_DEFAULT_BRANCH = os.getenv("GITHUB_DEFAULT_BRANCH", "main")
```

**完成标准**: 配置加载正常，无破坏现有配置

---

### 步骤 3: 功能实现 - GithubLoader ⭐⭐⭐

**文件**: `src/data_loader.py`

**实现要点**:
1. 新增 `GithubLoader` 类（参考 `WebLoader` 结构）
2. 使用 `GithubRepositoryReader` 而非 `GithubClient`
3. 支持文件类型过滤（如仅加载 `.md`、`.py` 等）
4. 添加元数据（仓库名、文件路径、分支等）

**核心方法**:
```python
class GithubLoader:
    def load_repository(self, owner, repo, branch, file_extensions) -> List[LlamaDocument]
    def load_repositories(self, repo_configs) -> List[LlamaDocument]
```

**便捷函数**:
```python
def load_documents_from_github(owner, repo, branch, file_extensions, clean) -> List[LlamaDocument]
```

**完成标准**: 
- 能成功加载公开仓库
- 能使用 Token 加载私有仓库
- 元数据完整

---

### 步骤 4: CLI 工具集成 ⭐⭐

**文件**: `main.py`

**新增命令**: `import-github`

**命令参数**:
```bash
python main.py import-github OWNER REPO --branch main --exts .md,.py --token xxx
```

**实现要点**:
- 参考 `cmd_import_urls` 函数结构
- 添加参数解析
- 调用 `load_documents_from_github`
- 输出统计信息

**完成标准**: CLI 命令可正常执行

---

### 步骤 5: 测试用例补充 ⭐⭐⭐

**文件**: `tests/unit/test_data_loader.py`

**新增测试类**: `TestGithubLoader`

**测试用例**（至少 8 个）:
1. ✅ 成功加载公开仓库
2. ✅ 使用 Token 加载（Mock）
3. ✅ 文件类型过滤
4. ✅ 分支指定
5. ✅ 错误仓库处理
6. ✅ 网络错误处理（Mock）
7. ✅ 元数据验证
8. ✅ 批量加载多个仓库

**Mock 策略**:
- Mock `GithubClient` API 调用
- 使用固定测试数据（参考 `TestWebLoader` 的 Mock 方式）

**完成标准**: 
- 测试通过率 100%
- 无破坏现有测试

---

### 步骤 6: 集成测试补充 ⭐

**文件**: `tests/integration/test_data_pipeline.py`

**新增测试**:
- 测试 GitHub → Indexer 完整流程
- 参考现有 `test_markdown_to_index_pipeline`

**完成标准**: 集成测试通过

---

### 步骤 7: 文档更新 - 技术决策 ⭐

**文件**: `docs/DECISIONS.md`

**新增 ADR**: `ADR-008: 集成 GitHub 数据源`

**内容**:
- 背景：为什么需要 GitHub 数据源
- 决策：使用 `GithubRepositoryReader` 而非 `GithubClient`
- 理由：高层封装、开箱即用、与现有架构一致
- 实施：集成方案概述

**完成标准**: 决策记录完整

---

### 步骤 8: 文档更新 - 架构文档 ⭐⭐

**文件**: `docs/ARCHITECTURE.md`

**更新位置**:
1. 第 104-159 行：数据加载模块设计
2. 添加 `GithubLoader` 说明
3. 更新扩展指南

**完成标准**: 架构文档准确反映新功能

---

### 步骤 9: 文档更新 - API 文档 ⭐⭐

**文件**: `docs/API.md`

**新增章节**:
- `GithubLoader` 类 API
- `load_documents_from_github()` 函数 API
- 参数说明、返回值、示例代码

**完成标准**: API 文档完整

---

### 步骤 10: 文档更新 - README ⭐

**文件**: `README.md`

**更新位置**:
- "快速开始" 部分添加 GitHub 示例
- "数据源支持" 列表添加 GitHub
- CLI 命令示例添加 `import-github`

**完成标准**: 用户可看到 GitHub 使用方法

---

### 步骤 11: 文档更新 - CHANGELOG ⭐

**文件**: `docs/CHANGELOG.md`

**新增条目**:
```markdown
### GitHub数据源集成
**目标**: 支持从 GitHub 仓库导入文档

- ✅ 依赖添加：llama-index-readers-github
- ✅ 配置管理：GitHub Token、分支配置
- ✅ 功能实现：GithubLoader 类
- ✅ CLI 工具：import-github 命令
- ✅ 测试补充：8+ 单元测试，集成测试
- ✅ 文档更新：ARCHITECTURE、API、README、DECISIONS
- 📈 功能覆盖：3种数据源（Markdown、Web、GitHub）
```

**完成标准**: CHANGELOG 记录详细

---

### 步骤 12: Agent Task Log 补充 ⭐⭐

**文件**: `agent-task-log/2025-10-10-1_GitHub数据源集成_详细过程.md`

**内容**（按 TEMPLATE.md 格式）:
- 任务目标
- 时间线（每个步骤的执行过程）
- 思考过程（方案选择）
- 修改记录（文件列表）
- 关键发现
- 最终成果
- 经验教训

**完成标准**: 任务日志完整，便于后续回溯

---

## 🧪 测试要点

### 单元测试
- GithubLoader 各方法独立测试
- 边界条件：空仓库、网络错误、权限错误
- Mock 策略：隔离外部 API

### 集成测试
- GitHub → Indexer → QueryEngine 全流程
- 使用小型公开仓库测试

### 手动测试
```bash
# 测试 1: 公开仓库
python main.py import-github microsoft TypeScript --branch main --exts .md

# 测试 2: 私有仓库（需 Token）
python main.py import-github yourorg yourrepo --token xxx

# 测试 3: 查询验证
python main.py query "GitHub 仓库中的内容"
```

---

## 📂 影响文件清单

### 新增文件
- `agent-task-log/2025-10-10-1_GitHub数据源集成_详细过程.md`

### 修改文件（共 12 个）
1. `pyproject.toml` - 依赖添加
2. `env.template` - 配置模板
3. `src/config.py` - 配置类
4. `src/data_loader.py` - 核心功能
5. `main.py` - CLI 命令
6. `tests/unit/test_data_loader.py` - 单元测试
7. `tests/integration/test_data_pipeline.py` - 集成测试
8. `docs/DECISIONS.md` - 技术决策
9. `docs/ARCHITECTURE.md` - 架构文档
10. `docs/API.md` - API 文档
11. `docs/README.md` - 使用指南
12. `docs/CHANGELOG.md` - 开发日志

---

## ⚠️ 注意事项

### 争议点（需要用户决策）

1. **是否需要在 Streamlit UI 中集成？**
   - 优点：Web 界面可用
   - 缺点：增加 UI 复杂度
   - **建议**：暂不集成，保持 CLI 使用，符合"最小改动"原则

2. **文件类型过滤默认值？**
   - 选项 A：仅 `.md`（保守）
   - 选项 B：`.md`, `.py`, `.js`, `.ts`（常用代码文档）
   - **建议**：选项 B

3. **是否支持子目录过滤？**
   - 需求：只加载特定目录（如 `/docs`）
   - **建议**：暂不支持，遵循"最小改动"

### 风险控制
- ✅ 不修改现有 Loader 代码（避免破坏）
- ✅ 使用官方 Reader（避免造轮子）
- ✅ Mock 所有外部调用（测试隔离）

---

## 📊 预期成果

### 代码
- 新增：~150 行核心代码
- 测试：10+ 测试用例
- 测试通过率：100%

### 文档
- 新建：1 个 task log
- 更新：7 个文档文件

### 功能
- 支持 3 种数据源：Markdown、Web、GitHub
- CLI 命令完整：4 个导入命令
- 配置灵活：支持 Token、分支、文件过滤

---

## ⏱️ 预估工作量

- **总时长**：3-4 小时
- **步骤 1-2**（配置）：30 分钟
- **步骤 3-4**（功能）：1 小时
- **步骤 5-6**（测试）：1 小时
- **步骤 7-12**（文档）：1 小时

---

## 📋 实施清单（Todo）

- [ ] 步骤 1: 添加 llama-index-readers-github 依赖到 pyproject.toml
- [ ] 步骤 2: 配置管理：env.template 和 config.py 添加 GitHub 配置
- [ ] 步骤 3: 实现 GithubLoader 类和便捷函数
- [ ] 步骤 4: main.py 添加 import-github CLI 命令
- [ ] 步骤 5: 编写 GithubLoader 单元测试（8+ 用例）
- [ ] 步骤 6: 添加 GitHub 数据管道集成测试
- [ ] 步骤 7: 更新 DECISIONS.md：添加 ADR-008
- [ ] 步骤 8: 更新 ARCHITECTURE.md：数据加载模块章节
- [ ] 步骤 9: 更新 API.md：GithubLoader API 文档
- [ ] 步骤 10: 更新 README.md：添加 GitHub 使用示例
- [ ] 步骤 11: 更新 CHANGELOG.md：记录本次集成
- [ ] 步骤 12: 编写 agent-task-log 任务日志

---

## 🚀 1小时工作建议

如果时间有限（仅1小时），建议优先完成以下**高优先级步骤**：

```
✅ 步骤 1: 依赖管理 (5分钟)
✅ 步骤 2: 配置管理 (10分钟)  
✅ 步骤 3: GithubLoader 功能实现 (30分钟) ⭐核心
✅ 步骤 4: CLI 工具集成 (15分钟)
```

**总计约 60 分钟** - 完成核心功能实现

### 下次继续（剩余步骤）
- 步骤 5-6: 测试补充（1小时）
- 步骤 7-12: 文档更新（1小时）

---

**方案制定完成时间**: 2025-10-10  
**方案设计原则**: 最小改动、参考现有、渐进实施、文档完备  
**断点续传**: 本方案支持分阶段执行，完成前4步即可实现核心功能

