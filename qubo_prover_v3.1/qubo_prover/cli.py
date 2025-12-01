"""
命令行接口

QUBO Prover V3.1 - 神经引导的命题逻辑自动定理证明器

用法:
    # 基本用法
    python -m qubo_prover.cli --axioms "P; P->Q" --goal "Q"
    
    # 使用神经网络引导
    python -m qubo_prover.cli --axioms "P; P->Q" --goal "Q" --use-neural
    
    # 使用符号证明器
    python -m qubo_prover.cli --axioms "P; P->Q" --goal "Q" --mode symbolic
"""

import argparse
import sys
import time
from typing import List, Optional

from .logic.parser import parse, parse_axioms
from .logic.evaluator import entails
from .proof.search import prove, SearchConfig, SearchStrategy

# 延迟导入 QUBO 相关模块（可能需要 pyqubo）
_QUBO_AVAILABLE = None

def _check_qubo_available():
    global _QUBO_AVAILABLE
    if _QUBO_AVAILABLE is None:
        try:
            from .qubo.builder import QUBOBuilder, build_qubo
            from .solver.backends import make_backend, list_backends
            from .solver.decoder import decode_result, format_proof_output
            _QUBO_AVAILABLE = True
        except ImportError as e:
            _QUBO_AVAILABLE = False
            print(f"警告: QUBO 模块不可用 ({e})")
            print("提示: 运行 'pip install pyqubo dwave-neal' 安装依赖")
    return _QUBO_AVAILABLE

def _get_qubo_modules():
    """获取 QUBO 相关模块"""
    from .qubo.builder import QUBOBuilder, build_qubo
    from .solver.backends import make_backend, list_backends
    from .solver.decoder import decode_result, format_proof_output
    return QUBOBuilder, build_qubo, make_backend, list_backends, decode_result, format_proof_output

# 神经网络模块（可选）
_NEURAL_AVAILABLE = None

def _check_neural_available():
    global _NEURAL_AVAILABLE
    if _NEURAL_AVAILABLE is None:
        try:
            from .neural.predictor import RulePredictor
            _NEURAL_AVAILABLE = True
        except ImportError:
            _NEURAL_AVAILABLE = False
    return _NEURAL_AVAILABLE

