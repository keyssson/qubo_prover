# QUBO Prover V3.1 - 神经引导的命题逻辑自动定理证明器

## 项目概述

QUBO Prover V3.1 是一个基于量子退火优化（QUBO）的命题逻辑自动定理证明器，结合神经网络进行规则选择引导。本版本是对 V3 的重大重构，实现了更完备的证明系统。

### 核心特性

- ✅ **完整的推理规则库** - 支持 12+ 种自然演绎规则
- ✅ **改进的 QUBO 编码** - 更精确的逻辑语义编码
- ✅ **神经网络规则选择** - 预测最有效的推理规则
- ✅ **多种证明模式** - QUBO、符号、混合三种模式
- ✅ **完备性保证** - 归结消解确保理论完备性

### 与 V3 的主要区别

| 特性 | V3 | V3.1 |
|------|----|----|
| 推理规则 | 8 种 | 12+ 种（含归结消解） |
| 特征维度 | 12 维 | 32 维 |
| CNF 转换 | ❌ 无 | ✅ 完整实现 |
| 证明搜索 | 简单 | 前向/后向/双向 |
| 相继式支持 | ❌ 无 | ✅ 有 |
| 证明模式 | 仅 QUBO | QUBO/符号/混合 |

---

## 项目结构

```
qubo_prover_v3.1/
├── qubo_prover/
│   ├── __init__.py
│   ├── cli.py                 # 命令行接口
│   ├── __main__.py            # 模块入口
│   │
│   ├── logic/                 # 逻辑表示层
│   │   ├── ast.py            # 抽象语法树
│   │   ├── parser.py         # 公式解析器
│   │   ├── cnf.py            # CNF 转换
│   │   └── evaluator.py      # 语义求值
│   │
│   ├── proof/                 # 证明系统层
│   │   ├── rules.py          # 推理规则库
│   │   ├── proof_state.py    # 证明状态
│   │   ├── sequent.py        # 相继式
│   │   └── search.py         # 证明搜索
│   │
│   ├── qubo/                  # QUBO 编码层
│   │   ├── encoder.py        # 公式编码器
│   │   ├── proof_encoder.py  # 证明步骤编码
│   │   ├── builder.py        # QUBO 构建器
│   │   └── constraints.py    # 约束生成
│   │
│   ├── solver/                # 求解器层
│   │   ├── backends.py       # 采样后端
│   │   ├── decoder.py        # 结果解码
│   │   └── verifier.py       # 证明验证
│   │
│   └── neural/                # 神经网络层
│       ├── features.py       # 特征编码
│       ├── model.py          # 网络模型
│       └── predictor.py      # 预测接口
│
├── tests/                     # 测试套件
│   ├── test_parser.py
│   ├── test_proof.py
│   ├── test_qubo.py
│   └── test_integration.py
│
├── requirements.txt
└── README.md
```

---

## 快速开始

### 1. 安装依赖

```bash
cd qubo_prover_v3.1
pip install -r requirements.txt
```

### 2. 基本用法

```bash
# Modus Ponens: P, P→Q ⊢ Q
python -m qubo_prover.cli --axioms "P; P->Q" --goal "Q"

# 使用神经网络引导
python -m qubo_prover.cli --axioms "P; P->Q" --goal "Q" --use-neural

# 符号证明模式
python -m qubo_prover.cli --axioms "P; P->Q" --goal "Q" --mode symbolic

# 混合模式（先尝试符号，失败则 QUBO）
python -m qubo_prover.cli --axioms "P; P->Q" --goal "Q" --mode hybrid
```

### 3. 更多示例

