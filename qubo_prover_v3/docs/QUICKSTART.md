# 快速开始指南 - QUBO Prover V3

## 🎯 目标

在 15 分钟内完成以下任务：
1. 安装依赖
2. 生成训练数据
3. 训练神经网络
4. 测试神经引导的 QUBO 证明器

---

## 步骤 1：安装依赖（2分钟）

```bash
cd qubo_prover_v3
pip install -r requirements.txt
```

**预期输出：**
```
Successfully installed torch-2.0.0 pyqubo-1.4.0 ...
```

---

## 步骤 2：测试特征编码器（1分钟）

```bash
python -m qubo_prover_v3.neural.feature_encoder
```

**预期输出：**
```
案例1: Modus Ponens
公理: ['P', 'P->Q']
目标: Q
特征向量: [2. 1. 0. 0. 0. 0. 0. 0. 0. 2. 4. 0.]
```

---

## 步骤 3：测试规则选择器（1分钟）

```bash
python -m qubo_prover_v3.neural.rule_selector
```

**预期输出：**
```
规则选择器神经网络
============================================================
输入维度: 12
隐藏层大小: 64
输出维度（规则数量）: 8
```

---

## 步骤 4：生成训练数据（3分钟）

```bash
python scripts/generate_data.py --num-samples 1000 --output qubo_prover_v3/data/training_data/dataset.json
```

**预期输出：**
```
生成 1000 个训练样本...
100%|████████████████████| 1000/1000 [00:01<00:00, 500.00it/s]
数据集已保存到: qubo_prover_v3/data/training_data/dataset.json
```

---

## 步骤 5：训练神经网络（5分钟）

```bash
python scripts/train_model.py --data qubo_prover_v3/data/training_data/dataset.json --epochs 50
```

**预期输出：**
```
开始训练...
============================================================
Epoch 1/50
  训练损失: 0.6931
  验证损失: 0.6523
  验证准确率: 0.7234

...

Epoch 50/50
  训练损失: 0.0412
  验证损失: 0.0523
  验证准确率: 0.9876
  ✓ 保存最佳模型（验证损失: 0.0523）
```

---

## 步骤 6：测试系统（1分钟）

```bash
# 测试基础功能
python -m qubo_prover_v3.cli --axioms "P; P->Q" --goal "Q"

# 测试神经引导（开发中）
python -m qubo_prover_v3.cli --axioms "P; P->Q" --goal "Q" --use-neural
```

---

## 🎉 完成！

您已经成功：
- ✅ 安装了所有依赖
- ✅ 生成了训练数据
- ✅ 训练了规则选择器神经网络
- ✅ 测试了系统

---

## 📊 当前进度

### 已完成 ✅
- [x] 项目结构
- [x] 特征编码器
- [x] 规则选择器网络
- [x] 数据生成器
- [x] 训练器
- [x] 训练脚本

### 进行中 ⏳
- [ ] QUBO 系统集成
- [ ] 神经引导的 QUBO 构建器
- [ ] 端到端测试

### 待完成 📝
- [ ] 性能评估
- [ ] 文档完善
- [ ] 论文撰写

---

## 🔗 下一步

1. **查看实现细节** - [IMPLEMENTATION.md](IMPLEMENTATION.md)
2. **了解训练过程** - [TRAINING.md](TRAINING.md)
3. **参与开发** - 查看 [README.md](../README.md) 的实施进度

---

**有问题？** 查看 [FAQ](../README.md#常见问题) 或提交 Issue

