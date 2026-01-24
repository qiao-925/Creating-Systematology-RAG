# 浏览器测试详细说明

## 1. 测试类型

| 测试类型 | 说明 | 命令 |
|----------|------|------|
| 功能测试 | 验证 UI 功能是否正常 | `browser-test` |
| 可访问性测试 | 验证可访问性标准 | `browser-a11y` |
| 视觉回归测试 | 验证 UI 外观是否变化 | `browser-visual-regression` |
| 重启测试 | 重启应用并测试 | `browser-restart-and-test` |

## 2. 执行流程

### 2.1 功能测试

```bash
# 执行功能测试
python scripts/run_browser_tests.py --type functional

# 测试内容：
# - 页面加载
# - 组件交互
# - 数据流动
```

### 2.2 可访问性测试

```bash
# 执行可访问性测试
python scripts/run_browser_tests.py --type a11y

# 测试内容：
# - WCAG 标准
# - 键盘导航
# - 屏幕阅读器兼容性
```

### 2.3 视觉回归测试

```bash
# 执行视觉回归测试
python scripts/run_browser_tests.py --type visual

# 测试内容：
# - 截图对比
# - 布局变化
# - 样式变化
```

## 3. 前提条件

### 3.1 环境要求

- Streamlit 应用已启动
- 浏览器驱动已安装（Playwright）

### 3.2 启动应用

```bash
# 启动 Streamlit 应用
streamlit run frontend/main.py

# 或使用 Make 命令
make run
```

## 4. 结果处理

### 4.1 成功

```
✅ 功能测试：通过
✅ 可访问性测试：通过
✅ 视觉回归测试：通过
```

### 4.2 失败

```
❌ 功能测试：失败
   - test_chat_input: 元素未找到

下一步：
1. 检查元素选择器
2. 验证页面结构
3. 触发诊断流程
```

## 5. 脚本使用

### 5.1 完整测试

```bash
# 执行所有浏览器测试
python scripts/run_browser_tests.py --all
```

### 5.2 参数说明

| 参数 | 说明 |
|------|------|
| `--type` | 测试类型（functional/a11y/visual） |
| `--all` | 执行所有测试 |
| `--headless` | 无头模式 |
| `--screenshots` | 保存截图 |
