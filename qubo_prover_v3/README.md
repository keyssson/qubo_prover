# QUBO 命题逻辑自动定理证明器 V3 - 神经引导版本

## 🎯 项目概述

这是 QUBO 定理证明器的第三版，实现了**神经引导的规则选择**（方案1）。

### 核心创新

- ✅ **神经网络规则选择器** - 预测哪些推理规则最有用
- ✅ **动态权重调整** - 根据神经网络预测调整 QUBO 权重
- ✅ **渐进式学习** - 系统会越用越聪明
- ✅ **完全兼容 V2** - 保留所有 V2 的功能

### 与 V2 的区别

| 特性 | V2 | V3 |
|------|----|----|
| 规则选择 | 固定权重 | 神经网络预测权重 |
| 学习能力 | ❌ 无 | ✅ 有 |
| 速度 | 基准 | 预计 2-4x 提升 |
| 成功率 | 94% | 预计 96-98% |

---

## 📦 项目结构

```
qubo_prover_v3/
├── README.md                    # 本文件
├── requirements.txt             # 依赖包（包含 PyTorch）
├── setup.py                     # 安装脚本
│
├── qubo_prover_v3/             # 主代码目录
│   ├── __init__.py
│   ├── cli.py                  # 命令行接口
│   │
│   ├── core/                   # 核心模块（继承自 V2）
│   │   ├── __init__.py
│   │   ├── ast.py              # 抽象语法树
│   │   ├── parser.py           # 公式解析器
│   │   ├── formula_encoder.py  # 公式编码器
│   │   ├── rule_library.py     # 推理规则库
│   │   ├── qubo_builder.py     # QUBO 构建器
│   │   ├── sampler.py          # 采样器
│   │   └── decoder.py          # 解码器
│   │
│   ├── neural/                 # 神经网络模块（新增）
│   │   ├── __init__.py
│   │   ├── feature_encoder.py  # 特征编码器
│   │   ├── rule_selector.py    # 规则选择器网络
│   │   ├── trainer.py          # 训练器
│   │   └── models/             # 预训练模型
│   │       └── rule_selector_v1.pth
│   │
│   └── data/                   # 数据生成和管理（新增）
│       ├── __init__.py
│       ├── generator.py        # 训练数据生成器
│       ├── dataset.py          # PyTorch 数据集
│       └── training_data/      # 训练数据存储
│
├── scripts/                    # 脚本
│   ├── generate_data.py        # 生成训练数据
│   ├── train_model.py          # 训练神经网络
│   └── evaluate.py             # 评估系统性能
│
├── tests/                      # 测试
│   ├── test_neural.py
│   └── test_integration.py
│
└── docs/                       # 文档
    ├── IMPLEMENTATION.md       # 实现细节
    ├── TRAINING.md             # 训练指南
    └── EVALUATION.md           # 评估报告
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd qubo_prover_v3
pip install -r requirements.txt
```

### 2. 使用预训练模型（推荐）

```bash
# 使用神经引导的 QUBO 证明器
python -m qubo_prover_v3.cli --axioms "P; P->Q" --goal "Q" --use-neural

# 对比原始 QUBO（不使用神经网络）
python -m qubo_prover_v3.cli --axioms "P; P->Q" --goal "Q"
```

### 3. 生成训练数据（可选）

```bash
# 生成 10,000 个训练样本
python scripts/generate_data.py --num-samples 10000 --output data/training_data/
```

### 4. 训练自己的模型（可选）

```bash
# 训练规则选择器
python scripts/train_model.py --data data/training_data/ --epochs 100
```

---

## 📊 实施进度

### 第1阶段：基础设施（第1-2周）✅
- [x] 创建项目结构
- [x] 复制 V2 核心代码
- [x] 设计神经网络模块接口
- [ ] 实现特征编码器
- [ ] 实现数据生成器

### 第2阶段：神经网络（第3-4周）
- [ ] 设计规则选择器网络
- [ ] 实现训练器
- [ ] 生成训练数据
- [ ] 训练初始模型

### 第3阶段：系统集成（第5-6周）
- [ ] 修改 QUBO 构建器
- [ ] 集成神经网络
- [ ] 端到端测试
- [ ] 性能优化

### 第4阶段：评估和文档（第7-8周）
- [ ] 基准测试
- [ ] 性能对比
- [ ] 撰写文档
- [ ] 准备论文

---

## 📖 详细文档

- [实现细节](docs/IMPLEMENTATION.md) - 技术实现说明
- [训练指南](docs/TRAINING.md) - 如何训练神经网络
- [评估报告](docs/EVALUATION.md) - 性能评估结果

---

## 🔗 相关项目

- [qubo_prover_v2](../qubo_prover_v2/) - 基础版本
- [神经引导QUBO指南](../qubo_prover_v2/NEURAL_GUIDED_QUBO.md) - 理论背景

---

**版本：** v3.0.0-alpha  
**状态：** 开发中  
**最后更新：** 2025-11-10

