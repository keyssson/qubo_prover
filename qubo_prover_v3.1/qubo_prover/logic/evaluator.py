"""
公式语义求值器

提供对命题逻辑公式的语义求值功能：
- 在给定赋值下求值
- 可满足性判定
- 永真性判定
- 模型查找
"""

from __future__ import annotations
from typing import Dict, Set, Iterator, Tuple, Optional, List
from itertools import product
from .ast import Expr, Var, Not, And, Or, Imply, Iff, get_vars


# 赋值类型：变量名 -> 布尔值
Assignment = Dict[str, bool]


def evaluate(expr: Expr, assignment: Assignment) -> bool:
    """
    在给定赋值下求值公式
    
    Args:
        expr: 逻辑公式
        assignment: 变量赋值，例如 {"P": True, "Q": False}
        
    Returns:
        公式在该赋值下的真值
        
    Raises:
        KeyError: 变量未定义
    """
    if isinstance(expr, Var):
        if expr.name not in assignment:
            raise KeyError(f"Variable '{expr.name}' not in assignment")
        return assignment[expr.name]
    
    if isinstance(expr, Not):
        return not evaluate(expr.operand, assignment)
    
    if isinstance(expr, And):
        return evaluate(expr.left, assignment) and evaluate(expr.right, assignment)
    
    if isinstance(expr, Or):
        return evaluate(expr.left, assignment) or evaluate(expr.right, assignment)
    
    if isinstance(expr, Imply):
        # P -> Q  ≡  ~P | Q
        left_val = evaluate(expr.left, assignment)
        right_val = evaluate(expr.right, assignment)
        return (not left_val) or right_val
    
    if isinstance(expr, Iff):
        # P <-> Q  ≡  (P -> Q) & (Q -> P)
        left_val = evaluate(expr.left, assignment)
        right_val = evaluate(expr.right, assignment)
        return left_val == right_val
    
    raise ValueError(f"Unknown expression type: {type(expr)}")


def evaluate_safe(expr: Expr, assignment: Assignment, default: bool = False) -> bool:
    """
    安全求值（未定义变量使用默认值）
    
    Args:
        expr: 逻辑公式
        assignment: 变量赋值
        default: 未定义变量的默认值
        
    Returns:
        公式的真值
    """
    vars_in_expr = get_vars(expr)
    full_assignment = {v: assignment.get(v, default) for v in vars_in_expr}
    return evaluate(expr, full_assignment)


def all_assignments(variables: Set[str]) -> Iterator[Assignment]:
    """
    生成所有可能的赋值
    
    Args:
        variables: 变量集合
        
    Yields:
        所有可能的赋值字典
    """
    var_list = sorted(variables)
    for values in product([False, True], repeat=len(var_list)):
        yield dict(zip(var_list, values))


def is_tautology(expr: Expr) -> bool:
    """
    判断公式是否为永真式（重言式）
    
    Args:
        expr: 逻辑公式
        
    Returns:
        是否在所有赋值下都为真
    """
    variables = get_vars(expr)
    for assignment in all_assignments(variables):
        if not evaluate(expr, assignment):
            return False
    return True


def is_contradiction(expr: Expr) -> bool:
    """
    判断公式是否为矛盾式
    
    Args:
        expr: 逻辑公式
        
    Returns:
        是否在所有赋值下都为假
    """
    variables = get_vars(expr)
    for assignment in all_assignments(variables):
        if evaluate(expr, assignment):
            return False
    return True


def is_satisfiable(expr: Expr) -> bool:
    """
    判断公式是否可满足
    
    Args:
        expr: 逻辑公式
        
    Returns:
        是否存在使公式为真的赋值
    """
    variables = get_vars(expr)
    for assignment in all_assignments(variables):
        if evaluate(expr, assignment):
            return True
    return False


