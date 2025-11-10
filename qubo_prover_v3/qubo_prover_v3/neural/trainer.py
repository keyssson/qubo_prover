"""
训练器 - 训练规则选择器神经网络

功能：
1. 加载训练数据
2. 训练神经网络
3. 验证和评估
4. 保存模型
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import List, Dict, Tuple
import json
from tqdm import tqdm

from .feature_encoder import FeatureEncoder
from .rule_selector import RuleSelectorNetwork


class LogicProofDataset(Dataset):
    """逻辑证明数据集"""
    
    def __init__(self, data_path: str, feature_encoder: FeatureEncoder):
        """
        初始化数据集
        
        Args:
            data_path: 数据文件路径（JSON格式）
            feature_encoder: 特征编码器
        """
        self.feature_encoder = feature_encoder
        
        # 加载数据
        with open(data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        print(f"加载了 {len(self.data)} 个样本")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        """
        获取一个样本
        
        Returns:
            features: 特征向量
            labels: 标签向量（哪些规则有用）
        """
        sample = self.data[idx]
        
        # 编码特征
        features = self.feature_encoder.encode(sample['axioms'], sample['goal'])
        
        # 创建标签（one-hot编码）
        labels = np.zeros(8, dtype=np.float32)  # 8个规则
        
        # 规则名称到索引的映射
        rule_to_idx = {
            "modus_ponens": 0,
            "modus_tollens": 1,
            "and_elimination_left": 2,
            "and_elimination_right": 3,
            "and_introduction": 4,
            "or_introduction_left": 5,
            "or_introduction_right": 6,
            "double_negation": 7,
        }
        
        # 标记有用的规则
        for rule_name in sample['useful_rules']:
            if rule_name in rule_to_idx:
                labels[rule_to_idx[rule_name]] = 1.0
        
        return torch.tensor(features), torch.tensor(labels)


class Trainer:
    """训练器"""
    
    def __init__(self, model: RuleSelectorNetwork, device='cpu'):
        """
        初始化训练器
        
        Args:
            model: 规则选择器模型
            device: 设备（'cpu' 或 'cuda'）
        """
        self.model = model
        self.device = device
        self.model.to(device)
        
        # 损失函数：二元交叉熵
        self.criterion = nn.BCELoss()
        
        # 优化器：Adam
        self.optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        # 学习率调度器
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=5, verbose=True
        )
    
    def train_epoch(self, train_loader: DataLoader) -> float:
        """
        训练一个 epoch
        
        Args:
            train_loader: 训练数据加载器
        
        Returns:
            平均损失
        """
        self.model.train()
        total_loss = 0.0
        
        for features, labels in tqdm(train_loader, desc="训练"):
            features = features.to(self.device)
            labels = labels.to(self.device)
            
            # 前向传播
            outputs = self.model(features)
            loss = self.criterion(outputs, labels)
            
            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
        
        return total_loss / len(train_loader)
    
    def validate(self, val_loader: DataLoader) -> Tuple[float, float]:
        """
        验证模型
        
        Args:
            val_loader: 验证数据加载器
        
        Returns:
            (平均损失, 准确率)
        """
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for features, labels in val_loader:
                features = features.to(self.device)
                labels = labels.to(self.device)
                
                # 前向传播
                outputs = self.model(features)
                loss = self.criterion(outputs, labels)
                
                total_loss += loss.item()
                
                # 计算准确率（阈值0.5）
                predictions = (outputs > 0.5).float()
                correct += (predictions == labels).sum().item()
                total += labels.numel()
        
        avg_loss = total_loss / len(val_loader)
        accuracy = correct / total
        
        return avg_loss, accuracy
    
    def save_model(self, path: str):
        """保存模型"""
        torch.save(self.model.state_dict(), path)
        print(f"模型已保存到: {path}")

