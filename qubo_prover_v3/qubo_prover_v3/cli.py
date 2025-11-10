"""
命令行接口 - V3 神经引导版本

用法:
    # 使用神经引导
    python -m qubo_prover_v3.cli --axioms "P; P->Q" --goal "Q" --use-neural
    
    # 不使用神经引导（baseline）
    python -m qubo_prover_v3.cli --axioms "P; P->Q" --goal "Q"
"""

import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(
        description='QUBO 命题逻辑自动定理证明器 V3 - 神经引导版本'
    )
    
    parser.add_argument('--axioms', type=str, required=True,
                        help='公理列表，用分号分隔，例如 "P; P->Q"')
    parser.add_argument('--goal', type=str, required=True,
                        help='证明目标，例如 "Q"')
    parser.add_argument('--use-neural', action='store_true',
                        help='使用神经网络引导（默认: 不使用）')
    parser.add_argument('--model-path', type=str,
                        default='qubo_prover_v3/neural/models/rule_selector_v1.pth',
                        help='神经网络模型路径')
    parser.add_argument('--backend', type=str, default='neal',
                        choices=['neal', 'exact'],
                        help='QUBO 求解器后端（默认: neal）')
    parser.add_argument('--num-reads', type=int, default=100,
                        help='采样次数（默认: 100）')
    parser.add_argument('--show-weights', action='store_true',
                        help='显示神经网络预测的规则权重')
    
    args = parser.parse_args()
    
    # 解析公理
    axioms = [ax.strip() for ax in args.axioms.split(';')]
    goal = args.goal.strip()
    
    print("=" * 60)
    print("QUBO 命题逻辑自动定理证明器 V3")
    print("=" * 60)
    print(f"公理: {axioms}")
    print(f"目标: {goal}")
    print(f"神经引导: {'是' if args.use_neural else '否'}")
    print(f"后端: {args.backend}")
    print()
    
    if args.use_neural:
        print("⚠️  神经引导功能正在开发中...")
        print("⚠️  当前版本仅支持基础 QUBO 证明")
        print()
        print("提示: 请先运行以下步骤:")
        print("  1. 生成训练数据: python scripts/generate_data.py")
        print("  2. 训练模型: python scripts/train_model.py --data ...")
        print("  3. 然后再使用 --use-neural 选项")
        print()
        return
    
    # TODO: 集成 V2 的 QUBO 系统
    print("⚠️  基础 QUBO 证明功能正在集成中...")
    print()
    print("当前进度:")
    print("  ✓ 项目结构创建完成")
    print("  ✓ 特征编码器实现完成")
    print("  ✓ 规则选择器网络实现完成")
    print("  ✓ 数据生成器实现完成")
    print("  ✓ 训练器实现完成")
    print("  ⏳ QUBO 系统集成中...")
    print()
    print("下一步:")
    print("  1. 复制 V2 的核心代码")
    print("  2. 修改 QUBO 构建器以支持动态权重")
    print("  3. 集成神经网络预测")
    print("  4. 端到端测试")


if __name__ == "__main__":
    main()

