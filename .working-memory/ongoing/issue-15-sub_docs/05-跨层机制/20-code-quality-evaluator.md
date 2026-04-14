# 代码生成质量评估与测试策略调研

## 核心问题

工程阶段生成代码时，如何设计评估器确保代码正确性、可读性和可维护性（基于 OpenAI 计划+任务拆分模式）。

---

## OpenAI 模式回顾

**核心原则**：
1. **计划（Plan）**：先制定详细的任务分解计划
2. **拆分（Split）**：大任务拆为小任务，每步只做一件事
3. **执行（Execute）**：每步执行后立即验证
4. **评估（Evaluate）**：通过才进入下一步

**对 CLDFlow 的意义**：
- 避免长代码生成后才发现错误
- 小步快跑，快速反馈
- 降低调试成本

---

## 备选方案对比

### 方案 A：实时验证（推荐）

**流程**：
```
生成代码片段 → 立即运行测试 → 通过 → 下一步
                ↓ 失败
           报错，重新生成
```

**验证方式**：
- 单元测试（pytest）
- 类型检查（mypy）
- 静态分析（ruff, black）
- 简单运行时测试

**优点**：即时反馈，错误定位精确
**缺点**：需要测试环境，增加执行时间

### 方案 B：事后审查

**流程**：
```
生成完整模块 → 批量审查 → 标记问题 → 一次性修复
```

**审查方式**：
- LLM 代码审查（Self-critique）
- 规则匹配（lint rules）
- 复杂度检查（cyclomatic complexity）

**优点**：整体视角，发现架构问题
**缺点**：错误发现晚，修复成本高

### 方案 C：混合模式（推荐）

**结合**：
- **小步验证**：每个函数生成后立即测试
- **模块审查**：模块完成后整体审查
- **集成验证**：所有模块联调测试

---

## 学术/工业界实践

### 1. Test-Driven Generation

**方法**：
1. 先生成测试用例
2. 再生成实现代码
3. 验证通过即完成

**Prompt 模板**：
```
为以下函数生成 pytest 测试用例：

def calculate_leverage_impact(weight_matrix, initial_state, node_idx):
    \"\"\"计算节点扰动对系统的影响\"\"\"
    ...

要求：
1. 覆盖正常输入
2. 覆盖边界条件（空矩阵、越界索引）
3. 每个测试用例有断言
```

### 2. Code Review Agent

**专用评估 Agent**：
```python
class CodeReviewAgent:
    """代码审查 Agent"""
    
    def review(self, code: str, context: Dict) -> Dict:
        """
        审查生成的代码
        
        Returns: {
            'passed': bool,
            'issues': [{severity, message, line}],
            'suggestions': [str]
        }
        """
        checks = [
            self._check_syntax(code),
            self._check_types(code),
            self._check_complexity(code),
            self._check_style(code),
            self._check_tests(code, context.get('tests'))
        ]
        
        all_passed = all(c['passed'] for c in checks)
        
        return {
            'passed': all_passed,
            'checks': checks
        }
```

### 3. 自动修复循环

**Self-Healing Code**：
```
生成 → 测试失败 → 分析错误 → 修复 → 重测
  ↑___________________________________↓
               （循环直到通过）
```

**最大重试次数**：3 次，避免无限循环

### 4. 静态分析工具集成

| 工具 | 用途 | 集成方式 |
|------|------|----------|
| **ruff** | 代码风格、import 检查 | 命令行调用 |
| **mypy** | 类型检查 | 命令行调用 |
| **bandit** | 安全检查 | 命令行调用 |
| **pytest** | 单元测试 | Python API |
| **coverage** | 测试覆盖率 | pytest 插件 |

---

## 推荐方案

### Phase 1 MVP：三层评估体系

```python
class CodeQualityEvaluator:
    """代码质量评估器"""
    
    def __init__(self, max_retries=3):
        self.max_retries = max_retries
        self.checks = [
            SyntaxCheck(),
            TypeCheck(),
            StyleCheck(),
            TestCheck()
        ]
    
    async def evaluate_and_fix(
        self,
        code: str,
        test_cases: List[Dict]
    ) -> Dict:
        """
        评估代码质量，失败则尝试修复
        """
        for attempt in range(self.max_retries + 1):
            # 运行所有检查
            results = []
            for check in self.checks:
                result = await check.run(code, test_cases)
                results.append(result)
            
            all_passed = all(r['passed'] for r in results)
            
            if all_passed:
                return {
                    'success': True,
                    'code': code,
                    'attempts': attempt + 1,
                    'checks': results
                }
            
            # 尝试修复
            if attempt < self.max_retries:
                code = await self._attempt_fix(code, results)
        
        # 超过重试次数
        return {
            'success': False,
            'code': code,
            'attempts': self.max_retries + 1,
            'checks': results,
            'error': 'Max retries exceeded'
        }
    
    async def _attempt_fix(self, code: str, failed_checks: List[Dict]) -> str:
        """基于失败的检查尝试修复代码"""
        
        fix_prompt = f"""
        以下代码未通过质量检查，请修复：
        
        ```python
        {code}
        ```
        
        失败项：
        {format_failures(failed_checks)}
        
        请输出修复后的完整代码。
        """
        
        fixed_code = await llm.generate(fix_prompt)
        return extract_code(fixed_code)
```

