# IDE 调试功能对比：Cursor (VS Code) vs PyCharm

> FastAPI 项目在 Cursor (VS Code) 和 PyCharm 中的调试配置与功能对比

---

## 1. 快速对比表

| 功能 | Cursor (VS Code) | PyCharm |
|------|------------------|---------|
| **配置文件** | `.vscode/launch.json` | `.idea/runConfigurations/` 或 GUI 配置 |
| **配置方式** | JSON 文件 | GUI 界面或 XML 文件 |
| **断点设置** | 点击行号左侧 | 点击行号左侧 |
| **条件断点** | ✅ 支持 | ✅ 支持 |
| **日志断点** | ✅ 支持 | ✅ 支持 |
| **异常断点** | ✅ 支持 | ✅ 支持 |
| **多进程调试** | ✅ 支持（需配置） | ✅ 支持（需配置） |
| **远程调试** | ✅ 支持 | ✅ 支持 |
| **调试控制台** | ✅ 支持 | ✅ 支持 |
| **变量监视** | ✅ 支持 | ✅ 支持 |
| **热重载** | ✅ 支持（--reload） | ✅ 支持（需配置） |
| **第三方库调试** | ✅ 支持（justMyCode: false） | ✅ 支持（默认） |
| **学习曲线** | 中等 | 较陡 |
| **配置复杂度** | 低（JSON） | 中等（GUI） |

---

## 2. Cursor (VS Code) 调试配置

### 2.1 配置文件位置

**文件**：`.vscode/launch.json`

### 2.2 完整配置示例

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

### 2.3 关键配置项

- **`type: "debugpy"`**：使用 Python 调试器
- **`module: "uvicorn"`**：以模块方式运行
- **`justMyCode: false`**：允许调试第三方库
- **`--reload`**：代码修改后自动重载

### 2.4 启动方式

1. 按 `F5` 或点击调试面板的播放按钮
2. 选择配置：`Python: FastAPI (Debug)`
3. 服务在 `http://127.0.0.1:8000` 启动

### 2.5 快捷键

| 操作 | 快捷键 |
|------|--------|
| 启动/继续 | `F5` |
| 停止 | `Shift+F5` |
| 单步跳过 | `F10` |
| 单步进入 | `F11` |
| 单步跳出 | `Shift+F11` |
| 切换断点 | `F9` |

---

## 3. PyCharm 调试配置

### 3.1 配置方式

PyCharm 提供两种配置方式：

#### 方式一：GUI 配置（推荐）

1. **打开运行配置**：
   - 点击右上角运行配置下拉菜单
   - 选择 "Edit Configurations..."

2. **创建新配置**：
   - 点击左上角 `+` 号
   - 选择 "Python"

3. **配置参数**：
   - **Name**: `FastAPI (Debug)`
   - **Script path**: 留空
   - **Module name**: `uvicorn`
   - **Parameters**: `src.business.rag_api.fastapi_app:app --host 127.0.0.1 --port 8000 --reload`
   - **Working directory**: 项目根目录
   - **Environment variables**: 
     ```
     PYTHONUNBUFFERED=1
     LOG_LEVEL=DEBUG
     ```
   - **Python interpreter**: 选择项目使用的 Python 解释器

4. **高级选项**：
   - 取消勾选 "Attach to subprocess"（除非需要多进程调试）
   - 勾选 "Gevent compatible"（如果使用 gevent）

#### 方式二：XML 配置文件

**文件位置**：`.idea/runConfigurations/FastAPI_Debug.xml`

```xml
<component name="ProjectRunConfigurationManager">
  <configuration default="false" name="FastAPI (Debug)" type="PythonConfigurationType" factoryName="Python">
    <module name="Creating-Systematology-RAG" />
    <option name="INTERPRETER_OPTIONS" value="" />
    <option name="PARENT_ENVS" value="true" />
    <envs>
      <env name="PYTHONUNBUFFERED" value="1" />
      <env name="LOG_LEVEL" value="DEBUG" />
    </envs>
    <option name="SDK_HOME" value="$PROJECT_DIR$/.venv/bin/python" />
    <option name="WORKING_DIRECTORY" value="$PROJECT_DIR$" />
    <option name="IS_MODULE_SDK" value="true" />
    <option name="ADD_CONTENT_ROOTS" value="true" />
    <option name="ADD_SOURCE_ROOTS" value="true" />
    <EXTENSION ID="PythonCoverageRunConfigurationExtension" runner="coverage.py" />
    <option name="SCRIPT_NAME" value="" />
    <option name="PARAMETERS" value="src.business.rag_api.fastapi_app:app --host 127.0.0.1 --port 8000 --reload" />
    <option name="SHOW_COMMAND_LINE" value="false" />
    <option name="EMULATE_TERMINAL" value="false" />
    <option name="MODULE_MODE" value="true" />
    <option name="MODULE_NAME" value="uvicorn" />
    <method v="2" />
  </configuration>
</component>
```

