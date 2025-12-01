## 测试目标
- 覆盖当前功能的正确性：解析、公式编码、QUBO 构建、采样、验证与证明路径输出。
- 加入“不可证”负例用例，评估系统能否判定失败；对现阶段无法识别的负例用例以 xfail（预期失败）标注，明确当前局限。
- 仅编写测试，不改动实现代码。

## 测试范围
1. 解析器（parser）
   - 优先级与括号：`P&Q|R`、`P->Q->R`、`~(P&Q)`。
   - 非法输入：缺右括号/未知符号。
2. 公式编码（formula_encoder）
   - NOT/AND/OR/IMPLY 的约束一致性（构造小 BQM，检查最小能量解满足语义）。
3. 构建器（qubo_builder）
   - 成功用例：MP、MT、合取消除、合取引入、析取引入、双重否定消除。
   - 变量统计与摘要不报错（`summary()`）。
4. 解码器与验证（decoder）
   - `verify_assignment` 能检测公理/目标未满足与（当前）基本结构违规。
   - 证明路径格式正确（包含公理、变量、推理步骤、结论四部分）。
5. CLI 冒烟测试（不跑退火，仅参数解析与构建执行，不依赖外部后端）。

## 正例用例（应得证）
- MP：`axioms=["P","P->Q"], goal="Q"`
- MT：`axioms=["P->Q","~Q"], goal="~P"`
- And-Elim：`axioms=["P&Q"], goal="P"` 与 `goal="Q"`
- And-Intro：`axioms=["P","Q"], goal="P&Q"`
- Or-Intro：`axioms=["P"], goal="P|Q"` 与 `axioms=["Q"], goal="P|Q"`
- DNE：`axioms=["~~P"], goal="P"`

## 负例用例（不可证）
- 目标相反：`axioms=["P","P->Q"], goal="~Q"`。
- 无关目标：`axioms=["P&Q"], goal="R"`。
- 矛盾公理：`axioms=["P","~P"], goal="Q"`（应失败，且显示公理未满足或结构冲突）。
- 逻辑不可导但可满足（揭示系统局限）：`axioms=["P"], goal="R"`、`axioms=[""], goal="P|~P"`（当前实现可能“成功”，标注为 xfail 并在断言信息中解释原因）。

## 技术要点
- 使用 `dwave-neal`（已在 requirements.txt）作为采样后端，设置 `reads` 较小（如 50）保证测试速度。
- 封装测试辅助：构建→采样→最佳解→验证→返回 success/message/proof；便于重复调用各案例。
- 对负例：断言 `success == False`，并匹配 `message` 提示（公理未满足/目标未满足/结构约束违反）。
- 对“局限用例”：使用 `pytest.mark.xfail(reason=...)` 标注，保留日志说明当前体系是“同时满足”而非“可导性”判断。

## 拟新增文件
- `tests/test_parser.py`：解析正反例与错误输入。
- `tests/test_formula_encoder.py`：约束语义一致性。
- `tests/test_qubo_builder_success.py`：六类成功用例端到端验证。
- `tests/test_qubo_builder_failure.py`：四类不可证用例端到端验证（含 xfail）。
- `tests/test_decoder.py`：验证与证明路径的结构与关键文案。
- `tests/test_cli_smoke.py`：CLI 参数解析与构建的冒烟测试。

## 运行与验收
- 运行：`pytest -q` 或 `python test_basic.py && python -m tests.test_neural.py`。
- 验收标准：
  - 正例全部通过；负例全部失败或按预期 xfail。
  - 日志包含最低能量、验证信息与核心变量赋值；失败案例能给出明确原因。

## 后续（非本轮实施）
- 若你确认测试方案，下一步再针对“可导性判断”与“规则全面应用”做实现修复，让上述 xfail 负例转为真正失败。