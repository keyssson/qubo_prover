# Bug 修复报告 - v2.1.1

## 🐛 发现的问题

### 问题描述
系统接受了逻辑上矛盾的证明，将错误的推理判定为成功。

### 错误案例

#### 案例 1: P, P→Q ⊢ ~Q
```bash
python -m qubo_prover_v2.cli --axioms "P; P->Q" --goal "~Q"
```

**系统输出（v2.1.0）：**
```
✓ 证明成功！
P = 真(True)
Q = 假(False)
```

**问题分析：**
- 公理 1: P = 真 ✓
- 公理 2: P→Q = 真 ✓
- 目标: ~Q = 真（即 Q = 假）✓

**逻辑矛盾：**
- 如果 P=真 且 P→Q=真，那么 Q **必须**=真
- 但系统找到了 Q=假 的解
- 这违反了蕴涵的语义！

**真值表验证：**
```
P | Q | P→Q
1 | 0 |  0   ← P=1, Q=0 时，P→Q 应该=0，不是 1！
```

---

#### 案例 2: P→Q, Q ⊢ ~P
```bash
python -m qubo_prover_v2.cli --axioms "P->Q; Q" --goal "~P"
```

**系统输出（v2.1.0）：**
```
✓ 证明成功！
P = 假(False)
Q = 真(True)
```

**问题分析：**
- 这个赋值在逻辑上是**一致的**（没有矛盾）
- 但这**不是一个有效的证明**！

**为什么不是有效证明？**
- P=1, Q=1 也满足所有公理
- 从 P→Q 和 Q 不能**唯一推导出** ~P
- 这是一个**可满足性问题**，不是**推导问题**

---

## 🔍 问题根源

### 原因 1：验证函数不完整

**原始代码（decoder.py）：**
```python
def verify_assignment(assignment, axiom_vars, goal_var):
    # 只检查公理变量和目标变量是否为 1
    for ax_var in axiom_vars:
        if assignment.get(ax_var, 0) != 1:
            return False
    
    if assignment.get(goal_var, 0) != 1:
        return False
    
    return True  # ← 没有检查结构约束！
```

**问题：**
- 只检查了 `Axiom1_Imp_P_Q = 1`
- 没有检查 P→Q 的**语义**是否正确
- 即：没有验证 `Imp_P_Q = 1 - P + P×Q`

---

### 原因 2：QUBO 约束不够强

虽然 QUBO 中有结构约束：
```python
constraint = (Imp_P_Q - 1 + P - P×Q)²
```

但惩罚系数只有 10，而公理约束的惩罚系数是 100。

**结果：**
- 采样器可能找到一个解，满足公理约束（罚分 0）
- 但违反结构约束（罚分 10）
- 总能量 = 10，不是 0

**问题：**
- 验证函数没有检查能量是否为 0
- 只要公理变量和目标变量为 1 就通过

---

## ✅ 解决方案

### 修复 1：增强验证函数

**新代码（decoder.py）：**
```python
def verify_assignment(assignment, axiom_vars, goal_var, var_info=None):
    # 检查公理和目标
    for ax_var in axiom_vars:
        if assignment.get(ax_var, 0) != 1:
            return False, f"公理 {ax_var} 未满足"
    
    if assignment.get(goal_var, 0) != 1:
        return False, f"目标 {goal_var} 未满足"
    
    # 【新增】验证结构约束
    if var_info:
        is_consistent, error_msg = _verify_structural_constraints(assignment, var_info)
        if not is_consistent:
            return False, f"结构约束违反: {error_msg}"
    
    return True, "所有约束满足"
```

---

### 修复 2：验证结构约束

**新函数（decoder.py）：**
```python
def _verify_structural_constraints(assignment, var_info):
    """验证结构约束是否满足"""
    formula_map = var_info.get("formula_map", {})
    
    # 检查所有 IMPLY 约束
    for var_name, formula_str in formula_map.items():
        if "->" in formula_str and assignment.get(var_name, 0) == 1:
            # 解析 P->Q
            parts = formula_str.strip("()").split("->")
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()
                
                # 如果 P=1 且 P->Q=1，那么 Q 必须=1
                if assignment.get(left, 0) == 1:
                    if assignment.get(right, 0) != 1:
                        return False, f"蕴涵约束违反: {left}=1 且 {var_name}=1，但 {right}=0"
    
    # 检查所有 NOT 约束
    for var_name, formula_str in formula_map.items():
        if "~" in formula_str:
            operand = formula_str.replace("~", "").strip()
            not_val = assignment.get(var_name, 0)
            operand_val = assignment.get(operand, 0)
            
            # ~P 和 P 必须互斥
            if not_val + operand_val != 1:
                return False, f"否定约束违反: {var_name}={not_val} 但 {operand}={operand_val}"
    
    return True, ""
```