### 3.2 启动方式

1. **方法一**：点击右上角运行配置下拉菜单，选择 `FastAPI (Debug)`，点击绿色调试按钮（🐛）
2. **方法二**：右键点击 `fastapi_app.py`，选择 "Debug 'FastAPI (Debug)'"
3. **方法三**：使用快捷键 `Shift+F9`（如果已设置默认配置）

### 3.3 快捷键

| 操作 | 快捷键 |
|------|--------|
| 启动/继续 | `F9` |
| 停止 | `Ctrl+F2` (Windows/Linux) / `Cmd+F2` (Mac) |
| 单步跳过 | `F8` |
| 单步进入 | `F7` |
| 单步跳出 | `Shift+F8` |
| 切换断点 | `Ctrl+F8` (Windows/Linux) / `Cmd+F8` (Mac) |
| 运行到光标 | `Alt+F9` |

### 3.4 调试面板

PyCharm 的调试面板包含：

- **Variables**：当前作用域的变量
- **Watches**：监视的表达式
- **Frames**：调用堆栈
- **Console**：调试控制台（可执行 Python 代码）

---

## 4. 功能详细对比

### 4.1 断点功能

#### Cursor (VS Code)

- **设置断点**：点击行号左侧或按 `F9`
- **条件断点**：右键断点 → "编辑断点" → 输入条件
- **日志断点**：右键断点 → "编辑断点" → 选择"日志点"
- **异常断点**：调试面板 → 断点设置图标 → 勾选异常选项

#### PyCharm

- **设置断点**：点击行号左侧或按 `Ctrl+F8`
- **条件断点**：右键断点 → "More" → 输入条件
- **日志断点**：右键断点 → "More" → 勾选 "Log evaluated expression"
- **异常断点**：Run → View Breakpoints → Exception Breakpoints

**对比**：两者功能相似，PyCharm 的异常断点配置更直观。

### 4.2 变量查看

#### Cursor (VS Code)

- **变量面板**：左侧调试面板的 "Variables" 区域
- **悬停提示**：鼠标悬停在变量上显示值
- **调试控制台**：底部面板，可执行表达式
- **监视**：添加表达式到 "Watch" 面板

#### PyCharm

- **变量面板**：底部调试面板的 "Variables" 标签
- **悬停提示**：鼠标悬停在变量上显示值（更详细）
- **评估表达式**：`Alt+F8` 打开表达式评估窗口
- **监视**：右键变量 → "Add to Watches"

**对比**：PyCharm 的变量查看更详细，支持更多数据类型可视化。

### 4.3 第三方库调试

#### Cursor (VS Code)

需要在 `launch.json` 中设置：
```json
"justMyCode": false
```

#### PyCharm

默认支持调试第三方库，无需额外配置。

**对比**：PyCharm 默认支持，VS Code 需要显式配置。

### 4.4 热重载

#### Cursor (VS Code)

在 uvicorn 参数中添加 `--reload`：
```json
"args": [
    "src.business.rag_api.fastapi_app:app",
    "--reload"
]
```

#### PyCharm

在运行配置的 Parameters 中添加 `--reload`：
```
src.business.rag_api.fastapi_app:app --reload
```

**对比**：两者都需要在参数中添加 `--reload`，配置方式相同。

### 4.5 多进程调试

#### Cursor (VS Code)

需要创建附加配置：
```json
{
    "name": "Python: Attach",
    "type": "debugpy",
    "request": "attach",
    "connect": {
        "host": "localhost",
        "port": 5678
    }
}
```

#### PyCharm

在运行配置中勾选 "Attach to subprocess"。

**对比**：PyCharm 配置更简单，VS Code 需要创建单独的附加配置。

---

## 5. 实际使用场景对比

### 5.1 快速调试

**Cursor (VS Code)**：
- ✅ 配置文件简单（JSON）
- ✅ 启动快速（`F5`）
- ✅ 轻量级

