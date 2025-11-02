# 规则体系优化建议

> 基于当前规则体系的全面分析和优化建议

---

## 📊 当前规则体系分析

### 规则文件统计

| 类型 | 数量 | 规则文件 |
|------|------|---------|
| **Always** | 8 | python-code-style, file-organization, development-workflow, task-log-workflow, proposal-discussion-workflow, decision-making-principles, collaboration-guidelines |
| **Auto Attached** | 3 | rag-architecture, modular-design, testing-standards |
| **Manual** | 2 | workflow-definitions, (可能还有其他) |

### 潜在问题

1. **Always规则过多** (8个) - 可能导致上下文过长，影响性能
2. **规则可能有重复内容** - 需要检查重叠部分
3. **缺少特定场景规则** - Streamlit、Git、错误处理等
4. **规则粒度问题** - 某些规则可能过大，需要拆分

---

## 🎯 优化建议

### 1. 优化规则类型分配 ⭐⭐⭐

**问题**: Always规则过多（8个），可能影响AI性能

**建议**:

#### 方案A: 合并相关规则
- 将 `task-log-workflow`, `proposal-discussion-workflow` 合并到 `development-workflow`
- 将 `decision-making-principles`, `collaboration-guidelines` 合并为一个 `agent-collaboration.mdc`

#### 方案B: 转为Auto Attached或Manual
- `task-log-workflow` → Manual（仅在需要记录日志时引用）
- `proposal-discussion-workflow` → Auto Attached（当包含"方案"关键词时触发）

**推荐**: 方案B，保留灵活性，减少Always规则数量

---

### 2. 添加缺失的规则 ⭐⭐⭐

#### 2.1 Streamlit开发规范
```markdown
---
description: Streamlit开发规范
globs:
  - "app.py"
  - "pages/**"
  - "**/*streamlit*.py"
alwaysApply: false
---

# Streamlit开发规范

- UI组件规范
- 状态管理
- 页面路由
- 性能优化
```

#### 2.2 Git操作规范
```markdown
---
description: Git操作规范
globs:
  - "**/.git/**"
alwaysApply: false
---

# Git操作规范

- 提交消息格式
- 分支管理
- 合并策略
```

#### 2.3 错误处理模式
```markdown
---
description: 错误处理与异常管理
globs:
  - "src/**/*error*.py"
  - "src/**/*exception*.py"
alwaysApply: false
---

# 错误处理规范

- 异常分类
- 错误传播策略
- 用户友好错误消息
```

#### 2.4 配置管理规范
```markdown
---
description: 配置管理规范
globs:
  - "src/config/**"
  - "**/.env*"
alwaysApply: false
---

# 配置管理规范

- 环境变量管理
- 配置验证
- 默认值处理
```

---

### 3. 规则内容优化 ⭐⭐

#### 3.1 添加代码示例

**当前问题**: 某些规则缺少实际代码示例

**建议**: 在关键规则中添加：
- ✅ 正确示例
- ❌ 错误示例
- 💡 最佳实践示例

例如在 `python-code-style.mdc` 中添加更多对比例子。

#### 3.2 添加快速参考

**建议**: 每个规则文件末尾添加"快速参考"部分：

```markdown
## ⚡ 快速参考

### 核心要点
- [要点1]
- [要点2]

### 常见场景
- **场景1**: [处理方式]
- **场景2**: [处理方式]
```

#### 3.3 规则优先级

**建议**: 在README中定义规则优先级，避免冲突

```markdown
## 规则优先级

1. **Always规则** - 基础规范（最低优先级）
2. **Auto Attached规则** - 场景特定（中等优先级）
3. **Manual规则** - 明确引用（最高优先级）
```

---

### 4. 规则组织优化 ⭐⭐

#### 4.1 规则分类目录

**当前**: 所有规则在一个目录

**建议**: 创建分类目录

```
.cursor/rules/
├── workflows/          # 工作流规则
│   ├── development-workflow.mdc
│   ├── proposal-discussion-workflow.mdc
│   └── task-log-workflow.mdc
├── guidelines/        # 指导原则
│   ├── collaboration-guidelines.mdc
│   ├── decision-making-principles.mdc
│   └── code-style/
│       ├── python-code-style.mdc
│       └── streamlit-style.mdc
├── architecture/      # 架构规范
│   ├── rag-architecture.mdc
│   └── modular-design.mdc
└── testing/          # 测试规范
    └── testing-standards.mdc
```