def _get_neural_modules():
    from .neural.predictor import RulePredictor
    return RulePredictor


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='QUBO Prover V3.1 - 神经引导的命题逻辑自动定理证明器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本 QUBO 证明
  python -m qubo_prover.cli --axioms "P; P->Q" --goal "Q"

  # 使用神经网络引导
  python -m qubo_prover.cli --axioms "P; P->Q" --goal "Q" --use-neural

  # 符号证明（不使用 QUBO）
  python -m qubo_prover.cli --axioms "P; P->Q" --goal "Q" --mode symbolic

  # Modus Tollens
  python -m qubo_prover.cli --axioms "P->Q; ~Q" --goal "~P"

  # 三段论
  python -m qubo_prover.cli --axioms "P; P->Q; Q->R" --goal "R" --reads 200

  # 列出可用后端
  python -m qubo_prover.cli --list-backends
        """
    )
    
    # 证明参数
    parser.add_argument('--axioms', type=str,
                        help='公理列表，用分号分隔，例如 "P; P->Q"')
    parser.add_argument('--goal', type=str,
                        help='证明目标，例如 "Q"')
    
    # 模式选择
    parser.add_argument('--mode', type=str, default='qubo',
                        choices=['qubo', 'symbolic', 'hybrid'],
                        help='证明模式 (默认: qubo)')
    
    # 神经网络
    parser.add_argument('--use-neural', action='store_true',
                        help='使用神经网络引导')
    parser.add_argument('--model-path', type=str, default=None,
                        help='神经网络模型路径')
    parser.add_argument('--show-weights', action='store_true',
                        help='显示预测的规则权重')
    
    # QUBO 参数
    parser.add_argument('--backend', type=str, default='neal',
                        help='QUBO 求解器后端 (默认: neal)')
    parser.add_argument('--reads', type=int, default=100,
                        help='采样次数 (默认: 100)')
    parser.add_argument('--axiom-penalty', type=float, default=100.0,
                        help='公理惩罚系数 (默认: 100.0)')
    parser.add_argument('--structure-penalty', type=float, default=20.0,
                        help='结构惩罚系数 (默认: 20.0)')
    
    # 输出选项
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='详细输出')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='静默模式')
    parser.add_argument('--show-qubo', action='store_true',
                        help='显示 QUBO 方程')
    
    # 其他
    parser.add_argument('--list-backends', action='store_true',
                        help='列出可用的求解器后端')
    parser.add_argument('--check-entailment', action='store_true',
                        help='仅检查语义蕴涵（不进行证明）')
    
    args = parser.parse_args()
    
    # 列出后端
    if args.list_backends:
        if not _check_qubo_available():
            print("QUBO 模块不可用，无法列出后端")
            return 1
        _, _, _, list_backends, _, _ = _get_qubo_modules()
        print("可用的求解器后端:")
        for backend in list_backends():
            status = "✓" if backend['available'] else "✗"
            print(f"  {status} {backend['name']}")
        return 0
    
    # 检查必需参数
    if not args.axioms or not args.goal:
        parser.print_help()
        print("\n错误: 必须指定 --axioms 和 --goal")
        return 1
    
    # 解析输入
    axiom_strs = [ax.strip() for ax in args.axioms.split(';') if ax.strip()]
    goal_str = args.goal.strip()
    
    if not axiom_strs:
        print("错误: 至少需要一个公理")
        return 1
    
    # 打印标题
    if not args.quiet:
        print("=" * 70)
        print(" " * 15 + "QUBO Prover V3.1 - 神经引导版本")
        print("=" * 70)
        print()
        print(f"公理: {axiom_strs}")
        print(f"目标: {goal_str}")
        print(f"模式: {args.mode}")
        if args.use_neural:
            print(f"神经网络: ✓ 启用")
        print()
    
    # 仅检查蕴涵
    if args.check_entailment:
        axioms = [parse(ax) for ax in axiom_strs]
        goal = parse(goal_str)
        
        if entails(axioms, goal):
            print("✓ 语义蕴涵成立：公理蕴涵目标")
            return 0
        else:
            print("✗ 语义蕴涵不成立：公理不蕴涵目标")
            return 1
    
    # 执行证明
    start_time = time.time()
    
    try:
        if args.mode == 'symbolic':
            success = _prove_symbolic(axiom_strs, goal_str, args)
        elif args.mode == 'hybrid':
            success = _prove_hybrid(axiom_strs, goal_str, args)
        else:
            success = _prove_qubo(axiom_strs, goal_str, args)
    except Exception as e:
        print(f"\n错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 2
    
    elapsed = time.time() - start_time
    
    if not args.quiet:
        print(f"\n耗时: {elapsed:.2f} 秒")
    
    return 0 if success else 1


def _prove_qubo(axiom_strs: List[str], goal_str: str, args) -> bool:
    """QUBO 证明模式"""
    
    if not _check_qubo_available():
        print("错误: QUBO 模块不可用")
        print("请安装依赖: pip install pyqubo dwave-neal")
        return False
    
    QUBOBuilder, _, make_backend, _, decode_result, format_proof_output = _get_qubo_modules()
    
    # 神经网络预测
    rule_weights = None
    if args.use_neural:
        if not _check_neural_available():
            print("警告: 神经网络模块不可用，使用默认权重")
        else:
            RulePredictor = _get_neural_modules()
            predictor = RulePredictor(model_path=args.model_path)
            rule_weights = predictor.predict(axiom_strs, goal_str)
            
            if args.show_weights:
                print(predictor.explain_prediction(axiom_strs, goal_str))
    
    # 构建 QUBO
    builder = QUBOBuilder(
        axiom_penalty=args.axiom_penalty,
        structure_penalty=args.structure_penalty,
        verbose=args.verbose
    )
    
    qubo_problem = builder.build(axiom_strs, goal_str, rule_weights)
    
    if args.verbose:
        print(builder.summary())
    
    if args.show_qubo:
        _display_qubo(qubo_problem.qubo_dict, qubo_problem.offset)
    
    # 采样
    if not args.quiet:
        print(f"\n[采样阶段]")
        print(f"后端: {args.backend}")
        print(f"采样次数: {args.reads}")
    
    backend = make_backend(args.backend)
    sample_result = backend.sample(qubo_problem.bqm, num_reads=args.reads)
    
    # 解码
    decoded = decode_result(sample_result, qubo_problem)
    
    if not args.quiet:
        print(f"\n最低能量: {decoded.energy:.4f}")
        print(format_proof_output(decoded, qubo_problem))
    
    return decoded.proof_valid


def _prove_symbolic(axiom_strs: List[str], goal_str: str, args) -> bool:
    """符号证明模式"""
    
    axioms = [parse(ax) for ax in axiom_strs]
    goal = parse(goal_str)
    
    config = SearchConfig(
        strategy=SearchStrategy.FORWARD,
        max_steps=100,
        use_semantic_check=True
    )
    
    result = prove(axioms, goal, config)
    
    if not args.quiet:
        print(result.format_result())
    
    return result.success


def _prove_hybrid(axiom_strs: List[str], goal_str: str, args) -> bool:
    """混合证明模式：先尝试符号，失败则使用 QUBO"""
    
    if not args.quiet:
        print("[尝试符号证明]")
    
    # 先尝试符号证明
    axioms = [parse(ax) for ax in axiom_strs]
    goal = parse(goal_str)
    
    config = SearchConfig(
        strategy=SearchStrategy.FORWARD,
        max_steps=50  # 限制步数
    )
    
    result = prove(axioms, goal, config)
    
    if result.success:
        if not args.quiet:
            print("✓ 符号证明成功")
            print(result.proof_state.format_proof())
        return True
    
    # 符号证明失败，使用 QUBO
    if not args.quiet:
        print("符号证明未成功，尝试 QUBO 证明...")
    
    return _prove_qubo(axiom_strs, goal_str, args)


def _display_qubo(qubo_dict: dict, offset: float):
    """显示 QUBO 方程"""
    print("\n[QUBO 方程]")
    print("=" * 50)
    print("E(x) = Σ Q_ij * x_i * x_j + offset")
    print()
    
    linear = []
    quadratic = []
    
    for (i, j), coeff in sorted(qubo_dict.items()):
        if i == j:
            linear.append((i, coeff))
        else:
            quadratic.append((i, j, coeff))
    
    if linear:
        print("线性项:")
        for var, coeff in linear[:10]:
            print(f"  {coeff:+.1f} * {var}")
        if len(linear) > 10:
            print(f"  ... 还有 {len(linear) - 10} 个")
    
    if quadratic:
        print("\n二次项:")
        for v1, v2, coeff in quadratic[:10]:
            print(f"  {coeff:+.1f} * {v1} * {v2}")
        if len(quadratic) > 10:
            print(f"  ... 还有 {len(quadratic) - 10} 个")
    
    print(f"\n偏移量: {offset:.1f}")
    print("=" * 50)


if __name__ == "__main__":
    sys.exit(main())

