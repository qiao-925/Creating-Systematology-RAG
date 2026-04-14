# 因果层 - 数据格式与接口标准化调研

## 核心问题

定义 CausalLink 数据结构、共享 CLD 存储格式、以及与 FCM 层的接口契约，确保各层之间数据流转无缝衔接。

---

## CausalLink 数据结构

### 完整字段定义

```json
{
  "causal_link": {
    "id": "uuid-v4",
    "source": {
      "id": "node-001",
      "name": "政府住房补贴",
      "canonical_name": "政府住房补贴",
      "aliases": ["财政补贴", "购房补贴"],
      "type": "policy_variable",
      "domain": "政府政策"
    },
    "target": {
      "id": "node-002",
      "name": "房价",
      "canonical_name": "房价",
      "aliases": [],
      "type": "economic_variable",
      "domain": "市场机制"
    },
    "polarity": "+",
    "strength": "medium",
    "evidence": {
      "quotes": ["政府补贴增加了购房需求，推动房价上涨 (p.12)"],
      "sources": ["政策分析报告2024"],
      "confidence": 0.85
    },
    "provenance": {
      "extracted_by": "policy-perspective-agent",
      "extraction_time": "2026-04-13T10:30:00Z",
      "document_id": "doc-001",
      "paragraph_range": "12-15"
    },
    "validation": {
      "conflicts": [],
      "supporting_agents": ["policy", "economic"],
      "opposing_agents": [],
      "disagreement_score": 0.0,
      "status": "confirmed"
    },
    "metadata": {
      "tags": ["housing", "subsidy", "price"],
      "notes": "短期内正向，长期可能因供需平衡而减弱"
    }
  }
}
```

### 字段详细说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| **id** | UUID | ✅ | 全局唯一标识 |
| **source** | Object | ✅ | 源节点完整信息 |
| **target** | Object | ✅ | 目标节点完整信息 |
| **polarity** | Enum | ✅ | "+", "-", "?"（不确定）|
| **strength** | Enum | ⚪ | "weak", "medium", "strong", "unknown" |
| **evidence.quotes** | [String] | ✅ | 原文引用（支持多条）|
| **evidence.sources** | [String] | ⚪ | 来源文档标识 |
| **evidence.confidence** | Float | ⚪ | LLM 自评置信度 (0-1) |
| **provenance.extracted_by** | String | ✅ | 提取 Agent ID |
| **provenance.extraction_time** | ISO8601 | ✅ | 提取时间戳 |
| **validation.status** | Enum | ✅ | "pending", "confirmed", "conflicted", "rejected" |
| **validation.conflicts** | [Object] | ⚪ | 冲突详情 |

### 简化版（Phase 1 MVP）

```json
{
  "causal_link": {
    "id": "uuid",
    "source": "政府住房补贴",
    "target": "房价",
    "polarity": "+",
    "evidence": "政府补贴增加了购房需求，推动房价上涨 (p.12)",
    "extracted_by": "policy-agent",
    "extraction_time": "2026-04-13T10:30:00Z",
    "status": "confirmed"
  }
}
```

---

## 共享 CLD 存储格式

### 方案对比

| 方案 | 格式 | 优点 | 缺点 | 推荐 |
|------|------|------|------|------|
| A | **JSON** | 通用，易解析，人可读 | 图结构不直观 | **Phase 1 推荐** |
| B | **GraphML** | 标准图格式，可视化工具支持 | 复杂，学习曲线 | Phase 2 |
| C | **NetworkX pickle** | Python 原生，功能完整 | 非通用，版本锁 | 内部使用 |
| D | **Neo4j Cypher** | 数据库持久化，查询强 | 依赖外部服务 | 生产环境 |
| E | **GraphQL** | 灵活查询，前后端通用 | 复杂度高 | API 层 |

### 推荐：JSON + NetworkX 双格式

**存储层（JSON）**：
```json
{
  "cld_document": {
    "id": "cld-001",
    "name": "Prop13 住房影响分析",
    "created_at": "2026-04-13T10:00:00Z",
    "source_question": "分析 Prop 13 对加州住房的影响",
    "nodes": [
      {"id": "n1", "name": "政府住房补贴", "type": "policy", "x": 100, "y": 200},
      {"id": "n2", "name": "房价", "type": "economic", "x": 300, "y": 200}
    ],
    "edges": [
      {
        "id": "e1",
        "source": "n1",
        "target": "n2",
        "polarity": "+",
        "weight": 0.7,
        "evidence": "..."
      }
    ],
    "metadata": {
      "total_agents": 3,
      "conflicts_pending": 2,
      "validated_links": 15
    }
  }
}
```

**计算层（NetworkX DiGraph）**：
```python
import networkx as nx

# 从 JSON 加载
G = nx.DiGraph()
for node in json_data['nodes']:
    G.add_node(node['id'], **node)
for edge in json_data['edges']:
    G.add_edge(edge['source'], edge['target'], **edge)

# 使用 NetworkX 进行图分析
cycles = list(nx.simple_cycles(G))  # 检测反馈环
in_degree = dict(G.in_degree())     # 入度分析
```

---

## 节点（Variable）数据结构

