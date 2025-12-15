# Cursor (VS Code) 调试操作指南

> 基于 VS Code 的 Cursor IDE 调试功能完整指南，适用于 Python FastAPI 项目

> **提示**：如需对比 PyCharm 的调试配置，请参考 [IDE 调试功能对比文档](./IDE_DEBUG_COMPARISON.md)

---

## 1. 调试配置

### 1.1 创建调试配置文件

在项目根目录创建 `.vscode/launch.json` 文件：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI (Debug)",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "src.business.rag_api.fastapi_app:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
                "--reload"
            ],
            "jinja": true,
            "justMyCode": false,
            "env": {
                "PYTHONUNBUFFERED": "1",
                "LOG_LEVEL": "DEBUG"
            },
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

### 1.2 配置说明

- **`type: "debugpy"`**：使用 Python 调试器（debugpy）
- **`module: "uvicorn"`**：以模块方式运行 uvicorn
- **`args`**：传递给 uvicorn 的参数
  - `--reload`：代码修改后自动重载
- **`justMyCode: false`**：允许调试第三方库代码
- **`env`**：环境变量设置
  - `PYTHONUNBUFFERED=1`：禁用输出缓冲
  - `LOG_LEVEL=DEBUG`：启用调试日志

---

## 2. 设置断点

### 2.1 基本操作

1. **设置断点**：
   - 点击代码行号左侧的空白区域
   - 或按 `F9` 切换当前行的断点
   - 断点显示为红色圆点

2. **条件断点**：
   - 右键点击断点 → 选择"编辑断点"
   - 设置条件表达式，例如：`token_count < 3`
   - 只有满足条件时才会暂停

3. **日志断点**：
   - 右键点击断点 → 选择"编辑断点" → 选择"日志点"
   - 输入日志表达式，例如：`Chunk received: {chunk}`
   - 不会暂停执行，只记录日志

### 2.2 断点类型

- **普通断点**（红色圆点）：无条件暂停
- **条件断点**（黄色圆点）：满足条件时暂停
- **日志点**（橙色圆点）：记录日志，不暂停
- **禁用断点**（灰色圆点）：暂时禁用，不删除

---

## 3. 启动调试

### 3.1 方法一：使用调试面板

1. 按 `Ctrl+Shift+D`（Mac: `Cmd+Shift+D`）打开调试面板
2. 在顶部下拉菜单选择调试配置：`Python: FastAPI (Debug)`
3. 点击绿色播放按钮或按 `F5` 启动调试

### 3.2 方法二：使用命令面板

1. 按 `Ctrl+Shift+P`（Mac: `Cmd+Shift+P`）打开命令面板
2. 输入 `Debug: Start Debugging`
3. 选择调试配置

### 3.3 方法三：快捷键

- **`F5`**：启动调试（或继续执行）
- **`Shift+F5`**：停止调试
- **`Ctrl+Shift+F5`**：重启调试

---

## 4. 调试控制

### 4.1 基本控制按钮

调试工具栏（通常在顶部）包含以下按钮：

- **继续** (`F5`)：继续执行到下一个断点
- **单步跳过** (`F10`)：执行当前行，不进入函数内部
- **单步进入** (`F11`)：进入函数内部
- **单步跳出** (`Shift+F11`)：跳出当前函数
- **重启** (`Ctrl+Shift+F5`)：重新启动调试会话
- **停止** (`Shift+F5`)：停止调试

### 4.2 快捷键汇总

| 操作 | Windows/Linux | Mac |
|------|---------------|-----|
| 启动/继续调试 | `F5` | `F5` |
| 停止调试 | `Shift+F5` | `Shift+F5` |
| 重启调试 | `Ctrl+Shift+F5` | `Cmd+Shift+F5` |
| 单步跳过 | `F10` | `F10` |
| 单步进入 | `F11` | `F11` |
| 单步跳出 | `Shift+F11` | `Shift+F11` |
| 切换断点 | `F9` | `F9` |

---

## 5. 查看变量和表达式

### 5.1 变量面板

调试时，左侧面板显示：

- **变量 (Variables)**：
  - 当前作用域的所有变量
  - 展开对象查看属性
  - 右键变量可设置监视、复制值等

- **监视 (Watch)**：
  - 添加表达式监视
  - 例如：`chunk.raw['choices'][0]['delta']['content']`
  - 实时显示表达式值

- **调用堆栈 (Call Stack)**：
  - 显示函数调用链
  - 点击可跳转到对应位置

### 5.2 调试控制台

- **位置**：底部面板的"调试控制台"标签
- **功能**：
  - 执行 Python 表达式
  - 查看变量值：输入变量名按回车
  - 调用函数：`print(chunk.raw)`
  - 修改变量：`chunk_text = "test"`

### 5.3 悬停提示

- 将鼠标悬停在变量上，显示变量值
- 对于复杂对象，可展开查看属性

---

## 6. FastAPI 流式调试示例

### 6.1 关键断点位置

在 `src/business/rag_api/fastapi_routers/chat.py` 中设置断点：

```python
# 断点 1：流式调用开始前（第 133 行）
logger.debug("🚀 开始直接流式调用 DeepSeek API（绕过中间层）")

# 断点 2：每个 chunk 到达时（第 137 行）
for chunk in llm.stream_chat(messages):
    
    # 断点 3：检查 chunk 结构（第 143 行）
    chunk_text = ""
    
    # 断点 4：提取到 token 后（第 166 行）
    if chunk_text:
        token_count += 1
        
        # 断点 5：yield token 前（第 180 行）
        yield f"data: {json.dumps({'type': 'token', 'data': chunk_text}, ensure_ascii=False)}\n\n"
```