**PyCharm**：
- ✅ GUI 配置直观
- ✅ 功能更丰富
- ⚠️ 启动稍慢

### 5.2 复杂调试

**Cursor (VS Code)**：
- ✅ 配置灵活（JSON）
- ✅ 支持多种调试器
- ⚠️ 需要手动配置

**PyCharm**：
- ✅ 自动检测配置
- ✅ 智能提示
- ✅ 集成度高

### 5.3 团队协作

**Cursor (VS Code)**：
- ✅ `.vscode/launch.json` 可提交到版本控制
- ✅ 配置共享方便

**PyCharm**：
- ⚠️ `.idea/` 目录通常不提交（个人配置）
- ⚠️ 需要手动导出/导入配置

---

## 6. 推荐选择

### 选择 Cursor (VS Code) 如果：

- ✅ 喜欢轻量级 IDE
- ✅ 需要快速启动和调试
- ✅ 团队使用 VS Code/Cursor
- ✅ 配置需要版本控制
- ✅ 喜欢 JSON 配置方式

### 选择 PyCharm 如果：

- ✅ 需要强大的调试功能
- ✅ 喜欢 GUI 配置界面
- ✅ 需要智能代码分析
- ✅ 项目复杂，需要深度集成
- ✅ 个人使用，不需要共享配置

---

## 7. 迁移指南

### 7.1 从 Cursor 迁移到 PyCharm

1. **导出配置**：
   - 复制 `.vscode/launch.json` 中的参数
   - 在 PyCharm 中创建对应的运行配置

2. **配置映射**：
   - `module` → PyCharm 的 "Module name"
   - `args` → PyCharm 的 "Parameters"
   - `env` → PyCharm 的 "Environment variables"
   - `cwd` → PyCharm 的 "Working directory"

### 7.2 从 PyCharm 迁移到 Cursor

1. **读取配置**：
   - 查看 PyCharm 运行配置的参数
   - 创建对应的 `launch.json`

2. **配置映射**：
   - "Module name" → `module`
   - "Parameters" → `args`（数组形式）
   - "Environment variables" → `env`（对象形式）
   - "Working directory" → `cwd`

---

## 8. 常见问题

### 8.1 Cursor (VS Code)

**Q: 断点不生效？**

A: 检查 `justMyCode: false` 是否设置，确认 Python 解释器路径正确。

**Q: 无法进入第三方库？**

A: 设置 `"justMyCode": false"` 在 `launch.json` 中。

**Q: 热重载不工作？**

A: 确认 `--reload` 参数已添加到 `args` 数组。

### 8.2 PyCharm

**Q: 调试时找不到模块？**

A: 检查 "Working directory" 和 "Python interpreter" 设置。

**Q: 断点在第三方库不生效？**

A: PyCharm 默认支持，如果不行，检查 "Attach to subprocess" 设置。

**Q: 热重载不工作？**

A: 确认 `--reload` 参数已添加到 "Parameters"。

---

## 9. 最佳实践

### 9.1 通用建议

1. **使用条件断点**：避免在循环中无条件暂停
2. **使用日志断点**：观察变量变化而不中断执行
3. **清理断点**：调试完成后及时移除或禁用
4. **使用监视**：添加关键表达式到监视面板

### 9.2 Cursor (VS Code) 特定

1. **版本控制配置**：将 `.vscode/launch.json` 提交到仓库
2. **多配置管理**：为不同场景创建多个配置
3. **使用任务**：结合 `tasks.json` 实现自动化

### 9.3 PyCharm 特定

1. **模板配置**：创建运行配置模板供团队使用
2. **使用书签**：标记重要代码位置
3. **使用代码片段**：快速插入调试代码

---

## 10. 参考资源

### Cursor (VS Code)

- [VS Code 调试文档](https://code.visualstudio.com/docs/editor/debugging)
- [Python 调试文档](https://code.visualstudio.com/docs/python/debugging)
- [debugpy 文档](https://github.com/microsoft/debugpy)

### PyCharm

- [PyCharm 调试文档](https://www.jetbrains.com/help/pycharm/debugging-code.html)
- [PyCharm 运行配置](https://www.jetbrains.com/help/pycharm/run-debug-configuration.html)
- [PyCharm 断点文档](https://www.jetbrains.com/help/pycharm/using-breakpoints.html)

---

**最后更新**：2025-12-15  
**版本**：v1.0
