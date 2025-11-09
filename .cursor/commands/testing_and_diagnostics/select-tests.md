# /select-tests

## 1. Command Summary
- 目的：根据本次修改的文件快速筛选应执行的测试集。
- 触发时机：代码变更完成，准备运行单元测试前；规则 `testing_and_diagnostics_guidelines.mdc` 提醒时。
- 关联规则：`testing_and_diagnostics_guidelines.mdc`
- 依赖工具：`python tests/tools/agent_test_selector.py`

## 2. 输入
- 必需：本次修改文件相对路径列表。
- 可选：需要额外覆盖的测试文件或目录。

## 3. 执行步骤
1. 整理变更文件列表（含新增、修改、删除）。
2. 运行 `python tests/tools/agent_test_selector.py <files...>`。
3. 过滤输出，仅保留 `tests/unit/` 下的测试集合。
4. 记录推荐测试列表，为后续命令提供输入。

## 4. 输出
- 推荐测试文件列表。
- 若工具失败，记录失败原因并提示人工补救。

