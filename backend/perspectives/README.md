# CLDFlow Perspective Generation System

基于 DDC（杜威十进制分类法）的动态视角生成系统，为 CLDFlow 提供多 Agent 分析的 Specialist Agent 角色模板。

## 核心特性

- **DDC 分类映射**：将研究问题映射到图书馆分类法的知识领域
- **模板继承体系**：基础模板 + 领域特化模板的可扩展架构
- **双维度评估**：反事实对比（Counterfactual）+ 结果导向（Action Advancement）
- **生产门禁**：只有通过评估的模板才允许部署

## 快速开始

```python
from backend.perspectives import PerspectiveGenerator, TemplateEvaluator

# 1. 生成视角
generator = PerspectiveGenerator()
result = generator.generate("房产税政策如何影响住房市场？")

for perspective in result.perspectives:
    print(f"- {perspective.name} (DDC: {perspective.ddc_class})")

# 2. 评估模板
evaluator = TemplateEvaluator()
report = evaluator.evaluate("ddc_330_economic")

print(f"反事实贡献: {report.counterfactual.mean_contribution}")
print(f"推进率: {report.action_advancement.advancement_rate * 100}%")
print(f"可通过: {report.can_deploy}")
```

## 目录结构

```
backend/perspectives/
├── __init__.py              # 模块入口
├── classifier.py            # 问题→DDC 分类器
├── generator.py             # 视角生成器
├── registry.py              # 模板注册表
├── evaluator.py             # 模板评估器
├── templates/               # 预置模板（版本控制）
│   ├── base/
│   │   └── base_analyst.yaml      # 基础模板
│   └── ddc_300/              # 社会科学模板
│       ├── 320_political.yaml     # 政治学
│       ├── 330_economic.yaml      # 经济学
│       ├── 340_legal.yaml         # 法律
│       └── 360_social.yaml        # 社会学
└── generated/               # 运行时生成（.gitignore）
```

## 模板体系

### DDC 分类映射

| DDC 类 | 领域 | 模板文件 | 核心关注 |
|--------|------|---------|---------|
| 320 | 政治学 | `320_political.yaml` | 政策机制、政府行为 |
| 330 | 经济学 | `330_economic.yaml` | 市场机制、价格动态 |
| 340 | 法律 | `340_legal.yaml` | 法规框架、合规要求 |
| 360 | 社会学 | `360_social.yaml` | 社会行为、公平性 |

### 模板继承

```yaml
# 子模板继承父模板并覆盖特定字段
inheritance:
  from: "base/base_analyst.yaml"
  override_fields: ["role_definition", "extraction_preferences"]
```

## 评估体系

### 1. 反事实对比（Counterfactual）

**问题**：这个视角模板对系统的真实贡献是多少？

**方法**：
```
贡献度 = 系统性能（有该视角）- 系统性能（用通用视角替代）
```

**通过标准**：
- 平均贡献 > 10 分
- 所有测试案例都有正向贡献

### 2. 结果导向（Action Advancement）

**问题**：这个视角在检索任务中有效推进了吗？

**判定标准**（三项需全满足）：
1. 找到新变量
2. 变量与角色专业匹配
3. 建立有效因果链

**通过标准**：推进率 ≥ 70%

### 评估报告示例

```yaml
metadata:
  evaluation_results:
    counterfactual:
      mean_contribution: 18.5
      min_contribution: 5.2
      passed: true
    action_advancement:
      advancement_rate: 0.82
      passed: true
    overall_pass: true
    can_deploy: true
```

## 测试

```bash
# 运行单元测试
pytest tests/unit/perspectives/ -v

# 运行特定测试
pytest tests/unit/perspectives/test_generator.py -v
```

## 扩展指南

### 添加新模板

1. 创建 YAML 文件：`templates/ddc_XXX/xxx_topic.yaml`
2. 继承基础模板并定义领域特定内容
3. 运行评估验证
4. 提交 PR

### 添加新 DDC 分类

1. 在 `classifier.py` 的 `KEYWORD_TO_DDC` 中添加关键词映射
2. 创建对应的模板文件
3. 更新文档

## 工作原理

```
用户问题
    ↓
[QuestionClassifier] → DDC 分类
    ↓
[TemplateRegistry] → 选择模板
    ↓
[PerspectiveGenerator] → 生成具体视角
    ↓
[TemplateEvaluator] → 评估可靠性
    ↓
可用的 Specialist Agent 角色
```

## 参考

- DDC 分类法：https://www.oclc.org/dewey.html
- 反事实评估：Galileo "Agent Roles in Dynamic Multi-Agent Workflows" (2024)
- Action Advancement：Galileo Action Advancement Metrics (2024)