### 6.2 调试步骤

1. **设置断点**：在关键位置设置断点（建议使用条件断点：`token_count < 3`）

2. **启动调试**：按 `F5` 启动 FastAPI 服务

3. **触发请求**：在终端发送请求
   ```bash
   curl -X POST "http://127.0.0.1:8000/chat/stream" \
     -H "Content-Type: application/json" \
     -d '{"message": "测试"}'
   ```

4. **检查变量**：
   - 在断点处暂停时，查看 `chunk` 对象
   - 检查 `chunk.raw`、`chunk.delta`、`chunk.message`
   - 验证 `chunk_text` 是否正确提取

5. **单步执行**：
   - 使用 `F10` 单步跳过
   - 使用 `F11` 进入函数内部
   - 观察变量值的变化

### 6.3 常用调试表达式

在调试控制台或监视面板中使用：

```python
# 检查 chunk 类型
type(chunk)

# 检查 chunk 属性
dir(chunk)
hasattr(chunk, 'raw')
hasattr(chunk, 'delta')
hasattr(chunk, 'message')

# 查看 raw 内容
chunk.raw if hasattr(chunk, 'raw') else None

# 查看 delta 内容
chunk.delta.content if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content') else None

# 查看 message 内容
chunk.message.content if hasattr(chunk, 'message') and hasattr(chunk.message, 'content') else None

# 检查 token 长度
len(chunk_text) if chunk_text else 0
```

---

## 7. 高级调试技巧

### 7.1 条件断点

设置条件，只在特定情况下暂停：

```python
# 只在 token_count < 3 时暂停
token_count < 3

# 只在 chunk_text 为空时暂停
not chunk_text

# 只在 chunk.raw 存在时暂停
hasattr(chunk, 'raw') and chunk.raw is not None
```

### 7.2 日志断点

不暂停执行，只记录日志：

```
Chunk #{token_count}: raw={hasattr(chunk, 'raw')}, delta={hasattr(chunk, 'delta')}, text={chunk_text}
```

### 7.3 异常断点

1. 打开调试面板
2. 点击"断点"区域右上角的"断点设置"图标
3. 勾选"引发异常时中断"或"未捕获的异常时中断"

### 7.4 多进程调试

如果项目使用多进程，需要额外配置：

```json
{
    "name": "Python: FastAPI (Multi-Process)",
    "type": "debugpy",
    "request": "attach",
    "connect": {
        "host": "localhost",
        "port": 5678
    }
}
```

---

## 8. 常见问题

### 8.1 断点不生效

**问题**：设置了断点但程序不暂停

**解决方案**：
1. 确认调试配置正确（`justMyCode: false`）
2. 检查 Python 解释器路径是否正确
3. 确认代码已保存
4. 重启调试会话

### 8.2 无法进入第三方库

**问题**：无法进入 `llama_index` 等第三方库代码

**解决方案**：
- 设置 `"justMyCode": false"` 在 `launch.json` 中
- 或取消勾选调试面板中的"仅我的代码"

### 8.3 变量显示为 `<optimized out>`

**问题**：某些变量显示为优化掉的状态

**解决方案**：
- 这是 Python 优化导致的，正常现象
- 可以在代码中添加临时变量保存值
- 或使用调试控制台执行表达式

### 8.4 流式响应调试困难

**问题**：流式响应中，断点会影响实时性

**解决方案**：
1. 使用条件断点，只在特定条件下暂停
2. 使用日志断点，不暂停执行
3. 在关键位置添加日志输出
4. 使用 `logger.debug()` 记录变量值

---

## 9. 调试最佳实践

### 9.1 断点策略

- **开始调试时**：在入口函数设置断点
- **定位问题时**：在可疑代码附近设置断点
- **验证修复时**：在修复点设置断点，确认逻辑正确

### 9.2 日志与断点结合

- 使用日志记录正常流程
- 使用断点深入分析异常情况
- 日志断点用于不中断执行的观察

### 9.3 变量检查清单

调试流式响应时，检查以下变量：

- [ ] `chunk` 对象的类型和属性
- [ ] `chunk.raw` 是否存在及内容
- [ ] `chunk.delta` 是否存在及内容
- [ ] `chunk.message` 是否存在及内容
- [ ] `chunk_text` 是否正确提取
- [ ] `token_count` 是否正确递增
- [ ] `full_answer` 是否正确累加

### 9.4 性能考虑

- 避免在循环中设置无条件断点
- 使用条件断点限制暂停次数
- 调试完成后及时移除断点

---

## 10. 参考资源

- [VS Code 调试文档](https://code.visualstudio.com/docs/editor/debugging)
- [Python 调试文档](https://code.visualstudio.com/docs/python/debugging)
- [debugpy 文档](https://github.com/microsoft/debugpy)

---

## 11. 快速参考卡片

### 调试快捷键

```
F5          - 启动/继续调试
Shift+F5    - 停止调试
Ctrl+Shift+F5 - 重启调试
F9          - 切换断点
F10         - 单步跳过
F11         - 单步进入
Shift+F11   - 单步跳出
```

### 调试面板快捷键

```
Ctrl+Shift+D - 打开调试面板
Ctrl+Shift+Y - 打开调试控制台
```

### 常用命令

```
Debug: Start Debugging    - 启动调试
Debug: Stop Debugging     - 停止调试
Debug: Restart Debugging  - 重启调试
Debug: Toggle Breakpoint   - 切换断点
```

---

**最后更新**：2025-12-15  
**版本**：v1.0
