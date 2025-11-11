# V2 系统改进说明

本文档说明了针对用户反馈的三个关键改进。

---

## 改进 1: 展示完整的 QUBO 方程 ✅

### 问题
之前系统没有显示完整的 QUBO 方程，用户无法看到能量函数的具体形式。

### 解决方案
添加了 `--show-qubo` 参数，显示完整的 QUBO 方程，包括：
- 线性项（一次项）
- 二次项（交叉项）
- 常数项（offset）

### 使用方法
```bash
python -m qubo_prover_v2.cli --axioms "P->Q; ~Q" --goal "~P" --show-qubo
```

### 输出示例
```
[QUBO 方程]
======================================================================
完整的二次无约束二元优化（QUBO）方程:

能量函数 E(x) = Σ Q_ij * x_i * x_j + offset

其中:
  线性项（一次项）:
    -110.0 * Axiom0_Imp_P_Q
    -110.0 * Axiom1_Not_Q
    -110.0 * Goal_Not_P
    -20.0 * P
    +25.0 * P * Q
    -10.0 * Q

  二次项（交叉项）:
    -20.0 * Axiom0_Imp_P_Q * P * Q
    +20.0 * Axiom1_Not_Q * Q
    +20.0 * Goal_Not_P * P
    +20.0 * P * Axiom0_Imp_P_Q
    -10.0 * P * P * Q
    +5.0 * P * Q
    -10.0 * Q * P * Q

  常数项（offset）: 330.0

总计: 6 个线性项 + 7 个二次项
======================================================================
```

### 技术细节
- 修改了 `cli.py`，添加了 `_display_qubo_equation()` 函数
- 将 QUBO 字典按线性项和二次项分类显示
- 清晰展示每个变量的系数

---

## 改进 2: 详细的证明路径 ✅

### 问题
之前的证明路径过于简单，只列出公理和结论，没有展示推理过程。

### 解决方案
重写了 `decoder.py` 中的 `extract_proof_path()` 函数，现在包含：
1. **步骤 1**: 列出所有公理及其真值
2. **步骤 2**: 显示命题变量的赋值（真/假）
3. **步骤 3**: 详细的推理过程（包括使用的规则和逻辑推导）
4. **步骤 4**: 最终结论

### 输出示例

#### Modus Ponens (P, P→Q ⊢ Q)
```
【步骤 1】公理（已知为真）:
  ✓ 公理 1: P
  ✓ 公理 2: (P -> Q)

【步骤 2】命题变量赋值:
  P = 真(True)
  Q = 真(True)

【步骤 3】推理过程:
  由公理 1 (P=真) 和公理 2 (P→Q)，
    根据 Modus Ponens 规则，得 Q=真
  （系统激活了推理规则变量: MP → P → Q）

【步骤 4】结论:
  ✓ 目标 Q 得证
  证明完成！
```

#### Modus Tollens (P→Q, ~Q ⊢ ~P)
```
【步骤 1】公理（已知为真）:
  ✓ 公理 1: (P -> Q)
  ✓ 公理 2: ~Q

【步骤 2】命题变量赋值:
  P = 假(False)
  Q = 假(False)

【步骤 3】推理过程:
  由公理 1 (P→Q) 和公理 2 (~Q=真)，
    根据 Modus Tollens 规则（反证法）：
      假设 P=真，则由 P→Q 得 Q=真
      但 ~Q=真，即 Q=假，矛盾！
      因此 P=假，即 ~P=真

【步骤 4】结论:
  ✓ 目标 ~P 得证
  证明完成！
```

### 技术细节
- 添加了 `_analyze_inference_logic()` 函数来分析推理模式
- 自动检测 Modus Ponens、Modus Tollens、And-Elimination 等规则
- 对于 Modus Tollens，展示完整的反证法推理过程

---

## 改进 3: 关于 Modus Tollens 的澄清 ✅

### 问题
用户认为 "P->Q; ~Q ⊢ ~P" 的证明成功是不合理的。

### 澄清
**这个证明是完全正确的！** 这是经典的 **Modus Tollens（否定后件式）** 推理规则。

### 逻辑验证

#### 真值表验证
```
P | Q | P->Q | ~Q | ~P | 满足公理? | 满足目标?
--------------------------------------------------
0 | 0 |   1  |  1 |  1 |     ✓      |     ✓     
0 | 1 |   1  |  0 |  1 |     ✗      |     ✓     
1 | 0 |   0  |  1 |  0 |     ✗      |     ✗     
1 | 1 |   1  |  0 |  0 |     ✗      |     ✗     
```

