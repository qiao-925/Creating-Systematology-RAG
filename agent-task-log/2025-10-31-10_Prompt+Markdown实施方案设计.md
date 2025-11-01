# Prompt + Markdown 实施方案设计

**日期**：2025-10-31  
**目的**：详细设计 Prompt+Markdown 输出格式化方案的实现  
**优先级**：⭐⭐  
**状态**：方案设计

---

## 一、方案概览

### 1.1 核心思路

**三层架构**：
1. **Prompt增强层** - 添加Markdown格式约束
2. **LLM生成层** - 生成Markdown格式的回答
3. **后处理层** - 校验、修复、美化Markdown

### 1.2 设计原则

- **渐进式实施**：先简单后复杂，逐步优化
- **降级策略**：格式失败时回退到原文
- **用户感知**：保持回答质量，不因格式影响内容
- **最小侵入**：不改变现有架构，模块化集成

---

## 二、Prompt 设计

### 2.1 核心Prompt模板

#### 模板一：标准学术回答（推荐）

```markdown
你是一位系统科学领域的资深专家，请用Markdown格式回答用户问题。

【知识库参考】
{context_str}

【回答格式要求】
1. 使用Markdown语法，包含标题、列表、强调等
2. 结构清晰：核心概念 → 关键要点 → 应用场景 → 思考总结
3. 适度使用**粗体**强调重要概念
4. 列表使用规范的Markdown格式（- 或 1.）
5. 在回复末尾标注"📚 来源"部分（如知识库内容充分）

【回答内容要求】
1. 充分理解问题的深层含义
2. 优先使用知识库权威信息
3. 结合专业知识深入分析
4. 提供完整、有洞察力的回答

用户问题：{question}

请严格按照上述格式要求回答（必须使用Markdown语法）：
```

#### 模板二：简洁版（快速回答）

```markdown
你是一位系统科学领域的资深专家。

【知识库参考】
{context_str}

请用Markdown格式回答：
- 使用 ## 作为主标题
- 使用列表（-）组织要点
- 用**粗体**强调核心概念
- 末尾标注📚 来源

用户问题：{question}

回答（Markdown格式）：
```

#### 模板三：详细版（深度分析）

```markdown
你是一位系统科学领域的资深专家，请撰写一份结构化的学术回答。

【知识库参考】
{context_str}

【回答格式】
# 核心概念

## 1. 定义与特征
{详细定义和关键特征}

## 2. 理论基础
{相关理论和原理}

## 3. 应用与实践
{实际应用和案例}

## 4. 思考与展望
{深度思考和前沿方向}

📚 参考文献
{引用来源}

【要求】
- 严格遵循上述Markdown结构
- 使用>引用块展示关键概念
- 表格展示对比信息
- 突出关键术语（**粗体**）

用户问题：{question}

回答：
```

### 2.2 Prompt特性

**优点**：
- ✅ 明确格式要求，减少不遵循概率
- ✅ 提供结构模板，引导生成
- ✅ 保留学术风格与深度

**注意事项**：
- ⚠️ 模板长度增加token消耗
- ⚠️ 需测试与优化迭代
- ⚠️ 随问题类型调整

---

## 三、后处理设计

### 3.1 后处理流程

```
LLM原始输出
  ↓
Markdown解析（检测格式是否正确）
  ↓
格式修复（补充缺失的Markdown语法）
  ↓
引用替换（将 [1] 转换为可点击链接）
  ↓
美化优化（添加换行、空白）
  ↓
最终输出
```

### 3.2 后处理模块

#### 模块一：Markdown解析器

```python
import re
from typing import str, bool

class MarkdownValidator:
    """Markdown格式校验器"""
    
    def validate(self, text: str) -> bool:
        """检查是否包含Markdown语法"""
        # 检测标题、列表、粗体等
        has_title = bool(re.search(r'^#+\s', text, re.MULTILINE))
        has_list = bool(re.search(r'^\s*[-*+]\s|^\s*\d+\.\s', text, re.MULTILINE))
        has_bold = bool(re.search(r'\*\*.*?\*\*', text))
        
        # 至少包含一种格式
        return has_title or has_list or has_bold
    
    def get_format_score(self, text: str) -> float:
        """计算格式完整度分数（0-1）"""
        scores = []
        
        # 检查标题
        if re.search(r'^#+\s', text, re.MULTILINE):
            scores.append(0.3)
        
        # 检查列表
        if re.search(r'^\s*[-*+]\s|^\s*\d+\.\s', text, re.MULTILINE):
            scores.append(0.3)
        
        # 检查粗体
        if re.search(r'\*\*.*?\*\*', text):
            scores.append(0.2)
        
        # 检查引用块
        if re.search(r'^>\s', text, re.MULTILINE):
            scores.append(0.1)
        
        # 检查分割线
        if re.search(r'^---', text, re.MULTILINE):
            scores.append(0.1)
        
        return sum(scores)
```

