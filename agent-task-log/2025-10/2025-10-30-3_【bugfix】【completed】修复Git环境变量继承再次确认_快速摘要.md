# 修复 Git 环境变量继承问题 - 再次确认修复

**日期**: 2025-10-30  
**类型**: Bug 修复  
**状态**: ✅ 已再次修复并确认

## 问题

用户反馈仍然无法 pull GitHub 仓库，怀疑文件没有保存好。

## 检查结果

检查 `src/git_repository_manager.py` 发现：
- ✅ 第 160 行：`_clone_repository` 已正确使用 `os.environ.copy()`
- ❌ 第 219 行：`_update_repository` 中的 `git pull` **未修复**

## 修复内容

### 再次修复 `_update_repository` 方法

**位置**：`src/git_repository_manager.py` 第 211-220 行

**之前**：
```python
pull_cmd = ['git', 'pull', 'origin', branch]
result = subprocess.run(
    pull_cmd,
    cwd=repo_path,
    capture_output=True,
    text=True,
    timeout=300,
    env={'GIT_TERMINAL_PROMPT': '0'}  # ❌ 没有继承环境变量
)
```

**修复后**：
```python
pull_cmd = ['git', 'pull', 'origin', branch]
# 继承当前进程的环境变量，确保 DNS、代理等配置可用
env = os.environ.copy()
env['GIT_TERMINAL_PROMPT'] = '0'  # 禁用交互式提示

result = subprocess.run(
    pull_cmd,
    cwd=repo_path,
    capture_output=True,
    text=True,
    timeout=300,
    env=env  # ✅ 使用完整的环境变量
)
```

## 确认修复完成

已验证以下两个关键位置都已正确修复：

1. **`_clone_repository` 方法**（第 160-168 行）
   - ✅ 使用 `os.environ.copy()`
   - ✅ 设置 `env['GIT_TERMINAL_PROMPT'] = '0'`

2. **`_update_repository` 方法**（第 214-223 行）
   - ✅ 使用 `os.environ.copy()`
   - ✅ 设置 `env['GIT_TERMINAL_PROMPT'] = '0'`

## 其他 subprocess.run 调用

检查了文件中所有 5 个 `subprocess.run` 调用：
1. ✅ `git --version` - 不需要环境变量
2. ✅ `git clone` - 已修复
3. ✅ `git checkout` - 本地命令，不需要环境变量
4. ✅ `git pull` - 已修复
5. ✅ `git rev-parse` - 本地命令，不需要环境变量

## 测试建议

1. 重启应用以确保加载最新代码
2. 尝试 clone/pull GitHub 仓库
3. 查看日志确认是否继承环境变量

## 相关文件

- `src/git_repository_manager.py` - 已修复
- `agent-task-log/2025-10-30-2_修复Git子进程环境变量继承问题_快速摘要.md` - 初版修复日志

