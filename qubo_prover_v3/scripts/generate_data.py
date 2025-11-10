"""
生成训练数据脚本

用法:
    python scripts/generate_data.py --num-samples 10000 --output qubo_prover_v3/data/training_data/dataset.json
"""

import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qubo_prover_v3.data.generator import TrainingDataGenerator


def main():
    parser = argparse.ArgumentParser(description='生成训练数据')
    parser.add_argument('--num-samples', type=int, default=10000,
                        help='生成的样本数量（默认: 10000）')
    parser.add_argument('--output', type=str, 
                        default='qubo_prover_v3/data/training_data/dataset.json',
                        help='输出文件路径')
    parser.add_argument('--seed', type=int, default=42,
                        help='随机种子（默认: 42）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("训练数据生成器")
    print("=" * 60)
    print(f"样本数量: {args.num_samples}")
    print(f"输出路径: {args.output}")
    print(f"随机种子: {args.seed}")
    print()
    
    # 创建生成器
    generator = TrainingDataGenerator(seed=args.seed)
    
    # 生成数据集
    dataset = generator.generate_dataset(args.num_samples)
    
    # 保存数据集
    generator.save_dataset(dataset, args.output)
    
    # 统计信息
    print("\n数据集统计:")
    print("=" * 60)
    
    template_counts = {}
    for sample in dataset:
        template_name = sample['template_name']
        template_counts[template_name] = template_counts.get(template_name, 0) + 1
    
    for template_name, count in sorted(template_counts.items()):
        percentage = count / len(dataset) * 100
        print(f"  {template_name:25s}: {count:5d} ({percentage:5.2f}%)")
    
    print("\n✓ 数据生成完成！")


if __name__ == "__main__":
    main()

