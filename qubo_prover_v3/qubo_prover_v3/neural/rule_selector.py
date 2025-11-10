"""
规则选择器神经网络 - 预测哪些推理规则最有用

功能：
1. 接收特征向量作为输入
2. 输出每个推理规则的权重（0-1之间）
3. 支持训练和推理模式
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List
import numpy as np


class RuleSelectorNetwork(nn.Module):
    """规则选择器神经网络"""
    
    # 推理规则列表（与 V2 的 rule_library.py 对应）
    RULE_NAMES = [
        "modus_ponens",           # P, P->Q ⊢ Q
        "modus_tollens",          # P->Q, ~Q ⊢ ~P
        "and_elimination_left",   # P&Q ⊢ P
        "and_elimination_right",  # P&Q ⊢ Q
        "and_introduction",       # P, Q ⊢ P&Q
        "or_introduction_left",   # P ⊢ P|Q
        "or_introduction_right",  # Q ⊢ P|Q
        "double_negation",        # ~~P ⊢ P
    ]
    
    def __init__(self, input_size=12, hidden_size=64, num_rules=8):
        """
        初始化规则选择器网络
        
        Args:
            input_size: 输入特征维度（默认12）
            hidden_size: 隐藏层大小（默认64）
            num_rules: 规则数量（默认8）
        """
        super(RuleSelectorNetwork, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_rules = num_rules
        
        # 网络结构：3层全连接网络
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, num_rules)
        
        # Dropout 防止过拟合
        self.dropout = nn.Dropout(0.2)
        
        # Batch Normalization 加速训练
        self.bn1 = nn.BatchNorm1d(hidden_size)
        self.bn2 = nn.BatchNorm1d(hidden_size)
    
    def forward(self, x):
        """
        前向传播
        
        Args:
            x: 输入特征，形状为 (batch_size, input_size) 或 (input_size,)
        
        Returns:
            规则权重，形状为 (batch_size, num_rules) 或 (num_rules,)
            每个权重在 0-1 之间
        """
        # 处理单个样本的情况
        if x.dim() == 1:
            x = x.unsqueeze(0)
            squeeze_output = True
        else:
            squeeze_output = False
        
        # 第一层
        x = self.fc1(x)
        if x.size(0) > 1:  # Batch Normalization 需要 batch_size > 1
            x = self.bn1(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        # 第二层
        x = self.fc2(x)
        if x.size(0) > 1:
            x = self.bn2(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        # 输出层
        x = self.fc3(x)
        x = torch.sigmoid(x)  # 输出 0-1 之间的权重
        
        # 如果输入是单个样本，输出也应该是单个样本
        if squeeze_output:
            x = x.squeeze(0)
        
        return x
    
    def predict_rule_weights(self, features: np.ndarray) -> Dict[str, float]:
        """
        预测规则权重（推理模式）
        
        Args:
            features: 特征向量，形状为 (input_size,)
        
        Returns:
            规则权重字典，例如 {"modus_ponens": 0.95, ...}
        """
        self.eval()  # 设置为评估模式
        
        with torch.no_grad():
            # 转换为 Tensor
            features_tensor = torch.tensor(features, dtype=torch.float32)
            
            # 前向传播
            weights = self.forward(features_tensor)
            
            # 转换为字典
            weights_dict = {}
            for i, rule_name in enumerate(self.RULE_NAMES):
                weights_dict[rule_name] = float(weights[i])
        
        return weights_dict
    
    def get_rule_names(self) -> List[str]:
        """获取规则名称列表"""
        return self.RULE_NAMES.copy()


# 示例用法
if __name__ == "__main__":
    # 创建模型
    model = RuleSelectorNetwork(input_size=12, hidden_size=64, num_rules=8)
    
    print("=" * 60)
    print("规则选择器神经网络")
    print("=" * 60)
    print(f"输入维度: {model.input_size}")
    print(f"隐藏层大小: {model.hidden_size}")
    print(f"输出维度（规则数量）: {model.num_rules}")
    print(f"规则列表: {model.get_rule_names()}")
    print()
    
    # 测试前向传播
    print("测试前向传播：")
    test_features = torch.randn(1, 12)  # 随机特征
    output = model(test_features)
    print(f"输入形状: {test_features.shape}")
    print(f"输出形状: {output.shape}")
    print(f"输出值: {output}")
    print()
    
    # 测试预测接口
    print("测试预测接口：")
    test_features_np = np.random.randn(12).astype(np.float32)
    weights_dict = model.predict_rule_weights(test_features_np)
    print("预测的规则权重：")
    for rule_name, weight in weights_dict.items():
        print(f"  {rule_name:25s}: {weight:.4f}")

