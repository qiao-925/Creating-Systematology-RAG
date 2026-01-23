# /browser-start

## 1. Command Summary
- 目的：自动启动 Streamlit 应用并在浏览器中打开，准备进行可视化编辑或测试
- 触发时机：需要启动应用进行浏览器操作时
- 关联规则：`browser_visual_editor_integration.mdc`
- 依赖工具：`streamlit`、`@browser`

## 2. 输入
- 可选：端口号（默认 8501）、是否后台运行

## 3. 执行步骤
1. 检查应用是否已在运行（检查端口占用）
2. 如果未运行，启动 Streamlit 应用：
   ```bash
   uv run --no-sync python -m streamlit run app.py --server.port <port> --server.headless true
   ```
3. 等待应用启动完成（最多等待 10 秒）
4. 使用 `@browser` 打开 `http://localhost:<port>`
5. 截图记录初始状态
6. 提示用户可以进行可视化编辑或测试

## 4. 输出
- 应用启动状态（已运行/新启动）
- 访问地址
- 浏览器已打开确认
- 下一步操作建议（编辑/测试/审计）
