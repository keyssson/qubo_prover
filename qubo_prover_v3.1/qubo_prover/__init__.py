"""
QUBO Prover V3.1 - 神经引导的命题逻辑自动定理证明器

核心改进：
- 完整的推理规则库（自然演绎 + 归结消解）
- 改进的 QUBO 编码策略（证明步骤编码）
- 神经网络引导的规则选择
- 可靠性与完备性保证
"""

__version__ = "3.1.0"
__author__ = "QUBO Prover Team"

from .logic.ast import Var, Not, And, Or, Imply, Iff, Expr
from .logic.parser import parse

__all__ = [
    "Var", "Not", "And", "Or", "Imply", "Iff", "Expr",
    "parse",
]

