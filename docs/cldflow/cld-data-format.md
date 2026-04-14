# CLD层 - 数据格式与接口设计

> 不变量I-2：CLD输出必须符合JSON Schema
> 不变量I-5：层间数据边界解析（Parse, Don't Validate）
> 默认参数见：`docs/CLDFlow-defaults.md` CLD层

---

## Phase 1 MVP 数据结构

### CausalLink

```python
from pydantic import BaseModel, field_validator
from typing import Literal
from uuid import uuid4

class CausalLink(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    target: str
    polarity: Literal["+", "-"]
    evidence: str
    extracted_by: str

    @field_validator('source', 'target')
    @classmethod
    def not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('节点名不能为空，请确保每个节点有描述性名称')
        return v.strip()

    @field_validator('evidence')
    @classmethod
    def evidence_required(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('证据不能为空，每条因果链必须附原文引用')
        return v.strip()
```

### CLDNode

```python
class CLDNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    aliases: list[str] = []
    domain: str = "unknown"

    @field_validator('name')
    @classmethod
    def not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('节点名不能为空')
        return v.strip()
```

### SharedCLD

```python
import networkx as nx

class SharedCLD(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_question: str
    nodes: list[CLDNode]
    edges: list[CausalLink]

    def to_networkx(self) -> nx.DiGraph:
        G = nx.DiGraph()
        for node in self.nodes:
            G.add_node(node.id, **node.model_dump())
        for edge in self.edges:
            G.add_edge(edge.source, edge.target, **edge.model_dump())
        return G

    @classmethod
    def from_networkx(cls, G: nx.DiGraph, source_question: str) -> "SharedCLD":
        # 反向转换
        ...
```

---

## Phase 2 扩展字段

| 字段 | Phase 1 | Phase 2 | 说明 |
|------|---------|---------|------|
| confidence | ❌ 删除 | ✅ 贝叶斯可信区间 | D23, D14 |
| strength | ❌ 删除 | ✅ FCM层量化 | D25 |
| weight | ❌ | ✅ 数值权重 | FCM层 |
| GraphML | ❌ | ✅ 可视化调试 | D26 |
| node type | ✅ domain字段 | ✅ 更细分类 | — |

---

## 存储格式

**Phase 1**：JSON（通用、人可读、易解析）

**内部计算**：NetworkX DiGraph（图分析、环检测、入度分析）

**序列化路径**：JSON → `SharedCLD` Pydantic model → NetworkX DiGraph

---

## 接口校验（不变量I-5）

每层入口必须通过 Pydantic 验证：

```python
# CLD层输出 → FCM层输入
def validate_cld_output(cld: SharedCLD) -> SharedCLD:
    """不变量I-7：自审通过才传递"""
    errors = []
    if len(cld.nodes) < 3:
        errors.append("节点数<3，因果图过小，请确保提取了足够的变量")
    if len(cld.edges) < 2:
        errors.append("边数<2，因果关系过少，请检查提取质量")
    # 检查孤立节点
    connected = set()
    for edge in cld.edges:
        connected.add(edge.source)
        connected.add(edge.target)
    isolated = [n.name for n in cld.nodes if n.id not in connected and n.name not in connected]
    if isolated:
        errors.append(f"孤立节点: {isolated}，请确保每个节点至少参与一条因果关系")
    if errors:
        raise ValueError("; ".join(errors))
    return cld
```

---

## 已决策事项

| 决策 | 结论 | 来源 |
|------|------|------|
| 置信度字段 | Phase 1删除 | D23 |
| 节点ID策略 | UUID | D24 |
| strength字段 | Phase 1删除 | D25 |
| GraphML支持 | Phase 2 | D26 |
| 接口校验 | Pydantic严格模式 | D27 |

---

*整合自 issue-15-sub_docs: 12-cld-data-format.md*