### 评估检查点设计

| 检查点 | 时机 | 工具 | 失败处理 |
|--------|------|------|----------|
| 语法检查 | 每函数生成后 | Python AST | 立即报错，重新生成 |
| 类型检查 | 模块完成后 | mypy | 标记类型警告，继续 |
| 单元测试 | 每函数后 | pytest | 失败则分析原因，修复 |
| 风格检查 | 模块完成后 | ruff | 自动格式化，不阻塞 |
| 集成测试 | 流水线完成后 | pytest | 失败则回滚到上一个版本 |

### 与 Conductor 集成

```python
class ObservableConductor:
    """带代码质量评估的编排器"""
    
    async def _generate_and_validate(
        self,
        task_description: str,
        expected_signature: str
    ) -> str:
        """
        生成代码并验证
        """
        # 1. 生成代码
        code = await self._generate_code(task_description)
        
        # 2. 语法检查
        if not self._check_syntax(code):
            raise CodeGenerationError("Syntax error")
        
        # 3. 生成测试
        tests = await self._generate_tests(expected_signature)
        
        # 4. 运行测试
        test_result = await self._run_tests(code, tests)
        
        if not test_result['passed']:
            # 尝试修复
            code = await self._fix_code(code, test_result['failures'])
            
            # 重新测试
            test_result = await self._run_tests(code, tests)
            if not test_result['passed']:
                raise CodeGenerationError("Tests failed after fix attempt")
        
        return code
```

---

## 测试生成策略

### 测试类型

| 类型 | 生成方式 | 验证重点 |
|------|----------|----------|
| **单元测试** | 基于函数签名和 docstring | 输入输出正确性 |
| **边界测试** | 基于参数类型推断 | 边界条件处理 |
| **集成测试** | 基于模块接口定义 | 模块间协作 |
| **回归测试** | 基于历史 bug | 防止重复错误 |

### 测试生成 Prompt

```python
TEST_GENERATION_PROMPT = """
为以下 Python 函数生成 pytest 测试用例：

函数：
{function_code}

要求：
1. 至少 3 个测试用例：正常输入、边界条件、异常输入
2. 使用 pytest 语法
3. 测试函数名以 test_ 开头
4. 每个测试有清晰的 docstring 说明测试目的
5. 使用有意义的断言，不只是 assert True

输出格式：
```python
import pytest

# 测试用例代码
```
"""
```

---

## 待决策事项

1. **评估严格度**
   - 选项 A：严格（任何失败都修复）
   - 选项 B：分级（语法必须过，风格可警告）**推荐**
   - 选项 C：宽松（仅测试失败才修复）

2. **自动修复次数**
   - 选项 A：1 次
   - 选项 B：3 次 **推荐**
   - 选项 C：5 次

3. **测试覆盖率要求**
   - 选项 A：核心函数 80% 覆盖
   - 选项 B：全部函数 60% 覆盖
   - 选项 C：不强制，有测试即可 **推荐**

4. **类型检查是否强制**
   - 选项 A：强制（所有函数加类型注解）**推荐**
   - 选项 B：推荐但不强制
   - **建议**：A，Python 3.12 + mypy 能发现很多问题

5. **是否生成回归测试**
   - 选项 A：发现 bug 后手动添加
   - 选项 B：自动从 bug 报告生成（复杂）
   - **建议**：A，Phase 1 手动管理

---

## 代码模板

```python
from dataclasses import dataclass
from typing import List, Dict, Callable
import subprocess
import tempfile
import ast

@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    details: Dict = None

class SyntaxCheck:
    """语法检查"""
    
    def run(self, code: str, context=None) -> CheckResult:
        try:
            ast.parse(code)
            return CheckResult(
                name='syntax',
                passed=True,
                message='Syntax OK'
            )
        except SyntaxError as e:
            return CheckResult(
                name='syntax',
                passed=False,
                message=f'Syntax error: {e}'
            )

class TestCheck:
    """单元测试检查"""
    
    async def run(self, code: str, test_cases: List[Dict]) -> CheckResult:
        # 写入临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            code_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
            f.write(self._generate_test_code(test_cases, code_file))
            test_file = f.name
        
        # 运行 pytest
        result = subprocess.run(
            ['pytest', test_file, '-v'],
            capture_output=True,
            text=True
        )
        
        passed = result.returncode == 0
        
        return CheckResult(
            name='tests',
            passed=passed,
            message='All tests passed' if passed else result.stdout,
            details={'returncode': result.returncode}
        )

class CodeQualityPipeline:
    """代码质量流水线"""
    
    def __init__(self):
        self.checks: List[Callable] = [
            SyntaxCheck(),
            # TypeCheck(),  # 需要 mypy
            # StyleCheck(),  # 需要 ruff
            TestCheck()
        ]
    
    async def evaluate(self, code: str, tests: List[Dict]) -> Dict:
        """运行完整质量评估"""
        results = []
        
        for check in self.checks:
            result = await check.run(code, tests)
            results.append(result)
            
            # 关键检查失败立即停止
            if result.name == 'syntax' and not result.passed:
                break
        
        return {
            'all_passed': all(r.passed for r in results),
            'results': results
        }
```

---

## 下一步

等待用户阅读后决策 5 个事项。
