# /run-unit-tests

## 1. Command Summary
- 目的：执行针对性的单元测试，验证本次代码改动。
- 触发时机：完成 `/select-tests` 并获得测试列表后；规则 `testing_and_diagnostics_guidelines.mdc` 提醒时。
- 关联规则：`testing_and_diagnostics_guidelines.mdc`
- 依赖工具：`pytest`

## 2. 输入
- 必需：测试文件列表（来自 `/select-tests` 或人工判断）。
- 可选：特定测试类或函数、额外的 pytest 参数。

## 3. 执行步骤
1. 对列表中的每个测试文件运行 `pytest <path> -v`。
2. 若需要特定测试函数，追加 `::TestClass::test_case`。
3. 记录命令、关键输出和通过/失败结果。
4. 如测试失败：
   - 标记失败原因；
   - 评估是否为已知问题或本次改动引入；
   - 根据需要触发 `/auto-diagnose` 或重新运行。

## 4. 输出
- 测试执行命令与结果摘要。
- 失败用例列表及原因。
- 后续行动计划（如需重试或修复）。

