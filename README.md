# QUBO 命题逻辑自动定理证明

本仓库包含两个版本的 QUBO 命题逻辑自动定理证明器：

## 🆕 **V2 版本（推荐）** - 真正的定理证明器

**位置：** `qubo_prover_v2/`

**核心特性：**
- ✅ **动态 QUBO 生成**：根据输入的公理和目标动态构建哈密顿量
- ✅ **公理约束编码**：将输入公理编码为 QUBO 约束，强制其为真
- ✅ **目标约束编码**：将证明目标编码为 QUBO 约束
- ✅ **语义一致性**：确保逻辑变量之间的语义关系
- ✅ **高成功率**：~94% 的证明成功率

**快速开始：**
```bash
cd qubo_prover_v2
pip install -r requirements.txt
python -m qubo_prover_v2.cli --axioms "P; P->Q" --goal "Q"
```

**文档：**
- [完整文档](qubo_prover_v2/README.md) - 详细的使用指南和原理说明
- [快速入门](qubo_prover_v2/QUICKSTART.md) - 5 分钟上手指南
- [V1 vs V2 对比](qubo_prover_v2/COMPARISON.md) - 详细的技术对比
- [项目总结](qubo_prover_v2/PROJECT_SUMMARY.md) - 完整的项目总结

---

## 📦 **V1 版本（原型）** - 规则库

**位置：** `qubo_prover/`

本项目是一个基于 QUBO/Ising 表达与模拟退火采样的命题逻辑自动定理证明最小可行产品（MVP）。
当前以“蕴涵消除（Modus Ponens, MP）”为核心范式，演示从“公理与目标”到“QUBO 编码—采样—解码—验证—输出”的端到端流程。

本实现使用 PyQUBO 进行 QUBO 编码，配合 dimod 的模拟退火采样器。

**注意：** V1 版本存在以下限制：
- ❌ QUBO 固定不变（51 个变量）
- ❌ 公理未被编码为约束
- ❌ 目标未被编码为约束
- ❌ 成功率较低（~40%）

**推荐使用 V2 版本！**

## 功能概览
- 轻量级命题公式解析器：支持变量（如 A、P、Q、R 等）、一元/二元运算符：`~`（非）、`&`（与）、`|`（或）、`->`（蕴涵）以及括号
- QUBO 编码器（MP 原型，基于 PyQUBO）：针对 `{P, P->Q} ⊢ Q` 的推理模式进行编码
- 采样后端：默认使用 `neal` 的经典模拟退火；可选 `openjij`（如需请自行安装）
- 解码与验证：从采样结果恢复变量赋值并验证 MP 推理路径的合法性
- 命令行 CLI：便捷运行端到端流程

## 安装（conda）
```bash
# 进入项目目录
cd /mnt/lustre/GPU4/home/wangkesong/qubo_prover_mvp

# 创建并激活 conda 环境（Python 3.9 仅为示例，可按需调整）
conda create -n qubo-prover python=3.9 -y
conda activate qubo-prover

# 安装依赖
pip install -r requirements.txt
# 可选：如需 OpenJij（经典模拟退火/量子退火模拟），请另外安装
# pip install openjij==0.6.7
```

## 用法示例
目标：从公理 `{P, P->Q}` 证明 `Q`
```bash
python -m qubo_prover.cli \
  --axioms "P; P->Q" \
  --goal "Q" \
  --backend neal \
  --reads 50
```
你将看到最低能量样本与 `provable: True`，并输出简要的证明路径 `P, (P->Q) ⇒ Q`。

也可使用示例脚本：
```bash
bash examples/simple_mp.sh
```

## 设计要点（与可扩展性）
- 输入解析与 AST：将文本公式解析为内部表达（表达式树），便于后续匹配与验证
- QUBO 编码（MP，PyQUBO 版）：
  - 二元变量：`P, Imp(表示P->Q), Q, R(是否应用规则)`
  - 能量函数（惩罚系数 M）：
    - H = M · [ R·(1-P) + R·(1-Imp) + R·(1-Q) + Q·(1-R) ]
    - 展开得到：H = M · ( 3R + Q − R·P − R·Imp − 2·R·Q )
  - 采样将倾向于满足推理约束的低能量解，从而给出合法路径
- 采样器：默认 `neal`（Ocean/Dimod 的模拟退火），也保留 `openjij` 作为可选后端接口
- 解码与验证：把采样的 0/1 赋值映射回“是否应用规则/哪些命题为真”，并检查推理合法性与目标是否成立
- 扩展方向：
  - 更多推理规则（合取/析取规则、反证法等）
  - 更复杂逻辑（引入辅助变量/Tseitin 变换以编码更大公式）
  - 多种采样后端（D-Wave 硬件、SQASampler、遗传/强化学习等）

