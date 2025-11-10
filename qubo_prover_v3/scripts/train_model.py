"""
训练模型脚本

用法:
    python scripts/train_model.py --data qubo_prover_v3/data/training_data/dataset.json --epochs 100
"""

import argparse
import sys
import os
import torch
from torch.utils.data import DataLoader, random_split

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qubo_prover_v3.neural.feature_encoder import FeatureEncoder
from qubo_prover_v3.neural.rule_selector import RuleSelectorNetwork
from qubo_prover_v3.neural.trainer import Trainer, LogicProofDataset


def main():
    parser = argparse.ArgumentParser(description='训练规则选择器模型')
    parser.add_argument('--data', type=str, required=True,
                        help='训练数据路径（JSON文件）')
    parser.add_argument('--epochs', type=int, default=100,
                        help='训练轮数（默认: 100）')
    parser.add_argument('--batch-size', type=int, default=32,
                        help='批次大小（默认: 32）')
    parser.add_argument('--val-split', type=float, default=0.2,
                        help='验证集比例（默认: 0.2）')
    parser.add_argument('--output', type=str,
                        default='qubo_prover_v3/qubo_prover_v3/neural/models/rule_selector_v1.pth',
                        help='输出模型路径')
    parser.add_argument('--device', type=str, default='cpu',
                        choices=['cpu', 'cuda'],
                        help='设备（默认: cpu）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("规则选择器训练")
    print("=" * 60)
    print(f"数据路径: {args.data}")
    print(f"训练轮数: {args.epochs}")
    print(f"批次大小: {args.batch_size}")
    print(f"验证集比例: {args.val_split}")
    print(f"设备: {args.device}")
    print()
    
    # 检查 CUDA 可用性
    if args.device == 'cuda' and not torch.cuda.is_available():
        print("警告: CUDA 不可用，使用 CPU")
        args.device = 'cpu'
    
    # 创建特征编码器
    feature_encoder = FeatureEncoder()
    
    # 加载数据集
    print("加载数据集...")
    dataset = LogicProofDataset(args.data, feature_encoder)
    
    # 划分训练集和验证集
    val_size = int(len(dataset) * args.val_split)
    train_size = len(dataset) - val_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
    
    print(f"训练集大小: {train_size}")
    print(f"验证集大小: {val_size}")
    print()
    
    # 创建数据加载器
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    
    # 创建模型
    model = RuleSelectorNetwork(
        input_size=feature_encoder.get_feature_dim(),
        hidden_size=64,
        num_rules=8
    )
    
    print(f"模型参数数量: {sum(p.numel() for p in model.parameters())}")
    print()
    
    # 创建训练器
    trainer = Trainer(model, device=args.device)
    
    # 训练循环
    best_val_loss = float('inf')
    
    print("开始训练...")
    print("=" * 60)
    
    for epoch in range(args.epochs):
        # 训练
        train_loss = trainer.train_epoch(train_loader)
        
        # 验证
        val_loss, val_accuracy = trainer.validate(val_loader)
        
        # 更新学习率
        trainer.scheduler.step(val_loss)
        
        # 打印进度
        print(f"Epoch {epoch+1}/{args.epochs}")
        print(f"  训练损失: {train_loss:.4f}")
        print(f"  验证损失: {val_loss:.4f}")
        print(f"  验证准确率: {val_accuracy:.4f}")
        print()
        
        # 保存最佳模型
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            trainer.save_model(args.output)
            print(f"  ✓ 保存最佳模型（验证损失: {val_loss:.4f}）")
            print()
    
    print("=" * 60)
    print("训练完成！")
    print(f"最佳验证损失: {best_val_loss:.4f}")
    print(f"模型已保存到: {args.output}")


if __name__ == "__main__":
    main()