```bash
# Modus Tollens: P→Q, ~Q ⊢ ~P
python -m qubo_prover.cli --axioms "P->Q; ~Q" --goal "~P"

# 三段论: P, P→Q, Q→R ⊢ R
python -m qubo_prover.cli --axioms "P; P->Q; Q->R" --goal "R"

# 合取消除: P∧Q ⊢ P
python -m qubo_prover.cli --axioms "P & Q" --goal "P"

# 双重否定: ~~P ⊢ P
python -m qubo_prover.cli --axioms "~~P" --goal "P"

# 详细输出
python -m qubo_prover.cli --axioms "P; P->Q" --goal "Q" -v
```

---

## 支持的推理规则

| 规则 | 符号形式 | 说明 |
|------|----------|------|
| Modus Ponens | P, P→Q ⊢ Q | 肯定前件 |
| Modus Tollens | P→Q, ~Q ⊢ ~P | 否定后件 |
| And-Intro | P, Q ⊢ P∧Q | 合取引入 |
| And-Elim | P∧Q ⊢ P (或 Q) | 合取消除 |
| Or-Intro | P ⊢ P∨Q | 析取引入 |
| Or-Elim | P∨Q, ~P ⊢ Q | 析取消除 |
| Not-Intro | [P]...⊥ ⊢ ~P | 归谬法 |
| Double-Neg | ~~P ⊢ P | 双重否定消除 |
| Impl-Intro | [P]...Q ⊢ P→Q | 条件证明 |
| Resolution | A∨P, B∨~P ⊢ A∨B | 归结消解 |

---

## 公式语法

```
<iff>     ::= <imply> ('<->' <imply>)*
<imply>   ::= <or> ('->' <or>)*
<or>      ::= <and> ('|' <and>)*
<and>     ::= <unary> ('&' <unary>)*
<unary>   ::= '~' <unary> | <primary>
<primary> ::= '(' <iff> ')' | <var>
<var>     ::= [A-Za-z_][A-Za-z0-9_]*
```

**运算符优先级**（从高到低）：
1. `~` 否定
2. `&` 合取
3. `|` 析取
4. `->` 蕴涵
5. `<->` 等价

---

## 命令行参数

```
必需参数:
  --axioms TEXT      公理列表，用分号分隔
  --goal TEXT        证明目标

模式选择:
  --mode {qubo,symbolic,hybrid}
                     证明模式 (默认: qubo)

神经网络:
  --use-neural       启用神经网络引导
  --model-path PATH  模型路径
  --show-weights     显示预测的规则权重

QUBO 参数:
  --backend {neal,openjij,exact}
                     求解器后端 (默认: neal)
  --reads N          采样次数 (默认: 100)
  --axiom-penalty F  公理惩罚系数 (默认: 100.0)
  --structure-penalty F
                     结构惩罚系数 (默认: 20.0)

输出选项:
  -v, --verbose      详细输出
  -q, --quiet        静默模式
  --show-qubo        显示 QUBO 方程

其他:
  --list-backends    列出可用后端
  --check-entailment 仅检查语义蕴涵
```

---

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_parser.py -v
pytest tests/test_proof.py -v
pytest tests/test_qubo.py -v
pytest tests/test_integration.py -v

# 运行覆盖率测试
pytest tests/ --cov=qubo_prover --cov-report=html
```

---

## 技术细节

### QUBO 编码策略

1. **公式编码**：每个逻辑公式对应一个 QUBO 变量
2. **结构约束**：确保逻辑运算符语义正确
3. **公理约束**：强制公理为真
4. **目标约束**：强制目标为真
5. **规则约束**：编码推理规则的应用

### 神经网络特征

32 维特征向量包括：
- 基础统计（公理数、变量数、公式大小等）
- 运算符统计（蕴涵、否定、合取、析取数量）
- 模式匹配特征（MP/MT/And-Elim 等潜力）
- 变量关系特征（重叠率、覆盖率、频率）

---

## 许可证

MIT License

## 版本历史

- **V3.1.0** - 完全重构，实现完备证明系统
- **V3.0.0** - 引入神经网络引导
- **V2.0.0** - 基础 QUBO 证明器

