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
from typing import List

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qubo_prover_v3.core.qubo_builder import QUBOBuilder
from qubo_prover_v3.neural.neural_guided_builder import NeuralGuidedQUBOBuilder
from qubo_prover_v3.core.sampler import make_backend, NealBackend
from qubo_prover_v3.core.decoder import (
    decode_sampleset,
    decode_openjij_response,
    best_by_lowest_energy,
    verify_assignment,
    extract_proof_path,
    format_assignment,
)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='QUBO 命题逻辑自动定理证明器 V3 - 神经引导版本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用神经引导的 Modus Ponens
  python -m qubo_prover_v3.cli --axioms "P; P->Q" --goal "Q" --use-neural

  # 不使用神经引导（baseline）
  python -m qubo_prover_v3.cli --axioms "P; P->Q" --goal "Q"

  # Modus Tollens
  python -m qubo_prover_v3.cli --axioms "P->Q; ~Q" --goal "~P" --use-neural

  # 三段论
  python -m qubo_prover_v3.cli --axioms "P; P->Q; Q->R" --goal "R" --use-neural --reads 150
        """
    )

    # 必需参数
    parser.add_argument('--axioms', type=str, required=True,
                        help='公理列表，用分号分隔，例如 "P; P->Q"')
    parser.add_argument('--goal', type=str, required=True,
                        help='证明目标，例如 "Q"')

    # 神经网络相关
    parser.add_argument('--use-neural', action='store_true',
                        help='使用神经网络引导（默认: 不使用）')
    parser.add_argument('--model-path', type=str,
                        default='qubo_prover_v3/qubo_prover_v3/neural/models/rule_selector_v1.pth',
                        help='神经网络模型路径')
    parser.add_argument('--show-weights', action='store_true',
                        help='显示神经网络预测的规则权重')

    # QUBO 求解器相关
    parser.add_argument('--backend', type=str, default='neal',
                        choices=['neal', 'openjij'],
                        help='QUBO 求解器后端（默认: neal）')
    parser.add_argument('--reads', type=int, default=100,
                        help='采样次数（默认: 100）')

    # 惩罚系数
    parser.add_argument('--axiom-penalty', type=float, default=100.0,
                        help='公理惩罚系数（默认: 100.0）')
    parser.add_argument('--structure-penalty', type=float, default=10.0,
                        help='结构惩罚系数（默认: 10.0）')
    parser.add_argument('--rule-penalty', type=float, default=5.0,
                        help='规则惩罚系数（默认: 5.0）')

    # 显示选项
    parser.add_argument('--verbose', action='store_true',
                        help='显示详细信息')
    parser.add_argument('--show-all-vars', action='store_true',
                        help='显示所有变量（包括值为 0 的）')
    parser.add_argument('--show-qubo', action='store_true',
                        help='显示完整的 QUBO 方程')

    args = parser.parse_args()

    # 解析公理
    axioms: List[str] = [ax.strip() for ax in args.axioms.split(';') if ax.strip()]
    goal = args.goal.strip()

    if not axioms:
        print("错误: 至少需要一个公理", file=sys.stderr)
        return 1

    if not goal:
        print("错误: 目标不能为空", file=sys.stderr)
        return 1

    # 打印标题
    print("=" * 70)
    print(" " * 15 + "QUBO Prover V3 - 神经引导版本")
    print("=" * 70)
    print()
    print(f"公理: {axioms}")
    print(f"目标: {goal}")
    print(f"神经引导: {'✓ 是' if args.use_neural else '✗ 否（baseline）'}")
    print(f"后端: {args.backend}")
    print(f"采样次数: {args.reads}")
    print()

    try:
        # 1. 构建 QUBO
        if args.use_neural:
            print("[神经引导模式]")
            builder = NeuralGuidedQUBOBuilder(
                model_path=args.model_path,
                use_neural_weights=True,
                axiom_penalty=args.axiom_penalty,
                structure_penalty=args.structure_penalty,
                base_rule_penalty=args.rule_penalty
            )

            # 显示规则权重
            if args.show_weights:
                weights = builder.predict_rule_weights(axioms, goal)
                print("\n神经网络预测的规则权重:")
                for rule_name, weight in sorted(weights.items(), key=lambda x: -x[1]):
                    penalty = builder.get_rule_penalty(rule_name)
                    print(f"  {rule_name:25s}: 权重={weight:.4f}, 惩罚系数={penalty:.2f}")
                print()
        else:
            print("[Baseline 模式（固定权重）]")
            builder = QUBOBuilder(
                axiom_penalty=args.axiom_penalty,
                structure_penalty=args.structure_penalty,
                rule_penalty=args.rule_penalty
            )

        model, var_map, offset = builder.build(axioms, goal)
        qubo, bqm, offset = builder.compile_qubo(model)

        if args.verbose:
            print()
            print(builder.summary())

        # 显示 QUBO 方程
        if args.show_qubo or args.verbose:
            print(f"\n[QUBO 方程]")
            print("=" * 70)
            _display_qubo_equation(qubo, offset)

        # 2. 采样
        print(f"\n[采样阶段]")
        backend = make_backend(args.backend)
        print(f"使用后端: {backend.name()}")
        print(f"采样次数: {args.reads}")

        if isinstance(backend, NealBackend):
            sampleset = backend.sample_bqm(bqm, args.reads)
            rows = decode_sampleset(sampleset)
        else:
            resp = backend.sample_bqm(bqm, args.reads)
            rows = decode_openjij_response(resp)

        # 3. 选择最佳解
        assignment, energy = best_by_lowest_energy(rows)

        print(f"最低能量: {energy}")

        # 4. 验证
        print(f"\n[验证阶段]")
        var_info = builder.get_variable_info()
        axiom_vars = var_info["axiom_vars"]
        goal_var = var_info["goal_var"]

        success, message = verify_assignment(assignment, axiom_vars, goal_var, var_info)

        print(f"验证结果: {message}")

        # 5. 输出结果
        print(f"\n[结果]")
        if success:
            print("✓ 证明成功！")
            print()
            print("=" * 70)
            print("详细证明路径:")
            print("=" * 70)
            proof_steps = extract_proof_path(assignment, var_info)
            for step in proof_steps:
                print(step)
            print("=" * 70)
        else:
            print("✗ 证明失败")
            print(f"原因: {message}")

        # 6. 显示变量赋值
        if args.verbose or args.show_all_vars:
            print(f"\n[变量赋值]")
            print(format_assignment(assignment, show_zeros=args.show_all_vars))
        else:
            print(f"\n[关键变量赋值]")
            print(format_assignment(assignment, show_zeros=False))

        print()
        print("=" * 70)

        return 0 if success else 1

    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 2


def _display_qubo_equation(qubo: dict, offset: float):
    """显示完整的 QUBO 方程"""
    print("能量函数 E(x) = Σ Q_ij * x_i * x_j + offset")
    print()
    print("其中:")

    # 分类显示
    linear_terms = []
    quadratic_terms = []

    for (i, j), coeff in sorted(qubo.items()):
        if i == j:
            linear_terms.append((i, coeff))
        else:
            quadratic_terms.append((i, j, coeff))

    # 显示线性项
    if linear_terms:
        print("  线性项（一次项）:")
        for var, coeff in linear_terms[:10]:  # 只显示前10个
            sign = "+" if coeff >= 0 else ""
            print(f"    {sign}{coeff:.1f} * {var}")
        if len(linear_terms) > 10:
            print(f"    ... 还有 {len(linear_terms) - 10} 个线性项")

    # 显示二次项
    if quadratic_terms:
        print()
        print("  二次项（交叉项）:")
        for var1, var2, coeff in quadratic_terms[:10]:  # 只显示前10个
            sign = "+" if coeff >= 0 else ""
            print(f"    {sign}{coeff:.1f} * {var1} * {var2}")
        if len(quadratic_terms) > 10:
            print(f"    ... 还有 {len(quadratic_terms) - 10} 个二次项")

    # 显示常数项
    print()
    print(f"  常数项（offset）: {offset:.1f}")
    print()
    print(f"总计: {len(linear_terms)} 个线性项 + {len(quadratic_terms)} 个二次项")
    print("=" * 70)


if __name__ == "__main__":
    sys.exit(main())

