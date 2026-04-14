# 学术与政策研究可靠数据源调研

> 目标：为 CLDFlow 建立可靠的学术与政策研究数据源体系
> 调研日期：2026-04-12
> 核心诉求：来源可靠、可追溯、不误导用户

---

## 一、核心原则：分层可靠性体系

### 1.1 来源分级（按可靠性）

| 层级 | 来源类型 | 可靠性 | 使用场景 |
|------|---------|--------|---------|
| **Tier 1** | 政府官方、顶级期刊、国际组织 | ⭐⭐⭐⭐⭐ | 核心论据支撑 |
| **Tier 2** | 知名智库、学术预印本、官方统计 | ⭐⭐⭐⭐ | 补充分析、数据支持 |
| **Tier 3** | 主流媒体、行业报告、智库分析 | ⭐⭐⭐ | 背景信息、公众反应 |
| **Tier 4** | 博客、社论、非专家观点 | ⭐⭐ | 仅作参考，需标注 |

### 1.2 CLDFlow 的可靠性承诺

```
用户输出中每条因果链必须标注：
├── 来源层级（T1/T2/T3/T4）
├── 来源链接（可点击追溯）
├── 引用片段（原文摘录）
└── 置信度说明（基于来源质量）
```

---

## 二、学术数据库与 API

### 2.1 arXiv（预印本论文）

**特点**：
- 免费开放，无付费墙
- 覆盖物理、数学、计算机、定量生物学、金融等
- 更新快，未经同行评审（需注意质量差异）

**API**：
```python
import arxiv

# 搜索示例
search = arxiv.Search(
    query="causal inference policy evaluation",
    max_results=10,
    sort_by=arxiv.SortCriterion.SubmittedDate
)

for result in search.results():
    print(f"{result.title} - {result.pdf_url}")
```

**适用场景**：
- ✅ 最新方法论论文（如 D2D、Agentic RAG）
- ✅ 计算机科学、量化方法
- ⚠️ 注意：预印本质量参差不齐，需人工筛选

---

### 2.2 Semantic Scholar（学术图谱）

**特点**：
- 微软研究院开发，2 亿+ 论文
- 提供引用关系、影响力指标
- 免费 Academic Graph API

**API**：
```python
import requests

# 论文搜索
url = "https://api.semanticscholar.org/graph/v1/paper/search"
params = {
    "query": "fuzzy cognitive maps policy analysis",
    "fields": "title,authors,year,citationCount,openAccessPdf",
    "limit": 10
}
response = requests.get(url, params=params)
papers = response.json()["data"]
```

**优势**：
- ✅ 提供引用计数（影响力指标）
- ✅ 开放获取 PDF 链接
- ✅ 作者网络、论文关系图谱

---

### 2.3 Google Scholar（学术搜索）

**特点**：
- 覆盖面最广，包含期刊、会议、学位论文
- 引用数据权威
- **限制**：无官方 API，需爬虫或第三方库

**替代方案**：
```python
# 使用 scholarly 库（非官方，需谨慎使用）
from scholarly import scholarly

search_query = scholarly.search_pubs('system dynamics housing policy')
pub = next(search_query)
print(pub['bib']['title'])
print(pub['bib']['abstract'])
```

**注意事项**：
- ⚠️ 频繁请求会被封 IP
- ⚠️ 需设置请求间隔、代理池

---

### 2.4 领域特定期刊与数据库

| 领域 | 推荐数据库 | 访问方式 |
|------|-----------|---------|
| **经济学** | NBER, SSRN, EconLit | API / 开放获取 |
| **公共政策** | Policy Commons, JSTOR | 机构订阅 |
| **社会学** | SocArXiv, JSTOR | 开放获取 + 订阅 |
| **法律** | HeinOnline, Westlaw | 付费订阅 |
| **系统动力学** | System Dynamics Review | 出版社订阅 |

---

## 三、政策与政府数据源

### 3.1 美国政府数据源

