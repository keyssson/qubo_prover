"""
命令行接口
"""

import argparse
import sys
from typing import List

from .qubo_builder import QUBOBuilder
from .sampler import make_backend, NealBackend
from .decoder import (
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
        description="QUBO Prover V2 - 动态 QUBO 生成的命题逻辑定理证明器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # Modus Ponens
  python -m qubo_prover_v2.cli --axioms "P; P->Q" --goal "Q"
  
  # 三段论
  python -m qubo_prover_v2.cli --axioms "P; P->Q; Q->R" --goal "R" --reads 150
  
  # Modus Tollens
  python -m qubo_prover_v2.cli --axioms "P->Q; ~Q" --goal "~P"
        """
    )
    
    # 必需参数
    parser.add_argument(
        "--axioms",
        required=True,
        help="公理列表，用分号分隔，如 'P; P->Q'"
    )
    parser.add_argument(
        "--goal",
        required=True,
        help="证明目标，如 'Q'"
    )
    
    # 可选参数
    parser.add_argument(
        "--backend",
        default="neal",
        choices=["neal", "openjij"],
        help="采样后端（默认: neal）"
    )
    parser.add_argument(
        "--reads",
        type=int,
        default=100,
        help="采样次数（默认: 100）"
    )
    parser.add_argument(
        "--axiom-penalty",
        type=float,
        default=100.0,
        help="公理惩罚系数（默认: 100.0）"
    )
    parser.add_argument(
        "--structure-penalty",
        type=float,
        default=10.0,
        help="结构惩罚系数（默认: 10.0）"
    )
    parser.add_argument(
        "--rule-penalty",
        type=float,
        default=5.0,
        help="规则惩罚系数（默认: 5.0）"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细信息"
    )
    parser.add_argument(
        "--show-all-vars",
        action="store_true",
        help="显示所有变量（包括值为 0 的）"
    )
    
    args = parser.parse_args()
    
    # 解析公理
    axioms: List[str] = [a.strip() for a in args.axioms.split(";") if a.strip()]
    goal = args.goal.strip()
    
    if not axioms:
        print("错误: 至少需要一个公理", file=sys.stderr)
        return 1
    
    if not goal:
        print("错误: 目标不能为空", file=sys.stderr)
        return 1
    
    # 打印标题
    print("=" * 70)
    print(" " * 20 + "QUBO Prover V2")
    print("=" * 70)
    print()
    print(f"公理: {axioms}")
    print(f"目标: {goal}")
    print()
    
    try:
        # 1. 构建 QUBO
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
        
        success, message = verify_assignment(assignment, axiom_vars, goal_var)
        
        print(f"验证结果: {message}")
        
        # 5. 输出结果
        print(f"\n[结果]")
        if success:
            print("✓ 证明成功！")
            print()
            print("证明路径:")
            proof_steps = extract_proof_path(assignment, var_info)
            for step in proof_steps:
                print(f"  {step}")
        else:
            print("✗ 证明失败")
            print(f"原因: {message}")
        
        # 6. 显示变量赋值
        if args.verbose or args.show_all_vars:
            print(f"\n[变量赋值]")
            print(format_assignment(assignment, show_zeros=args.show_all_vars))
        else:
            print(f"\n[关键变量赋值]")
            # 只显示值为 1 的变量
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


if __name__ == "__main__":
    sys.exit(main())