---

## 🧪 测试结果

### 测试 1：错误案例 1（应该失败）
```bash
python -m qubo_prover_v2.cli --axioms "P; P->Q" --goal "~Q"
```

**输出（v2.1.1）：**
```
✗ 证明失败
原因: 结构约束违反: 蕴涵约束违反: P=1 且 Axiom1_Imp_P_Q=1，但 Q=0
```

✅ **正确！** 系统拒绝了矛盾的证明。

---

### 测试 2：错误案例 2（仍然通过）
```bash
python -m qubo_prover_v2.cli --axioms "P->Q; Q" --goal "~P"
```

**输出（v2.1.1）：**
```
✓ 证明成功！
P = 假(False)
Q = 真(True)
```

**说明：**
- 这个赋值在逻辑上是**一致的**（没有矛盾）
- 所以通过了结构约束验证
- 但这不是一个**有效的推导**

**这是一个更深层的问题：**
- 当前系统是一个**可满足性求解器**（SAT Solver）
- 不是一个**推导验证器**（Proof Checker）
- 要解决这个问题需要更复杂的推理规则验证

---

### 测试 3：正确案例（应该成功）
```bash
python -m qubo_prover_v2.cli --axioms "P; P->Q" --goal "Q"
```

**输出（v2.1.1）：**
```
✓ 证明成功！
P = 真(True)
Q = 真(True)
```

✅ **正确！** Modus Ponens 仍然工作。

---

### 测试 4：正确案例（应该成功）
```bash
python -m qubo_prover_v2.cli --axioms "P->Q; ~Q" --goal "~P"
```

**输出（v2.1.1）：**
```
✓ 证明成功！
P = 假(False)
Q = 假(False)
```

✅ **正确！** Modus Tollens 仍然工作。

---

## 📊 修复总结

| 问题 | 状态 | 说明 |
|------|------|------|
| **矛盾的证明被接受** | ✅ 已修复 | 增加了结构约束验证 |
| **蕴涵语义检查** | ✅ 已修复 | 验证 P=1 且 P→Q=1 时 Q=1 |
| **否定语义检查** | ✅ 已修复 | 验证 ~P 和 P 互斥 |
| **非推导性证明** | ⚠️ 部分问题 | 需要更复杂的推理验证 |

---

## 🎯 剩余问题

### 问题：可满足性 vs 推导性

**当前系统：**
- 检查是否存在一个赋值满足所有公理和目标
- 这是一个**可满足性问题**（SAT）

**理想系统：**
- 检查目标是否能从公理**推导出来**
- 这是一个**推导问题**（Entailment）

**区别：**
```
公理: P→Q, Q
目标: ~P

可满足性: 存在 P=0, Q=1 满足所有公理和目标 ✓
推导性: 从 P→Q 和 Q 能推导出 ~P 吗？ ✗
```

**解决方案（未来工作）：**
1. 检查是否存在反例（满足公理但不满足目标）
2. 使用更强的推理规则约束
3. 实现完整的推导验证器

---

## 📝 修改的文件

1. **`decoder.py`** (+72 行)
   - 修改 `verify_assignment()` 函数
   - 添加 `_verify_structural_constraints()` 函数

2. **`cli.py`** (+1 行)
   - 传递 `var_info` 给 `verify_assignment()`

---

## 🚀 版本信息

- **修复版本：** v2.1.1
- **修复日期：** 2025-11-04
- **修复类型：** Bug 修复（Critical）
- **影响范围：** 验证逻辑

---

## 📚 相关文档

- [HAMILTONIAN_EXPLAINED.md](HAMILTONIAN_EXPLAINED.md) - 哈密顿量构造的详细解释
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - v2.1.0 的改进说明
- [CHANGELOG.md](CHANGELOG.md) - 完整更新日志

---

**感谢用户 youxingug@gmail.com 发现并报告这个关键 bug！**

