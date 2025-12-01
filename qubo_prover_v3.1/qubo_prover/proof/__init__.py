"""
证明系统层

提供完整的命题逻辑证明系统：
- 推理规则库（自然演绎规则）
- 证明状态管理
- 相继式表示
- 证明搜索策略
"""

from .rules import (
    Rule, RuleResult,
    ModusPonens, ModusTollens,
    AndIntro, AndElimLeft, AndElimRight,
    OrIntroLeft, OrIntroRight, OrElim,
    NotIntro, NotElim, DoubleNegElim,
    ImplyIntro, ImplyElim,
    Resolution,
    RULE_REGISTRY, get_rule, list_rules, apply_all_rules
)
from .proof_state import ProofState, ProofStep, ProofStatus
from .sequent import Sequent
from .search import ProofSearcher, SearchConfig, SearchResult

__all__ = [
    # Rules
    "Rule", "RuleResult",
    "ModusPonens", "ModusTollens",
    "AndIntro", "AndElimLeft", "AndElimRight",
    "OrIntroLeft", "OrIntroRight", "OrElim",
    "NotIntro", "NotElim", "DoubleNegElim",
    "ImplyIntro", "ImplyElim",
    "Resolution",
    "RULE_REGISTRY", "get_rule", "list_rules", "apply_all_rules",
    # Proof state
    "ProofState", "ProofStep", "ProofStatus",
    # Sequent
    "Sequent",
    # Search
    "ProofSearcher", "SearchConfig", "SearchResult",
]

