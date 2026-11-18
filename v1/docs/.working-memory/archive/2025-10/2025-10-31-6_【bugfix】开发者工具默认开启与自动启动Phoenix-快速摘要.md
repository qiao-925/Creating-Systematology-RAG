# 2025-10-31 【bugfix】# 变更摘要

**【Task Type】**: bugfix
- 默认开启以下开发者工具：
  - 🐛 调试日志（LlamaDebugHandler）
  - 📈 查询追踪信息收集
  - 📊 Phoenix 可视化平台（启动开关默认开启）
- 应用启动时自动启动 Phoenix（若启用且未运行），无需手动点击。

## 涉及文件

- 修改：`src/ui_components.py`（默认开启 debug_mode_enabled、collect_trace、phoenix_enabled）
- 修改：`app.py`（应用启动时自动启动 Phoenix）

## 验证要点

1. 首次进入主页无需手动进入设置页，即可看到 Phoenix 已运行（如访问 `http://localhost:6006`）。
2. 设置页 → 开发者工具 中对应开关默认为开启状态。
3. 查询后可看到追踪信息（若界面包含对应展示）。

## 备注

- Phoenix 启动失败会被静默忽略，不影响主流程。

