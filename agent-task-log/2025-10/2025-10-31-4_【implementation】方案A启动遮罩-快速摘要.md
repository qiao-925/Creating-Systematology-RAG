# 2025-10-31 【implementation】方案A：全屏启动遮罩 + 启动阶段初始化 - 快速摘要

**【Task Type】**: implementation
- 日期：2025-10-31
- 任务：消除首屏“白一下/像卡住”，实现全屏启动遮罩并后台初始化
- 文档类型：快速摘要

## 做了什么
- 新增“启动遮罩（Splash）”，首屏立即展示品牌化加载卡片与旋转动画。
- 将重型初始化（Embedding 模型预加载、Phoenix 启动）放到“启动阶段”执行，完成后设置 `boot_ready=True` 并 `st.rerun()`。
- 移除右侧 Phoenix 停止按钮，仅保留运行状态与访问链接（失败时可手动“启动Phoenix”重试）。

## 关键改动
- 文件：`src/ui_components.py`
  - `init_session_state()`：新增 `boot_ready`（默认 False）。
- 文件：`app.py`
  - 在进入主界面早期初始化会话状态；当 `boot_ready=False` 时渲染遮罩并执行：
    - `preload_embedding_model()`
    - `start_phoenix_ui(port=6006)`（失败在顶部报错）
    - 结束后 `boot_ready=True` 并 `st.rerun()`
  - 右侧调试栏：去掉“🛑 停止Phoenix”按钮，仅保留状态与访问链接；启动失败时保留“🚀 启动Phoenix”按钮以便重试。

## 预期效果
- 首屏无“白一下”，用户立即看到加载遮罩；初始化完成后切换到主界面。
- Phoenix 仍默认启动；若失败会在页面顶部呈现错误，且可手动重试。

## 验证要点
- 首次进入页面能看到遮罩；完成后自动进入主界面，无闪烁。
- 依赖缺失/端口占用时，顶部出现错误提示；右侧存在“启动Phoenix”重试按钮。
- 右侧不再有“停止Phoenix”按钮。
