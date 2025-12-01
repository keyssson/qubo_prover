"""
规则选择器神经网络

预测哪些推理规则最可能用于证明。

改进点：
1. 更深的网络结构
2. 残差连接
3. 注意力机制（可选）
4. 更好的正则化
"""

from __future__ import annotations
from typing import Dict, List, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


# 规则名称列表
RULE_NAMES = [
    "modus_ponens",           # P, P→Q ⊢ Q
    "modus_tollens",          # P→Q, ~Q ⊢ ~P
    "and_intro",              # P, Q ⊢ P∧Q
    "and_elim_left",          # P∧Q ⊢ P
    "and_elim_right",         # P∧Q ⊢ Q
    "or_intro_left",          # P ⊢ P∨Q
    "or_intro_right",         # Q ⊢ P∨Q
    "or_elim",                # P∨Q, ~P ⊢ Q
    "not_intro",              # 归谬法
    "double_neg_elim",        # ~~P ⊢ P
    "imply_intro",            # [P]...Q ⊢ P→Q
    "resolution",             # 归结消解
]


class ResidualBlock(nn.Module):
    """残差块"""
    
    def __init__(self, hidden_size: int, dropout: float = 0.2):
        super().__init__()
        self.fc1 = nn.Linear(hidden_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.bn1 = nn.BatchNorm1d(hidden_size)
        self.bn2 = nn.BatchNorm1d(hidden_size)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        identity = x
        
        out = self.fc1(x)
        if x.size(0) > 1:
            out = self.bn1(out)
        out = F.relu(out)
        out = self.dropout(out)
        
        out = self.fc2(out)
        if x.size(0) > 1:
            out = self.bn2(out)
        
        out = out + identity  # 残差连接
        out = F.relu(out)
        
        return out


class RuleSelectorNetwork(nn.Module):
    """
    规则选择器神经网络
    
    输入：特征向量
    输出：每个规则的权重（0-1之间）
    """
    
    def __init__(self, 
                 input_size: int = 32,
                 hidden_size: int = 128,
                 num_rules: int = 12,
                 num_residual_blocks: int = 2,
                 dropout: float = 0.2):
        """
        初始化网络
        
        Args:
            input_size: 输入特征维度
            hidden_size: 隐藏层大小
            num_rules: 规则数量
            num_residual_blocks: 残差块数量
            dropout: Dropout 概率
        """
        super().__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_rules = num_rules
        
        # 输入层
        self.input_layer = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.BatchNorm1d(hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # 残差块
        self.residual_blocks = nn.ModuleList([
            ResidualBlock(hidden_size, dropout)
            for _ in range(num_residual_blocks)
        ])
        
        # 输出层
        self.output_layer = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, num_rules),
            nn.Sigmoid()  # 输出 0-1 之间的权重
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: 输入特征 (batch_size, input_size) 或 (input_size,)
            
        Returns:
            规则权重 (batch_size, num_rules) 或 (num_rules,)
        """
        # 处理单样本
        squeeze_output = False
        if x.dim() == 1:
            x = x.unsqueeze(0)
            squeeze_output = True
        
        # 输入层
        x = self.input_layer(x)
        
        # 残差块
        for block in self.residual_blocks:
            x = block(x)
        
        # 输出层
        x = self.output_layer(x)
        
        if squeeze_output:
            x = x.squeeze(0)
        
        return x
    
    def predict(self, features: np.ndarray) -> Dict[str, float]:
        """
        预测规则权重（推理模式）
        
        Args:
            features: 特征向量
            
        Returns:
            规则权重字典
        """
        self.eval()
        
        with torch.no_grad():
            x = torch.tensor(features, dtype=torch.float32)
            weights = self.forward(x)
            
            result = {}
            for i, rule_name in enumerate(RULE_NAMES):
                result[rule_name] = float(weights[i])
        
        return result
    
    def get_rule_names(self) -> List[str]:
        """获取规则名称列表"""
        return RULE_NAMES.copy()
    
    def save(self, path: str):
        """保存模型"""
        torch.save({
            'state_dict': self.state_dict(),
            'input_size': self.input_size,
            'hidden_size': self.hidden_size,
            'num_rules': self.num_rules,
        }, path)
    
    @classmethod
    def load(cls, path: str) -> RuleSelectorNetwork:
        """加载模型"""
        checkpoint = torch.load(path, map_location='cpu', weights_only=True)
        
        model = cls(
            input_size=checkpoint.get('input_size', 32),
            hidden_size=checkpoint.get('hidden_size', 128),
            num_rules=checkpoint.get('num_rules', 12)
        )
        model.load_state_dict(checkpoint['state_dict'])
        model.eval()
        
        return model


def create_model(input_size: int = 32, 
                 hidden_size: int = 128,
                 pretrained_path: Optional[str] = None) -> RuleSelectorNetwork:
    """
    创建模型
    
    Args:
        input_size: 输入维度
        hidden_size: 隐藏层大小
        pretrained_path: 预训练模型路径
        
    Returns:
        规则选择器网络
    """
    if pretrained_path:
        try:
            return RuleSelectorNetwork.load(pretrained_path)
        except Exception as e:
            print(f"加载预训练模型失败: {e}")
            print("使用随机初始化")
    
    return RuleSelectorNetwork(input_size=input_size, hidden_size=hidden_size)


# 简单的训练函数
def train_model(model: RuleSelectorNetwork,
                train_data: List[tuple],
                epochs: int = 100,
                lr: float = 0.001,
                verbose: bool = True) -> List[float]:
    """
    训练模型
    
    Args:
        model: 模型
        train_data: 训练数据 [(features, labels), ...]
        epochs: 训练轮数
        lr: 学习率
        verbose: 是否输出训练信息
        
    Returns:
        损失历史
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()
    
    losses = []
    model.train()
    
    for epoch in range(epochs):
        epoch_loss = 0.0
        
        for features, labels in train_data:
            x = torch.tensor(features, dtype=torch.float32)
            y = torch.tensor(labels, dtype=torch.float32)
            
            optimizer.zero_grad()
            outputs = model(x)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
        
        avg_loss = epoch_loss / len(train_data)
        losses.append(avg_loss)
        
        if verbose and (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
    
    return losses

