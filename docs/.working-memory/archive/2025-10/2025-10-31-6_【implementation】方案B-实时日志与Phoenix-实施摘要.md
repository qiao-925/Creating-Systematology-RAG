# 2025-10-31 【implementation】方案B：实时日志 + Phoenix 链接（实施摘要）

**【Task Type】**: implementation
- 日期：2025-10-31
- 目标：在聊天页集成开发者调试能力，便于学习与问题诊断
- 变更文件：`app.py`

## 功能点
- 在聊天页底部新增折叠面板“🐛 开发者调试（实时日志 + Phoenix）”
  - Phoenix：一键启动/停止，显示访问链接 `http://localhost:6006`
  - 实时日志：读取 `logs/YYYY-MM-DD.log` 的最后 200 行，便于快速定位问题

## 关键实现
- 新增导入：
```startLine:endLine:app.py
from src.phoenix_utils import (
    is_phoenix_running,
    start_phoenix_ui,
    stop_phoenix_ui,
    get_phoenix_url,
)
```
- UI 面板：
```startLine:endLine:app.py
    # ========== 开发者调试（实时日志 + Phoenix） ==========
    st.markdown("---")
    with st.expander("🐛 开发者调试（实时日志 + Phoenix）", expanded=False):
        ...
        # Phoenix 启停 + 链接
        # 读取 logs/ 当日日志最后 200 行并展示
```

## 使用说明
- 在主页聊天页底部展开“开发者调试”即可：
  - 点击“🚀 启动Phoenix”后，会自动注册 LlamaIndex 追踪；再次点击“🛑 停止Phoenix”可关闭。
  - “实时日志”区域实时展示当日日志尾部，遇到异常可点击“刷新页面（↻）”获取最新日志。

## 后续拓展（可选）
- 将 `HybridQueryEngine.stream_query()` 的 `status` 事件接入实时状态流（更贴近“过程可视化”）。
- 在设置页与主页公用一套 Phoenix 控制（避免重复按钮）。