def find_model(expr: Expr) -> Optional[Assignment]:
    """
    查找使公式为真的模型（赋值）
    
    Args:
        expr: 逻辑公式
        
    Returns:
        满足公式的赋值，或 None（如果不可满足）
    """
    variables = get_vars(expr)
    for assignment in all_assignments(variables):
        if evaluate(expr, assignment):
            return assignment
    return None


def find_all_models(expr: Expr) -> List[Assignment]:
    """
    查找所有使公式为真的模型
    
    Args:
        expr: 逻辑公式
        
    Returns:
        所有满足公式的赋值列表
    """
    variables = get_vars(expr)
    return [
        assignment for assignment in all_assignments(variables)
        if evaluate(expr, assignment)
    ]


def find_countermodel(expr: Expr) -> Optional[Assignment]:
    """
    查找反例（使公式为假的赋值）
    
    Args:
        expr: 逻辑公式
        
    Returns:
        使公式为假的赋值，或 None（如果是永真式）
    """
    variables = get_vars(expr)
    for assignment in all_assignments(variables):
        if not evaluate(expr, assignment):
            return assignment
    return None


def is_equivalent(expr1: Expr, expr2: Expr) -> bool:
    """
    判断两个公式是否逻辑等价
    
    Args:
        expr1: 第一个公式
        expr2: 第二个公式
        
    Returns:
        是否在所有赋值下真值相同
    """
    variables = get_vars(expr1) | get_vars(expr2)
    for assignment in all_assignments(variables):
        v1 = evaluate_safe(expr1, assignment)
        v2 = evaluate_safe(expr2, assignment)
        if v1 != v2:
            return False
    return True


def entails(premises: List[Expr], conclusion: Expr) -> bool:
    """
    判断前提是否蕴涵结论（语义蕴涵）
    
    Args:
        premises: 前提列表
        conclusion: 结论
        
    Returns:
        是否所有使前提全为真的赋值都使结论为真
    """
    if not premises:
        return is_tautology(conclusion)
    
    # 收集所有变量
    variables: Set[str] = set()
    for p in premises:
        variables |= get_vars(p)
    variables |= get_vars(conclusion)
    
    # 检查所有赋值
    for assignment in all_assignments(variables):
        # 如果所有前提都为真
        if all(evaluate_safe(p, assignment) for p in premises):
            # 结论也必须为真
            if not evaluate_safe(conclusion, assignment):
                return False
    
    return True


def find_entailment_countermodel(premises: List[Expr], conclusion: Expr) -> Optional[Assignment]:
    """
    查找蕴涵关系的反例
    
    Args:
        premises: 前提列表
        conclusion: 结论
        
    Returns:
        使前提为真但结论为假的赋值，或 None
    """
    if not premises:
        return find_countermodel(conclusion)
    
    variables: Set[str] = set()
    for p in premises:
        variables |= get_vars(p)
    variables |= get_vars(conclusion)
    
    for assignment in all_assignments(variables):
        if all(evaluate_safe(p, assignment) for p in premises):
            if not evaluate_safe(conclusion, assignment):
                return assignment
    
    return None


def truth_table(expr: Expr) -> List[Tuple[Assignment, bool]]:
    """
    生成真值表
    
    Args:
        expr: 逻辑公式
        
    Returns:
        [(赋值, 真值), ...] 列表
    """
    variables = get_vars(expr)
    return [
        (assignment, evaluate(expr, assignment))
        for assignment in all_assignments(variables)
    ]


def format_truth_table(expr: Expr) -> str:
    """
    格式化输出真值表
    
    Args:
        expr: 逻辑公式
        
    Returns:
        格式化的真值表字符串
    """
    variables = sorted(get_vars(expr))
    table = truth_table(expr)
    
    # 表头
    header = " | ".join(variables) + " | " + str(expr)
    separator = "-" * len(header)
    
    lines = [header, separator]
    
    for assignment, value in table:
        row_values = [str(int(assignment[v])) for v in variables]
        row_values.append(str(int(value)))
        lines.append(" | ".join(row_values))
    
    return "\n".join(lines)