**权衡**: 
- ✅ 更好的组织
- ❌ Cursor可能不支持嵌套目录（需验证）

#### 4.2 规则索引优化

**建议**: 在README中添加：
- 规则依赖关系图
- 规则使用场景矩阵
- 快速查找表

---

### 5. 规则维护机制 ⭐⭐⭐

#### 5.1 规则版本管理

**建议**: 在每个规则文件头部添加版本信息

```markdown
---
description: ...
version: 1.0.0
lastUpdated: 2025-11-02
source: AGENTS.md (lines 33-42)
---
```

#### 5.2 规则同步检查

**建议**: 创建脚本检查规则与AGENTS.md的同步

```python
# scripts/check_rules_sync.py
def check_rules_sync():
    """检查规则文件与AGENTS.md的同步状态"""
    pass
```

#### 5.3 规则使用统计

**建议**: 跟踪哪些规则最常被使用，优化高频规则

---

### 6. 规则性能优化 ⭐⭐

#### 6.1 规则长度优化

**当前问题**: 某些规则文件可能过长（>500行建议）

**建议**:
- 将长规则拆分为多个文件
- 使用"参见其他规则"减少重复
- 提取通用部分到独立规则

#### 6.2 规则加载优化

**建议**: 
- 使用更精确的glob模式，减少不必要的规则加载
- 将详细的参考内容移到Manual规则
- Always规则只保留核心要点

---

### 7. 规则测试与验证 ⭐

#### 7.1 规则有效性测试

**建议**: 创建测试用例验证规则是否有效

```python
# tests/rules/test_rule_effectiveness.py
def test_python_code_style_rule():
    """测试Python代码风格规则是否被正确应用"""
    pass
```

#### 7.2 规则冲突检测

**建议**: 检测规则之间的冲突或矛盾

---

### 8. 规则文档化 ⭐

#### 8.1 规则决策记录

**建议**: 创建 `RULE-DECISIONS.md` 记录规则设计的决策

```markdown
## 为什么将X规则设为Always？

决策: ...
理由: ...
影响: ...
```

#### 8.2 规则变更日志

**建议**: 在README或单独文件中记录规则变更历史

---

## 🎯 优先级排序

### 高优先级（立即实施）⭐⭐⭐

1. **减少Always规则数量**
   - 将部分规则转为Auto Attached或Manual
   - 合并相关规则

2. **添加缺失的规则**
   - Streamlit开发规范
   - 错误处理模式

3. **优化规则内容**
   - 添加代码示例
   - 添加快速参考

### 中优先级（近期实施）⭐⭐

4. **规则组织优化**
   - 改进规则索引
   - 添加使用场景矩阵

5. **规则维护机制**
   - 添加版本管理
   - 创建同步检查

### 低优先级（长期考虑）⭐

6. **规则性能优化**
   - 拆分长规则
   - 优化glob模式

7. **规则测试与验证**
   - 有效性测试
   - 冲突检测

---

## 📋 实施计划

### Phase 1: 规则类型优化（本周）

- [ ] 将 `task-log-workflow` 改为 Manual
- [ ] 将 `proposal-discussion-workflow` 改为 Auto Attached（关键词触发）
- [ ] 合并 `decision-making-principles` 和 `collaboration-guidelines`

**目标**: Always规则减少到5个以下

### Phase 2: 添加缺失规则（下周）

- [ ] 创建 `streamlit-development.mdc`
- [ ] 创建 `error-handling.mdc`
- [ ] 创建 `config-management.mdc`

### Phase 3: 内容优化（持续）

- [ ] 为所有规则添加代码示例
- [ ] 添加快速参考部分
- [ ] 优化规则长度

### Phase 4: 维护机制（长期）

- [ ] 添加版本管理
- [ ] 创建同步检查脚本
- [ ] 建立变更日志

---

## 🔍 规则冲突检查清单

当前需要检查的潜在冲突：

- [ ] `development-workflow.mdc` vs `proposal-discussion-workflow.mdc` - 代码修改流程
- [ ] `decision-making-principles.mdc` vs `collaboration-guidelines.mdc` - 决策相关
- [ ] `file-organization.mdc` vs `python-code-style.mdc` - 文件组织部分

---

## 📚 参考

- [Cursor Rules 最佳实践](https://docs.cursor.com/rules)
- 项目现有规则: `.cursor/rules/README.md`
- AGENTS.md映射: `.cursor/rules/AGENTS-MAPPING.md`

---

**创建日期**: 2025-11-02  
**状态**: 待实施  
**维护者**: 开发团队