#### 模块二：格式修复器

```python
class MarkdownFixer:
    """Markdown格式修复器"""
    
    def fix(self, text: str) -> str:
        """修复常见的格式问题"""
        fixed = text
        
        # 1. 确保标题前后有空行
        fixed = re.sub(r'(^#+\s[^\n]+)', r'\n\1\n', fixed, flags=re.MULTILINE)
        
        # 2. 确保列表前后有空行
        fixed = re.sub(r'([^\n])\n([-*+]|\d+\.)', r'\1\n\n\2', fixed)
        fixed = re.sub(r'([-*+]|\d+\.)\n([^\n])', r'\1\n\2\n', fixed)
        
        # 3. 统一列表符号（统一使用 -）
        fixed = re.sub(r'^\s*[*+]\s', '- ', fixed, flags=re.MULTILINE)
        
        # 4. 修复过度换行
        fixed = re.sub(r'\n{3,}', '\n\n', fixed)
        
        return fixed.strip()
```

#### 模块三：引用替换器

```python
class CitationReplacer:
    """引用替换器"""
    
    def replace_citations(self, text: str, sources: List[dict]) -> str:
        """将文本中的 [1] 格式替换为可点击链接"""
        # 匹配 [数字] 格式
        pattern = r'\[(\d+)\]'
        
        def replace_func(match):
            num = int(match.group(1))
            if 1 <= num <= len(sources):
                source = sources[num - 1]
                # 生成可点击链接（Markdown格式）
                return f"[{num}](#citation_{num})"
            return match.group(0)
        
        return re.sub(pattern, replace_func, text)
```

### 3.3 降级策略

如果Markdown解析失败或格式不达标：

```python
def process_response(raw_answer: str, sources: List[dict]) -> str:
    """主处理函数（带降级）"""
    
    # Step 1: 校验格式
    validator = MarkdownValidator()
    if not validator.validate(raw_answer):
        # 降级：返回原文（不做格式化）
        logger.warning("Markdown格式校验失败，返回原文")
        return raw_answer
    
    # Step 2: 格式修复
    fixer = MarkdownFixer()
    fixed_answer = fixer.fix(raw_answer)
    
    # Step 3: 引用替换
    replacer = CitationReplacer()
    final_answer = replacer.replace_citations(fixed_answer, sources)
    
    # Step 4: 最终校验
    score = validator.get_format_score(final_answer)
    if score < 0.5:
        # 格式质量过低，返回原文
        logger.warning(f"格式质量过低({score:.2f})，返回原文")
        return raw_answer
    
    return final_answer
```

---

## 四、集成方案

### 4.1 文件结构

```
src/
├── query_engine.py              # 修改：添加格式增强
├── chat_manager.py              # 修改：添加格式增强
└── response_formatter.py        # 新增：格式化模块
    ├── __init__.py
    ├── validator.py             # Markdown校验
    ├── fixer.py                 # 格式修复
    ├── replacer.py              # 引用替换
    └── templates.py             # Prompt模板
```

### 4.2 集成步骤

#### Step 1: 创建格式化模块（```src/response_formatter.py```）

```python
"""响应格式化模块"""

from typing import List, Dict
from .validator import MarkdownValidator
from .fixer import MarkdownFixer
from .replacer import CitationReplacer

class ResponseFormatter:
    """响应格式化器"""
    
    def __init__(self, enable_formatting: bool = True):
        self.enable_formatting = enable_formatting
        self.validator = MarkdownValidator()
        self.fixer = MarkdownFixer()
        self.replacer = CitationReplacer()
    
    def format(self, raw_answer: str, sources: List[Dict] = None) -> str:
        """格式化回答"""
        if not self.enable_formatting:
            return raw_answer
        
        # 校验格式
        if not self.validator.validate(raw_answer):
            return raw_answer
        
        # 修复格式
        fixed = self.fixer.fix(raw_answer)
        
        # 替换引用
        if sources:
            final = self.replacer.replace_citations(fixed, sources)
        else:
            final = fixed
        
        return final
```

#### Step 2: 修改 QueryEngine（```src/query_engine.py```）

```python
from src.response_formatter import ResponseFormatter

class QueryEngine:
    def __init__(self, ...):
        # ... 现有代码 ...
        self.formatter = ResponseFormatter(enable_formatting=True)
    
    def query(self, question: str, ...):
        # ... 现有查询逻辑 ...
        
        # 提取答案
        answer = str(response)
        
        # 格式化答案
        answer = self.formatter.format(answer, sources)
        
        return answer, sources, trace_info
```

#### Step 3: 修改 ChatManager（```src/chat_manager.py```）

```python
from src.response_formatter import ResponseFormatter

class ChatManager:
    def __init__(self, ...):
        # ... 现有代码 ...
        self.formatter = ResponseFormatter(enable_formatting=True)
    
    def chat(self, message: str):
        # ... 现有对话逻辑 ...
        
        # 格式化答案
        answer = self.formatter.format(answer, sources)
        
        return answer, sources
```

