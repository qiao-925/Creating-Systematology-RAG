# Python 代码规范详细指南

> **文档类型**: AGENTS 规则扩展文档  
> **版本**: 1.0  
> **更新日期**: 2025-11-03  
> **关联文档**: [AGENTS.md](../../AGENTS.md) 第115-129行

---

## 📖 文档说明

本文档是 **AGENTS.md 的扩展文档**，专门针对**Python 代码规范**。

由于代码规范内容较多且会持续更新，本文档从 AGENTS.md 中独立出来，便于维护和扩展。

### 适用范围

- ✅ **所有 Python 代码文件**
- ✅ **业务代码和测试代码**
- ✅ **工具脚本和配置脚本**

### 强制要求

所有代码必须遵循本文档中的**强制要求**，这些是项目的核心规范，不允许违反。

---

## 1. 使用日志代替 print

**强制要求**：所有业务代码必须使用 logging 模块记录日志，禁止使用 print 语句

- 使用内置的 `logging` 模块来记录日志，可以控制日志级别、输出格式和输出位置
- 通过 `src.logger.setup_logger` 创建日志器，统一管理日志配置
- **日志级别选择**：
     - `logger.info()` - 一般信息性消息（如操作成功、进度信息）
     - `logger.warning()` - 警告消息（如降级处理、配置问题）
     - `logger.error()` - 错误消息（如操作失败、异常情况）
     - `logger.debug()` - 调试信息（如详细步骤、调试输出）
- **保留 print 的情况（允许）**：
  - 测试代码中的示例输出（如 `__main__` 块中的测试）
  - 文档示例代码（如 docstring 中的 `>>> print(...)`）
     - 启动脚本中的关键信息输出
- 所有业务逻辑代码必须使用 logger，确保日志可追踪、可配置

---

## 2. 使用枚举（Enum）

对于固定的常量集合，使用枚举类型可以使代码更清晰、类型安全

   - 使用 `from enum import Enum` 定义枚举类
   - 枚举值应使用清晰的名称，如 `StrategyType`, `ModuleType`
   - 优先使用枚举替代字符串字面量常量

---

## 3. 代码文件行数限制

**强制要求**：所有代码文件不允许超过 300 行

   - 单个文件必须控制在 300 行以内（强制规定）
   - 如果遇到复杂任务，必须拆分成多个文件
   - 拆分原则：按功能模块、职责边界进行合理拆分
   - 目标：保持整个项目的可读性和可维护性

---

## 4. 代码注释与文档字符串（Docstring）

**强制要求**：所有公共函数、类必须有文档字符串（Docstring）

- **Docstring 是什么**：函数或类定义后的三引号字符串（`"""..."""`），用于说明功能、参数、返回值
- **规范要求**：
  - 所有公共函数、类必须有 docstring
  - 使用 Google 风格或 NumPy 风格
  - 包含参数说明、返回值说明、异常说明（如有）
- **代码注释**：在复杂逻辑处添加注释，解释**为什么这样做**，而不是**做什么**
  - 注释应该解释设计决策和实现原因（算法选择、架构决策、异常处理策略、性能优化、兼容性处理等）
- **示例**：
  ```python
  def process_documents(
      docs: List[Document],
      config: Optional[Dict] = None
  ) -> List[ProcessedDocument]:
      """处理文档列表
    
      Args:
          docs: 待处理的文档列表
          config: 可选配置字典
      
      Returns:
          处理后的文档列表
      
      Raises:
          ValueError: 当docs为空时抛出
      """
      # ✅ 好的注释：ChromaDB要求路径必须存在，使用parents=True和exist_ok=True避免异常
      self.persist_dir.mkdir(parents=True, exist_ok=True)
  ```

---

## 5. 类型提示（Type Hints）

**强制要求**：所有函数必须提供类型提示

- 使用 `typing` 模块（`List`, `Dict`, `Optional`, `Union` 等）
- 返回类型必须明确指定，无返回值使用 `-> None`
- **示例**：
  ```python
  from typing import List, Optional, Dict
  
  def process_documents(
      docs: List[Document],
      config: Optional[Dict[str, str]] = None
  ) -> List[ProcessedDocument]:
      """处理文档列表"""
      pass
  ```

---

## 6. 导入规范

**强制要求**：导入语句必须按顺序分组，每组之间空行分隔

- **导入顺序**：
  1. 标准库导入（按字母顺序）
  2. 第三方库导入（按字母顺序）
  3. 本地模块导入（按模块路径层次）
- **禁止**：避免 `from module import *`
- **示例**：
  ```python
  # 标准库
  import os
  from pathlib import Path
  from typing import List, Optional
  
  # 第三方库
  import chromadb
  from llama_index.core import VectorStoreIndex
  
  # 本地模块
  from src.config import config
  from src.logger import setup_logger
  ```

---

## 7. 命名规范

**强制要求**：遵循统一的命名约定

- **类名**：大驼峰（`PascalCase`）：`BaseEmbedding`, `VectorStoreIndex`
- **函数/变量**：蛇形命名（`snake_case`）：`build_index`, `embedding_model`
- **常量**：全大写下划线分隔：`MAX_RETRIES`, `DEFAULT_TOP_K`
- **私有成员**：单下划线前缀：`_internal_method`, `_cache`

---

## 8. 异常处理规范

**强制要求**：必须使用具体的异常类型，避免裸露的 `except:`

- 使用具体的异常类型（`ValueError`, `KeyError`, `FileNotFoundError` 等）
- 捕获异常后必须记录日志或重新抛出
- 关键路径必须有异常处理
- **示例**：
  ```python
  try:
      result = process_data()
  except ValueError as e:
      logger.error(f"数据验证失败: {e}")
      raise
  except Exception as e:
      logger.exception("未知错误")
      raise RuntimeError(f"处理失败: {e}") from e
  ```

---

## 9. 使用上下文管理器

**强制要求**：文件操作和资源管理必须使用 `with` 语句

- 文件操作必须使用 `with open()` 确保自动关闭
- 数据库连接、网络连接等资源管理使用上下文管理器
- 确保资源正确释放，避免资源泄露
- **示例**：
  ```python
  # ✅ 正确：使用 with 语句
  with open('file.txt', 'r') as f:
      content = f.read()
  
  # ❌ 错误：手动管理资源
  f = open('file.txt', 'r')
  content = f.read()
  f.close()  # 可能忘记关闭
  ```

---

## 📚 参考文档

- AGENTS.md 主文档：代码规范核心要求
- 错误处理详细指南：`.cursor/agents-expansion/AGENTS-EXPANSION-ERROR_HANDLING.md`
- Python 官方文档：[PEP 8](https://pep8.org/), [PEP 257](https://www.python.org/dev/peps/pep-0257/)

---

**最后更新**: 2025-11-03

