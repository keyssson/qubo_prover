"""
神经网络模块测试
"""

import sys
import os
import numpy as np
import torch

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qubo_prover_v3.neural.feature_encoder import FeatureEncoder
from qubo_prover_v3.neural.rule_selector import RuleSelectorNetwork


def test_feature_encoder():
    """测试特征编码器"""
    print("=" * 60)
    print("测试特征编码器")
    print("=" * 60)
    
    encoder = FeatureEncoder()
    
    # 测试案例1：Modus Ponens
    axioms1 = ["P", "P->Q"]
    goal1 = "Q"
    features1 = encoder.encode(axioms1, goal1)
    
    print(f"\n案例1: Modus Ponens")
    print(f"  公理: {axioms1}")
    print(f"  目标: {goal1}")
    print(f"  特征维度: {features1.shape}")
    print(f"  特征值: {features1}")
    
    assert features1.shape == (12,), "特征维度应该是12"
    assert features1[0] == 2, "公理数量应该是2"
    assert features1[1] == 1, "应该包含蕴涵"
    
    # 测试案例2：复杂公式
    axioms2 = ["P&Q", "(P&Q)->R", "~R"]
    goal2 = "~P|~Q"
    features2 = encoder.encode(axioms2, goal2)
    
    print(f"\n案例2: 复杂公式")
    print(f"  公理: {axioms2}")
    print(f"  目标: {goal2}")
    print(f"  特征维度: {features2.shape}")
    print(f"  特征值: {features2}")
    
    assert features2.shape == (12,), "特征维度应该是12"
    assert features2[0] == 3, "公理数量应该是3"
    
    print("\n✓ 特征编码器测试通过！")


def test_rule_selector():
    """测试规则选择器"""
    print("\n" + "=" * 60)
    print("测试规则选择器")
    print("=" * 60)
    
    model = RuleSelectorNetwork(input_size=12, hidden_size=64, num_rules=8)
    
    # 测试前向传播
    test_features = torch.randn(5, 12)  # 批次大小为5
    output = model(test_features)
    
    print(f"\n前向传播测试:")
    print(f"  输入形状: {test_features.shape}")
    print(f"  输出形状: {output.shape}")
    print(f"  输出范围: [{output.min():.4f}, {output.max():.4f}]")
    
    assert output.shape == (5, 8), "输出形状应该是 (5, 8)"
    assert (output >= 0).all() and (output <= 1).all(), "输出应该在 [0, 1] 范围内"
    
    # 测试单个样本
    single_features = torch.randn(12)
    single_output = model(single_features)
    
    print(f"\n单样本测试:")
    print(f"  输入形状: {single_features.shape}")
    print(f"  输出形状: {single_output.shape}")
    
    assert single_output.shape == (8,), "单样本输出形状应该是 (8,)"
    
    # 测试预测接口
    test_features_np = np.random.randn(12).astype(np.float32)
    weights_dict = model.predict_rule_weights(test_features_np)
    
    print(f"\n预测接口测试:")
    print(f"  输入类型: {type(test_features_np)}")
    print(f"  输出类型: {type(weights_dict)}")
    print(f"  规则数量: {len(weights_dict)}")
    
    assert len(weights_dict) == 8, "应该有8个规则"
    assert all(0 <= w <= 1 for w in weights_dict.values()), "权重应该在 [0, 1] 范围内"
    
    print("\n预测的规则权重:")
    for rule_name, weight in weights_dict.items():
        print(f"  {rule_name:25s}: {weight:.4f}")
    
    print("\n✓ 规则选择器测试通过！")


def test_integration():
    """集成测试"""
    print("\n" + "=" * 60)
    print("集成测试")
    print("=" * 60)
    
    # 创建编码器和模型
    encoder = FeatureEncoder()
    model = RuleSelectorNetwork(input_size=12, hidden_size=64, num_rules=8)
    
    # 测试完整流程
    axioms = ["P", "P->Q"]
    goal = "Q"
    
    print(f"\n测试问题:")
    print(f"  公理: {axioms}")
    print(f"  目标: {goal}")
    
    # 1. 编码特征
    features = encoder.encode(axioms, goal)
    print(f"\n1. 特征编码:")
    print(f"  特征向量: {features}")
    
    # 2. 预测规则权重
    weights = model.predict_rule_weights(features)
    print(f"\n2. 规则权重预测:")
    for rule_name, weight in weights.items():
        print(f"  {rule_name:25s}: {weight:.4f}")
    
    # 3. 找出最有用的规则
    top_rules = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"\n3. 最有用的3个规则:")
    for rule_name, weight in top_rules:
        print(f"  {rule_name:25s}: {weight:.4f}")
    
    print("\n✓ 集成测试通过！")


if __name__ == "__main__":
    test_feature_encoder()
    test_rule_selector()
    test_integration()
    
    print("\n" + "=" * 60)
    print("所有测试通过！ ✓")
    print("=" * 60)