### 4.3 Prompt注入点

需要修改LlamaIndex的Prompt注入点：

**Option A: 通过CitationQueryEngine的text_qa_template**

```python
from llama_index.core import PromptTemplate

markdown_qa_template = PromptTemplate("""
你是系统科学领域的资深专家，请用Markdown格式回答。

【知识库参考】
{context_str}

【回答格式】
使用##标题、-列表、**粗体**等Markdown语法，结构清晰。

问题：{query_str}

回答（Markdown格式）：
""")

self.query_engine = CitationQueryEngine.from_args(
    self.index,
    llm=self.llm,
    similarity_top_k=self.similarity_top_k,
    citation_chunk_size=self.citation_chunk_size,
    text_qa_template=markdown_qa_template,  # 注入自定义模板
)
```

**Option B: 通过查询时传入自定义Prompt**

需要使用LlamaIndex的query_bundle机制，需要在业务中搜索相关用法。

---

## 五、测试策略

### 5.1 单元测试

```python
def test_markdown_validator():
    """测试Markdown校验器"""
    validator = MarkdownValidator()
    
    # 测试有效Markdown
    valid_md = "# 标题\n\n- 列表项1\n- 列表项2"
    assert validator.validate(valid_md) == True
    
    # 测试无效Markdown
    invalid_md = "普通文本，没有格式"
    assert validator.validate(invalid_md) == False

def test_markdown_fixer():
    """测试格式修复器"""
    fixer = MarkdownFixer()
    
    # 测试标题修复
    input_text = "标题1\n内容"
    expected = "# 标题1\n\n内容"
    assert fixer.fix(input_text) == expected
```

### 5.2 集成测试

```python
def test_query_engine_with_formatting():
    """测试查询引擎的格式化功能"""
    # 创建引擎
    engine = QueryEngine(index_manager)
    engine.formatter = ResponseFormatter(enable_formatting=True)
    
    # 执行查询
    answer, sources, _ = engine.query("什么是系统？")
    
    # 验证返回的是Markdown格式
    assert "#" in answer or "##" in answer  # 至少有一个标题
    assert any(char in answer for char in ["-", "*", "**"])  # 有列表或强调
```

### 5.3 A/B测试

- 对照组：原有Prompt（无格式约束）
- 实验组：Markdown Prompt
- 评估指标：
  - 用户满意度
  - 回答清晰度
  - 阅读速度

---

## 六、实施路线图

### Phase 1: 基础框架（3天）

- [x] 创建格式化模块框架
- [ ] 实现MarkdownValidator
- [ ] 实现MarkdownFixer
- [ ] 实现CitationReplacer
- [ ] 单元测试

### Phase 2: 简单Prompt（2天）

- [ ] 设计简洁版Prompt模板
- [ ] 集成到QueryEngine
- [ ] 集成到ChatManager
- [ ] 端到端测试

### Phase 3: Prompt优化（3天）

- [ ] 设计标准学术Prompt模板
- [ ] 测试不同模板效果
- [ ] 根据反馈迭代优化
- [ ] 收集用户反馈

### Phase 4: 高级特性（5天）

- [ ] 详细版Prompt模板
- [ ] 问题分类 → 模板选择
- [ ] 用户偏好设置
- [ ] A/B测试框架

---

## 七、风险评估

### 7.1 技术风险

| 风险 | 可能性 | 影响 | 应对 |
|------|--------|------|------|
| 模型不遵循格式 | 中 | 高 | 降级策略 + Prompt迭代 |
| 格式修复出错 | 低 | 中 | 保守修复 + 回退 |
| 性能下降 | 低 | 低 | 轻量级实现 |
| token消耗增加 | 高 | 中 | 精简模板 |

### 7.2 业务风险

| 风险 | 可能性 | 影响 | 应对 |
|------|--------|------|------|
| 用户不适应 | 中 | 低 | 提供开关，可关闭 |
| 回答质量下降 | 低 | 高 | 降级策略 |
| 格式不统一 | 中 | 中 | 持续优化Prompt |

---

## 八、参考资源

1. [Markdown语法规范](https://spec.commonmark.org/)
2. [LlamaIndex Custom Prompts](https://docs.llamaindex.ai/en/stable/module_guides/deploying/prompts/guides/customization/)
3. [Prompt Engineering Guide](https://www.promptingguide.ai/)
4. [DeepSeek API文档](https://api-docs.deepseek.com/)

---

## 九、总结

**推荐路径**：
1. 先实现基础格式化（Phase 1-2）
2. 用简洁Prompt验证
3. 按反馈迭代优化（Phase 3）
4. 再叠加高级特性（Phase 4）

**成功标准**：
- 80%+ 的回答生成有效Markdown
- 用户满意度提升明显
- 无新bug，性能稳定

---

**作者**：AI Agent  
**最后更新**：2025-10-31

