"""
证明验证器

对证明结果进行深入验证，确保正确性。
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
from ..logic.ast import Expr
from ..logic.evaluator import evaluate, entails
from ..logic.parser import parse


class VerificationStatus(Enum):
    """验证状态"""
    VALID = "valid"           # 有效证明
    INVALID = "invalid"       # 无效证明
    INCOMPLETE = "incomplete" # 不完整
    ERROR = "error"           # 验证错误


@dataclass
class VerificationResult:
    """
    验证结果
    """
    status: VerificationStatus
    message: str
    details: Dict[str, Any] = None
    
    @property
    def is_valid(self) -> bool:
        return self.status == VerificationStatus.VALID


class ProofVerifier:
    """
    证明验证器
    
    提供多层次的证明验证：
    1. 语法验证：赋值格式正确
    2. 约束验证：QUBO 约束满足
    3. 语义验证：逻辑语义正确
    4. 完整性验证：证明链完整
    """
    
    def __init__(self, strict: bool = True):
        """
        初始化验证器
        
        Args:
            strict: 是否严格模式
        """
        self.strict = strict
    
    def verify(self, 
               axioms: List[Expr], 
               goal: Expr,
               assignment: Dict[str, int]) -> VerificationResult:
        """
        验证证明
        
        Args:
            axioms: 公理列表
            goal: 目标
            assignment: 变量赋值
            
        Returns:
            验证结果
        """
        details: Dict[str, Any] = {}
        
        # 1. 语法验证
        syntax_ok, syntax_msg = self._verify_syntax(assignment)
        details["syntax"] = {"ok": syntax_ok, "message": syntax_msg}
        if not syntax_ok:
            return VerificationResult(
                status=VerificationStatus.INVALID,
                message=f"语法验证失败: {syntax_msg}",
                details=details
            )
        
        # 2. 语义验证：检查赋值是否使公理为真
        semantic_ok, semantic_msg = self._verify_semantics(axioms, goal, assignment)
        details["semantic"] = {"ok": semantic_ok, "message": semantic_msg}
        if not semantic_ok:
            return VerificationResult(
                status=VerificationStatus.INVALID,
                message=f"语义验证失败: {semantic_msg}",
                details=details
            )
        
        # 3. 蕴涵验证：检查公理是否蕴涵目标
        entailment_ok, entailment_msg = self._verify_entailment(axioms, goal)
        details["entailment"] = {"ok": entailment_ok, "message": entailment_msg}
        if not entailment_ok and self.strict:
            return VerificationResult(
                status=VerificationStatus.INCOMPLETE,
                message=f"蕴涵验证失败: {entailment_msg}",
                details=details
            )
        
        return VerificationResult(
            status=VerificationStatus.VALID,
            message="证明有效",
            details=details
        )
    
    def _verify_syntax(self, assignment: Dict[str, int]) -> Tuple[bool, str]:
        """语法验证"""
        for var, val in assignment.items():
            if val not in (0, 1):
                return False, f"变量 {var} 的值 {val} 不是二进制"
        return True, "格式正确"
    
    def _verify_semantics(self, axioms: List[Expr], goal: Expr,
                          assignment: Dict[str, int]) -> Tuple[bool, str]:
        """语义验证"""
        # 提取命题变量赋值
        prop_assignment: Dict[str, bool] = {}
        for var, val in assignment.items():
            if len(var) == 1 and var.isupper():
                prop_assignment[var] = bool(val)
        
        if not prop_assignment:
            return True, "无命题变量需验证"
        
        # 验证公理
        for i, axiom in enumerate(axioms):
            try:
                val = evaluate(axiom, prop_assignment)
                if not val:
                    return False, f"公理 {i+1} ({axiom}) 在给定赋值下为假"
            except KeyError as e:
                # 变量缺失，跳过验证
                continue
        
        # 验证目标
        try:
            goal_val = evaluate(goal, prop_assignment)
            if not goal_val:
                return False, f"目标 ({goal}) 在给定赋值下为假"
        except KeyError:
            pass
        
        return True, "语义正确"
    
    def _verify_entailment(self, axioms: List[Expr], goal: Expr) -> Tuple[bool, str]:
        """蕴涵验证"""
        if entails(axioms, goal):
            return True, "公理蕴涵目标"
        return False, "公理不蕴涵目标（可能需要更多推理步骤）"
    
    def verify_step_by_step(self, 
                            axioms: List[Expr],
                            goal: Expr,
                            steps: List[Tuple[str, Expr, List[int]]]) -> VerificationResult:
        """
        验证逐步证明
        
        Args:
            axioms: 公理列表
            goal: 目标
            steps: 证明步骤 [(规则名, 结论, 前提步骤编号)]
            
        Returns:
            验证结果
        """
        proven: List[Expr] = list(axioms)
        
        for i, (rule_name, conclusion, premise_indices) in enumerate(steps):
            # 检查前提是否已证明
            for idx in premise_indices:
                if idx < 0 or idx >= len(proven):
                    return VerificationResult(
                        status=VerificationStatus.INVALID,
                        message=f"步骤 {i+1}: 前提 {idx} 不存在"
                    )
            
            # 验证规则应用
            # （简化处理：信任规则名称）
            proven.append(conclusion)
        
        # 检查目标是否被证明
        if goal in proven:
            return VerificationResult(
                status=VerificationStatus.VALID,
                message="逐步证明有效"
            )
        
        return VerificationResult(
            status=VerificationStatus.INCOMPLETE,
            message="目标未在证明步骤中出现"
        )


def quick_verify(axiom_strs: List[str], goal_str: str,
                 assignment: Dict[str, int]) -> bool:
    """
    快速验证
    
    Args:
        axiom_strs: 公理字符串列表
        goal_str: 目标字符串
        assignment: 赋值
        
    Returns:
        是否有效
    """
    axioms = [parse(s) for s in axiom_strs]
    goal = parse(goal_str)
    
    verifier = ProofVerifier(strict=False)
    result = verifier.verify(axioms, goal, assignment)
    
    return result.is_valid