| 数据源 | 内容 | API |
|--------|------|-----|
| **Census Bureau** | 人口、住房、经济数据 | ✅ 开放 API |
| **Bureau of Labor Statistics** | 就业、工资、物价 | ✅ 开放 API |
| **FRED (Federal Reserve)** | 经济指标、时间序列 | ✅ 开放 API |
| **Data.gov** | 联邦政府数据集门户 | ✅ 开放 API |
| **Congress.gov** | 法案、立法记录 | ✅ 开放 API |

**加州特定**：
- California Department of Finance
- Legislative Analyst's Office (LAO) - 非党派政策分析

---

### 3.2 国际组织数据

| 组织 | 数据类型 | API |
|------|---------|-----|
| **World Bank** | 全球发展指标 | ✅ 开放 API |
| **OECD** | 发达国家政策对比 | ✅ 开放 API |
| **UN Data** | 联合国统计数据 | ✅ 开放 API |
| **IMF** | 金融、经济指标 | ✅ 开放 API |

---

### 3.3 智库与研究机构

| 智库 | 领域 | 特点 |
|------|------|------|
| **Brookings Institution** | 经济、公共政策 | 高质量分析 |
| **Urban Institute** | 住房、社会政策 | 数据驱动 |
| **RAND Corporation** | 国防、公共政策 | 严谨研究方法 |
| **Pew Research Center** | 社会趋势、民意 | 调查数据权威 |
| **Tax Policy Center** | 税收政策 | 专业深度 |

---

## 四、来源可信度自动评估

### 4.1 域名分级规则

```python
TIER_1_DOMAINS = [
    # 政府机构
    '.gov', '.gov.uk', '.gov.au',
    # 国际组织
    'worldbank.org', 'oecd.org', 'un.org', 'imf.org',
    # 顶级期刊/出版社
    'nature.com', 'science.org', 'nejm.org', 'jstor.org',
]

TIER_2_DOMAINS = [
    # 学术预印本
    'arxiv.org', 'ssrn.com', 'socarxiv.org',
    # 智库
    'brookings.edu', 'urban.org', 'rand.org',
    'nber.org', 'piie.com',
    # 学术搜索
    'semanticscholar.org', 'scholar.google.com',
]

TIER_3_DOMAINS = [
    # 主流媒体
    'reuters.com', 'ap.org', 'bloomberg.com', 'economist.com',
    'nytimes.com', 'wsj.com', 'ft.com',
    # 行业分析
    'mckinsey.com', 'bcg.com',
]

def assess_source_tier(url: str) -> int:
    """自动评估来源层级"""
    url_lower = url.lower()
    
    for domain in TIER_1_DOMAINS:
        if domain in url_lower:
            return 1
    
    for domain in TIER_2_DOMAINS:
        if domain in url_lower:
            return 2
    
    for domain in TIER_3_DOMAINS:
        if domain in url_lower:
            return 3
    
    return 4  # 默认最低层级
```

### 4.2 学术论质量指标

```python
class AcademicPaperQuality:
    """学术论文质量评估"""
    
    def __init__(self, paper_metadata: dict):
        self.metadata = paper_metadata
    
    def quality_score(self) -> float:
        """综合质量评分 0-100"""
        score = 0
        
        # 1. 引用数（影响力）
        citations = self.metadata.get('citationCount', 0)
        score += min(citations / 10, 30)  # 最高 30 分
        
        # 2. 发表年份（时效性）
        year = self.metadata.get('year', 2020)
        if year >= 2023:
            score += 20  # 最新研究
        elif year >= 2018:
            score += 10  # 较新
        
        # 3. 开放获取（可验证性）
        if self.metadata.get('openAccessPdf'):
            score += 20
        
        # 4. 期刊/会议声誉（需预设列表）
        venue = self.metadata.get('venue', '')
        if venue in TOP_TIER_VENUES:
            score += 30
        elif venue in SECOND_TIER_VENUES:
            score += 15
        
        return score
```

### 4.3 引用验证机制

