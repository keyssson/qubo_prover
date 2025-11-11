# 更新日志

## [2.1.1] - 2025-11-04

### 🐛 Bug 修复（Critical）

#### 问题：系统接受了逻辑上矛盾的证明
- **发现者：** youxingug@gmail.com
- **问题：** 验证函数只检查公理变量和目标变量是否为 1，没有验证结构约束的语义一致性
- **影响：** 错误的证明（如 P, P→Q ⊢ ~Q）被判定为成功

#### 修复内容
1. **增强验证函数** (`decoder.py`)
   - 添加 `var_info` 参数到 `verify_assignment()`
   - 新增 `_verify_structural_constraints()` 函数

2. **结构约束验证**
   - **蕴涵检查：** 如果 P=1 且 P→Q=1，验证 Q=1
   - **否定检查：** 验证 ~P 和 P 互斥（~P + P = 1）

3. **更新 CLI** (`cli.py`)
   - 传递 `var_info` 给验证函数

#### 测试结果
```bash
# 错误案例 1（现在正确拒绝）
python -m qubo_prover_v2.cli --axioms "P; P->Q" --goal "~Q"
# 输出: ✗ 证明失败 - 结构约束违反

# 正确案例（仍然工作）
python -m qubo_prover_v2.cli --axioms "P; P->Q" --goal "Q"
# 输出: ✓ 证明成功
```

### 📚 新增文档
- `HAMILTONIAN_EXPLAINED.md` - 哈密顿量构造的通俗解释（三岁小孩也能懂）
- `BUGFIX_v2.1.1.md` - 详细的 Bug 修复报告

### ⚠️ 已知限制
- 系统仍然是**可满足性求解器**（SAT），不是完整的**推导验证器**
- 某些非推导性证明（如 P→Q, Q ⊢ ~P）可能仍然通过
- 未来版本将实现更强的推导验证

---

## [2.1.0] - 2025-11-04

### 新增功能

#### 1. 完整 QUBO 方程展示
- 添加 `--show-qubo` 命令行参数
- 显示完整的能量函数，包括：
  - 线性项（一次项）
  - 二次项（交叉项）
  - 常数项（offset）
- 清晰的分类展示，便于理解 QUBO 结构

**使用方法:**
```bash
python -m qubo_prover_v2.cli --axioms "P; P->Q" --goal "Q" --show-qubo
```

#### 2. 详细证明路径
- 重写 `extract_proof_path()` 函数
- 四步骤证明过程：
  1. 列出所有公理及其真值
  2. 显示命题变量赋值（真/假）
  3. 详细推理过程（包括使用的规则）
  4. 最终结论
- 自动检测推理规则：
  - Modus Ponens
  - Modus Tollens（包括反证法展示）
  - And-Elimination
- 对于 Modus Tollens，展示完整的反证法推理

**示例输出:**
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

#### 3. Modus Tollens 正确性验证
- 澄清 Modus Tollens (P→Q, ~Q ⊢ ~P) 是完全正确的推理规则
- 添加真值表验证脚本 `verify_modus_tollens.py`
- 在证明路径中展示完整的反证法推理过程
- 创建详细的说明文档 `IMPROVEMENTS.md`

### 改进

#### 代码改进
- `decoder.py`: 添加 `_analyze_inference_logic()` 函数（100+ 行）
- `cli.py`: 添加 `_display_qubo_equation()` 函数（50+ 行）
- `qubo_builder.py`: 扩展 `get_variable_info()` 返回更多信息

#### 文档改进
- 创建 `IMPROVEMENTS.md` - 详细说明三个改进
- 创建 `CHANGELOG.md` - 版本更新日志（本文件）
- 更新 `README.md` - 添加最新改进说明
- 创建 `examples/demo_improvements.sh` - 演示新功能

### 修复
- 修复 `format_expr` 导入错误，改用 AST 类的 `__str__` 方法
- 改进输出格式，使用分隔线增强可读性

### 测试
所有测试用例通过：
- ✅ Modus Ponens (P, P→Q ⊢ Q)
- ✅ Modus Tollens (P→Q, ~Q ⊢ ~P)
- ✅ 三段论 (P, P→Q, Q→R ⊢ R)
- ✅ And-Elimination (P∧Q ⊢ P)
- ✅ 复杂公式 ((P∨Q)∧R, ~P ⊢ Q∧R)

---

## [2.0.0] - 2025-10-27

### 初始版本

#### 核心功能
- 动态 QUBO 生成
- 公理和目标约束编码
- 结构约束确保语义一致性
- 支持 Neal 和 OpenJij 采样器
- 命令行接口

#### 支持的运算符
- `~` - 否定 (NOT)
- `&` - 合取 (AND)
- `|` - 析取 (OR)
- `->` - 蕴涵 (IMPLY)

#### 推理规则
- Modus Ponens
- And-Elimination (左/右)
- Or-Introduction (左/右)
- And-Introduction
- Modus Tollens
- Double Negation

#### 文档
- `README.md` - 完整项目文档
- `QUICKSTART.md` - 快速入门指南
- `COMPARISON.md` - V1 vs V2 对比
- `PROJECT_SUMMARY.md` - 项目总结

#### 示例
- `examples/modus_ponens.sh`
- `examples/syllogism.sh`
- `examples/modus_tollens.sh`
- `examples/demo_all.sh`

---

## 版本说明

### 版本号规则
- **主版本号 (Major)**: 重大架构变更
- **次版本号 (Minor)**: 新功能添加
- **修订号 (Patch)**: Bug 修复和小改进

### 当前版本: 2.1.0
- **2**: V2 架构（动态 QUBO 生成）
- **1**: 添加了 QUBO 展示和详细证明路径
- **0**: 初始稳定版本

---

## 未来计划

### v2.2.0 (计划中)
- [ ] 添加更多推理规则检测
  - Resolution（归结）
  - Contraposition（逆否命题）
  - De Morgan 定律
- [ ] 证明树可视化（Mermaid 图表）
- [ ] 性能优化（QUBO 编译缓存）

### v2.3.0 (计划中)
- [ ] 交互式证明模式
- [ ] 多种证明路径展示
- [ ] 证明复杂度分析

### v3.0.0 (长期)
- [ ] 支持一阶逻辑（量词）
- [ ] 集成真实量子退火硬件
- [ ] 图形化界面

---

## 贡献者

- 主要开发: Augment Agent
- 用户反馈: youxingug@gmail.com

---

## 许可证

MIT License

---

**最后更新:** 2025-11-04