```json
{
  "node": {
    "id": "uuid",
    "canonical_name": "政府住房补贴",
    "aliases": ["财政补贴", "购房补贴", "政府补助"],
    "normalized_name": "government_housing_subsidy",
    "type": "policy_variable",
    "domain": "政府政策",
    "attributes": {
      "measurable": true,
      "unit": "美元/年",
      "typical_range": "0-50000"
    },
    "provenance": {
      "first_introduced_by": "policy-agent",
      "merging_history": [
        {"from": "财政补贴", "to": "政府住房补贴", "similarity": 0.92}
      ]
    }
  }
}
```

---

## CLD → FCM 层接口契约

### 输出规范（CLD 层 → FCM 层）

```python
class CLDOutput:
    """CLD 层输出给 FCM 层的标准格式"""
    
    graph: nx.DiGraph  # 共享 CLD
    
    @property
    def to_fcm_input(self) -> dict:
        """转换为 FCM 层输入"""
        return {
            "nodes": [
                {
                    "id": node_id,
                    "name": data['canonical_name'],
                    "domain": data.get('domain', 'unknown'),
                    "incident_edges": [
                        {
                            "from": edge[0],
                            "to": edge[1],
                            "polarity": edge_data['polarity'],
                            "evidence_count": len(edge_data.get('evidence', []))
                        }
                        for edge in self.graph.in_edges(node_id, data=True)
                    ]
                }
                for node_id, data in self.graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "polarity": data['polarity'],
                    "evidence": data.get('evidence', []),
                    "validation_status": data.get('status', 'pending')
                }
                for u, v, data in self.graph.edges(data=True)
            ],
            "metadata": {
                "total_nodes": self.graph.number_of_nodes(),
                "total_edges": self.graph.number_of_edges(),
                "cycles": list(nx.simple_cycles(self.graph)),
                "pending_conflicts": self._count_pending_conflicts()
            }
        }
```

### 接口校验

```python
from pydantic import BaseModel, validator
from typing import Literal, List

class CausalLinkSchema(BaseModel):
    """Pydantic 校验模型"""
    source: str
    target: str
    polarity: Literal["+", "-", "?"]
    evidence: str
    
    @validator('source', 'target')
    def not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('节点名不能为空')
        return v.strip()

# 使用
link_data = {"source": "A", "target": "B", "polarity": "+", "evidence": "..."}
validated = CausalLinkSchema(**link_data)
```

---

## 序列化与持久化

### 文件存储结构

```
sessions/
└── {session_id}/
    ├── cld/
    │   ├── raw_extractions/          # 各 Agent 原始输出
    │   │   ├── policy-agent.json
    │   │   ├── economic-agent.json
    │   │   └── social-agent.json
    │   ├── merged_nodes.json          # 节点归并结果
    │   ├── conflicts.json             # 冲突报告
    │   └── shared_cld.json            # 最终共享 CLD
    ├── fcm/
    │   └── ...
    └── d2d/
        └── ...
```

### 版本控制

```json
{
  "version": "1.0.0",
  "format": "cldflow-cld-v1",
  "compatibility": {
    "minimum_reader": "1.0.0",
    "backward_compatible_to": "1.0.0"
  }
}
```

---

## 待决策事项

1. **置信度字段是否保留**
   - 选项 A：保留（增加 Prompt 复杂度，但后续有用）
   - 选项 B：删除（Phase 1 简化，通过冲突检测推断置信度）
   - **建议**：B，减少复杂度

2. **节点 ID 生成策略**
   - 选项 A：UUID（全局唯一，无意义）
   - 选项 B：规范化名称哈希（可读，可能冲突）
   - 选项 C：混合（canonical_name + 短 UUID 后缀）
   - **建议**：A 或 C，B 有哈希冲突风险

3. **strength 字段是否保留**
   - 选项 A：保留（Agent 评估因果强度）
   - 选项 B：删除（Phase 1 只保留极性）
   - **建议**：B，Phase 1 只关注定性有无，FCM 层再量化

4. **GraphML 支持时机**
   - 选项 A：Phase 1 就支持（便于可视化调试）
   - 选项 B：Phase 2 添加（专注 MVP）
   - **建议**：B，JSON + NetworkX 足够调试

5. **接口校验严格度**
   - 选项 A：Pydantic 严格校验（推荐，提前发现错误）
   - 选项 B：宽松字典（灵活但易出错）
   - **建议**：A，生产环境必需

---

## 代码模板

### 数据结构定义

```python
from dataclasses import dataclass
from typing import List, Optional, Literal
from datetime import datetime

@dataclass
class Node:
    id: str
    canonical_name: str
    aliases: List[str]
    domain: str
    
@dataclass
class CausalLink:
    id: str
    source: Node
    target: Node
    polarity: Literal["+", "-", "?"]
    evidence: str
    extracted_by: str
    extraction_time: datetime
    status: Literal["pending", "confirmed", "conflicted"]
    
@dataclass
class SharedCLD:
    nodes: List[Node]
    links: List[CausalLink]
    
    def to_networkx(self) -> nx.DiGraph:
        """转换为 NetworkX 图"""
        G = nx.DiGraph()
        for node in self.nodes:
            G.add_node(node.id, **node.__dict__)
        for link in self.links:
            G.add_edge(link.source.id, link.target.id, **link.__dict__)
        return G
    
    @classmethod
    def from_networkx(cls, G: nx.DiGraph) -> "SharedCLD":
        """从 NetworkX 图加载"""
        # 实现略
        pass
```

---

## 下一步

等待用户决策以上 5 个事项，确认后产出完整数据层实现代码。