```python
def verify_citation(claim: str, source_doc: str) -> CitationVerification:
    """
    验证引用是否真实、准确
    
    1. 检查来源文档是否存在
    2. 检查引用片段是否在原文中
    3. 检查是否断章取义（上下文是否一致）
    """
    # 实现：使用 LLM 对比 claim 和 source_doc
    # 或使用文本匹配算法
    
    return CitationVerification(
        source_exists=True,
        fragment_found=True,
        context_consistent=True,
        confidence=0.95
    )
```

---

## 五、CLDFlow 数据源配置建议

### 5.1 Phase 1 数据源（MVP）

**优先集成**（免费、稳定、高质量）：

| 优先级 | 数据源 | 用途 |
|--------|--------|------|
| P0 | arXiv API | 最新方法论、技术论文 |
| P0 | Semantic Scholar API | 学术图谱、引用数据 |
| P0 | FRED (Federal Reserve) | 美国经济指标 |
| P1 | World Bank Open Data | 全球发展数据 |
| P1 | OECD Data | 发达国家政策对比 |
| P1 | Data.gov | 美国政府数据集 |
| P2 | Tavily / DuckDuckGo | 实时 Web 搜索（质量参差不齐，需过滤）|

### 5.2 来源质量过滤策略

```python
class SourceFilter:
    """来源质量过滤器"""
    
    def __init__(self):
        self.min_tier = 2  # 默认只接受 T2 及以上
    
    def filter_results(self, documents: List[Document]) -> List[Document]:
        """过滤低质量来源"""
        filtered = []
        
        for doc in documents:
            tier = assess_source_tier(doc.url)
            
            # Tier 1-2: 直接接受
            if tier <= 2:
                filtered.append(doc)
            
            # Tier 3: 需要额外验证
            elif tier == 3:
                if self._verify_tier3(doc):
                    filtered.append(doc)
            
            # Tier 4: 默认拒绝，除非人工确认
            else:
                continue
        
        return filtered
    
    def _verify_tier3(self, doc: Document) -> bool:
        """Tier 3 来源的额外验证"""
        # 检查作者权威性
        # 检查内容深度
        # 检查与其他 T1/T2 来源的一致性
        return True  # 简化实现
```

### 5.3 用户透明展示

```markdown
## 来源说明

本分析基于以下层级来源：

### Tier 1 - 权威来源（政府/顶级期刊）
- [U.S. Census Bureau] 2020 Census Housing Data
- [System Dynamics Review] Forrester (1961) Industrial Dynamics

### Tier 2 - 学术来源（预印本/智库）
- [arXiv:2508.05659] D2D: Diagrams to Dynamics
- [Brookings Institution] Housing Policy Analysis 2024

### Tier 3 - 参考来源（媒体/行业）
- [Reuters] California Housing Market Trends 2024

*注：Tier 4 来源已自动过滤，如需查看请联系管理员*
```

---

## 六、与检索评估的整合

```
[检索阶段]
    ↓
[来源过滤]  ← Tier 2+ 硬性过滤
    ↓
[质量评分]  ← 引用数、时效性、开放获取
    ↓
[覆盖率评估]  ← 检查清单
    ↓
[权威分布评估]  ← Tier 1/2/3 比例
    ↓
[停止决策]
```

**评估标准更新**：

| 维度 | 新增子项 |
|------|---------|
| **Coverage** | 各层级来源覆盖度 |
| **Novelty** | 新发现的 Tier 1 来源数 |
| **Authority** | Tier 1 ≥ 30%, Tier 2 ≥ 50%, Tier 3 ≤ 20% |
| **Verifiability** | 开放获取/可点击链接比例 |

---

## 七、参考资源

- **Semantic Scholar API**: https://api.semanticscholar.org/api-docs/
- **arXiv API**: https://arxiv.org/help/api/
- **World Bank Open Data**: https://data.worldbank.org/
- **FRED API**: https://fred.stlouisfed.org/docs/api/api_key.html
- **OECD Data Explorer**: https://data-explorer.oecd.org/

---

*Related: CLDFlow 输入增强评估 | 下一步: 工程架构设计（模块接口 + 流水线）*
