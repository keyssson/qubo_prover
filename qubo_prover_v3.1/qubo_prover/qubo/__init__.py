"""
QUBO 编码层

将证明问题编码为 QUBO（Quadratic Unconstrained Binary Optimization）问题。

核心组件：
- encoder: 公式编码器
- proof_encoder: 证明步骤编码
- builder: QUBO 构建器
- constraints: 约束生成器
"""

from .encoder import FormulaEncoder, encode_formula
from .proof_encoder import ProofStepEncoder, ProofQUBO
from .builder import QUBOBuilder, build_qubo
from .constraints import (
    ConstraintBuilder,
    add_axiom_constraint,
    add_goal_constraint,
    add_structure_constraint,
    add_rule_constraint
)

__all__ = [
    # Encoder
    "FormulaEncoder", "encode_formula",
    # Proof Encoder
    "ProofStepEncoder", "ProofQUBO",
    # Builder
    "QUBOBuilder", "build_qubo",
    # Constraints
    "ConstraintBuilder",
    "add_axiom_constraint",
    "add_goal_constraint",
    "add_structure_constraint",
    "add_rule_constraint",
]