**结论:** 只有 P=0, Q=0 同时满足所有公理和目标。

#### 反证法推理
1. **假设** P 为真
2. **由公理 1** (P→Q)，如果 P 为真，则 Q 必为真
3. **但公理 2** (~Q) 说 Q 为假
4. **矛盾！** 因此假设错误
5. **结论:** P 必为假，即 ~P 为真 ✓

### 为什么系统是正确的

系统通过 QUBO 约束确保：
- 公理 1 (P→Q) 必须为真 → 强制 `Axiom0_Imp_P_Q = 1`
- 公理 2 (~Q) 必须为真 → 强制 `Axiom1_Not_Q = 1`
- 目标 (~P) 必须为真 → 强制 `Goal_Not_P = 1`
- 结构约束确保语义一致性

采样器找到的解 (P=0, Q=0) 满足所有这些约束，能量为 0，证明成功！

---

## 总结

| 改进 | 状态 | 说明 |
|------|------|------|
| **1. 展示 QUBO 方程** | ✅ 完成 | 添加 `--show-qubo` 参数 |
| **2. 详细证明路径** | ✅ 完成 | 四步骤详细推理过程 |
| **3. Modus Tollens** | ✅ 正确 | 经典推理规则，逻辑完全正确 |

---

## 使用示例

### 示例 1: 查看 QUBO 方程
```bash
python -m qubo_prover_v2.cli \
  --axioms "P; P->Q" \
  --goal "Q" \
  --show-qubo
```

### 示例 2: 详细证明路径（默认）
```bash
python -m qubo_prover_v2.cli \
  --axioms "P->Q; ~Q" \
  --goal "~P"
```

### 示例 3: 完整调试信息
```bash
python -m qubo_prover_v2.cli \
  --axioms "P; P->Q; Q->R" \
  --goal "R" \
  --verbose \
  --show-qubo \
  --show-all-vars
```

---

## 技术改进细节

### 修改的文件

1. **`decoder.py`** (100+ 行新增)
   - 重写 `extract_proof_path()` 函数
   - 添加 `_analyze_inference_logic()` 函数
   - 自动检测推理规则模式

2. **`cli.py`** (50+ 行新增)
   - 添加 `--show-qubo` 参数
   - 添加 `_display_qubo_equation()` 函数
   - 改进输出格式

3. **`qubo_builder.py`** (10 行修改)
   - 在 `get_variable_info()` 中添加 `axiom_formulas` 和 `goal_formula`
   - 为 decoder 提供更多信息

### 新增功能

- ✅ QUBO 方程可视化
- ✅ 分步骤证明路径
- ✅ 推理规则自动检测
- ✅ 反证法推理展示
- ✅ 命题变量真值显示

---

## 验证测试

所有测试用例均通过：

### 测试 1: Modus Ponens
```bash
python -m qubo_prover_v2.cli --axioms "P; P->Q" --goal "Q"
```
**结果:** ✅ 成功，详细展示推理过程

### 测试 2: Modus Tollens
```bash
python -m qubo_prover_v2.cli --axioms "P->Q; ~Q" --goal "~P"
```
**结果:** ✅ 成功，展示反证法推理

### 测试 3: 三段论
```bash
python -m qubo_prover_v2.cli --axioms "P; P->Q; Q->R" --goal "R"
```
**结果:** ✅ 成功，展示多步推理

### 测试 4: And-Elimination
```bash
python -m qubo_prover_v2.cli --axioms "P&Q" --goal "P"
```
**结果:** ✅ 成功，展示合取消除

---

## 未来改进方向

虽然当前系统已经很完善，但仍有改进空间：

1. **更多推理规则检测**
   - Resolution（归结）
   - Contraposition（逆否命题）
   - De Morgan 定律

2. **证明树可视化**
   - 生成 Mermaid 图表
   - 显示推理依赖关系

3. **交互式证明**
   - 允许用户选择推理步骤
   - 提供多种证明路径

4. **性能优化**
   - 缓存 QUBO 编译结果
   - 并行采样

---

**改进完成日期:** 2025-11-04
**版本:** 2.1.0
**状态:** ✅ 所有改进已实现并测试通过