### 已支持规则（持续扩展中）
- Modus Ponens（`R`）：从 `P,(P->Q)` 推出 `Q`
- And-Elim 左/右（`RL`/`RR`）：从 `And(A,B)` 推出 `A` / `B`
- Or-Intro（`RI`）：从 `X` 推出 `X or Y`
- And-Intro（`RAI`）：从 `A,B` 推出 `And(A,B)`（复用 `A,B,And` 变量）
- Modus Tollens（`RMT`）：从 `(P->Q), ~Q` 推出 `~P`
- Double Negation Elimination（`RDN`）：从 `~~X` 推出 `X`
 - De Morgan（`RDM`）：从 `~(A&B)` 推出 `(~A or ~B)`
 - Double Negation Introduction（`RDI`）：从 `X` 推出 `~~X`
 - De Morgan 2（`RDM2`）：从 `~(A|B)` 推出 `(~A & ~B)`
 - Resolution（`RRES`）：从 `Or(A,X), Or(~A,Y)` 推出 `Or(X,Y)`
 - Implication Transitivity（`RTR`）：从 `(A->B),(B->C)` 推出 `(A->C)`
 - Or Commutation（`RORC`）：从 `Or(A,B)` 推出 `Or(B,A)`
  - Contraposition（`RCP`）：从 `(P->Q)` 推出 `(~Q -> ~P)`
  - And Commutation（`RANDC`）：从 `And(A,B)` 推出 `And(B,A)`
  - Or Associativity（`RORAS`）：从 `Or(A,Or(B,C))` 推出 `Or(Or(A,B),C)`
  - Or Idempotence（`RORI`）：从 `Or(A,A)` 推出 `A`
  - And Idempotence（`RANDI`）：从 `And(A,A)` 推出 `A`
 - Or-Elimination（`ROE`）：从 `Or(A,B), A->C, B->C` 推出 `C`

## 代码流程（Code Flow）
1. 命令行入口（`qubo_prover/cli.py`）
   - 解析参数：`--axioms`, `--goal`, `--backend`, `--reads`, `--penalty`
   - 示例：`python -m qubo_prover.cli --axioms "P; P->Q" --goal "Q"`
2. 输入解析（`parser.parse`）
   - 将字符串公式解析为 AST（如 `Var`, `Imply` 等），做基本格式校验
3. QUBO 编码（`encoder.ModusPonensEncoder`）
   - 使用 PyQUBO 构建哈密顿量 H：`H = M * [ R*(1-P) + R*(1-Imp) + R*(1-Q) + Q*(1-R) ]`
   - `compile_qubo` 生成 `model`, `qubo`, `bqm`, `offset`，供不同后端使用
4. 采样（`sampler.make_backend`）
   - 选择后端并进行采样：
     - `neal`：`SimulatedAnnealingSampler().sample(bqm, num_reads)`
     - `openjij`（可选）：`SASampler().sample_qubo(Q, num_reads)`
5. 解码与验证（`decoder.py`）
   - 将样本集转为字典列表：`decode_dimod_sampleset` / `decode_openjij_response`
   - 选取最低能量赋值：`best_by_lowest_energy`
   - 校验规则合法性：`verify_modus_ponens_assignment`、`verify_and_elim_left/right`、`verify_or_intro`、`verify_and_intro`、`verify_modus_tollens`、`verify_double_neg_elim`
6. 输出
   - 打印最低能量赋值、能量值与 `provable` 结果
   - 若成功，输出证明路径：`P, (P->Q) => Q with rule R=1`

## 目录结构
```
qubo_prover_mvp/
├─ README.md               # 本说明文档
├─ requirements.txt        # 依赖（包含 PyQUBO）
├─ examples/
│  └─ simple_mp.sh         # 运行示例脚本
└─ qubo_prover/
   ├─ __init__.py
   ├─ ast.py               # 表达式数据结构
   ├─ parser.py            # 轻量级命题解析器
   ├─ encoder.py           # MP 的 QUBO 编码（PyQUBO）
   ├─ sampler.py           # 采样后端（neal/openjij）
   └─ cli.py               # 命令行入口
```

## 常见问题
- Q：只能证明 MP 吗？
  - A：当前是 MP 的最小原型，结构已模块化，后续可以扩展更多规则与复杂逻辑。
- Q：为什么采样有时结果不同？
  - A：模拟退火为启发式方法，`num_reads`、退火温度等会影响结果；可多次运行取最低能量解。
- Q：如何加入新后端？
  - A：在 `sampler.py` 中实现符合统一接口的后端即可。
