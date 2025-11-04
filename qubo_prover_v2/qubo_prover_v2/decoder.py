"""
结果解码器
将采样结果解码为逻辑赋值并验证证明
"""

from typing import Any, Dict, List, Tuple


def decode_sampleset(sampleset: Any) -> List[Tuple[Dict[str, int], float]]:
    """
    解码 dimod SampleSet
    
    Args:
        sampleset: dimod 采样结果
        
    Returns:
        [(变量赋值字典, 能量值), ...]
    """
    rows: List[Tuple[Dict[str, int], float]] = []
    
    for sample, energy in zip(sampleset.record.sample, sampleset.record.energy):
        assignment = {
            v: int(sample[idx]) 
            for idx, v in enumerate(sampleset.variables)
        }
        rows.append((assignment, float(energy)))
    
    return rows


def decode_openjij_response(resp: Any) -> List[Tuple[Dict[str, int], float]]:
    """
    解码 OpenJij Response
    
    Args:
        resp: OpenJij 采样结果
        
    Returns:
        [(变量赋值字典, 能量值), ...]
    """
    rows: List[Tuple[Dict[str, int], float]] = []
    
    states = getattr(resp, "states", None)
    energies = getattr(resp, "energies", None)
    
    if states is None or energies is None:
        raise ValueError("Unexpected OpenJij response format")
    
    for st, en in zip(states, energies):
        if isinstance(st, dict):
            assignment = {str(k): int(v) for k, v in st.items()}
            rows.append((assignment, float(en)))
    
    return rows


def best_by_lowest_energy(rows: List[Tuple[Dict[str, int], float]]) -> Tuple[Dict[str, int], float]:
    """
    选择能量最低的解
    
    Args:
        rows: 解列表
        
    Returns:
        (最佳赋值, 最低能量)
    """
    if not rows:
        raise ValueError("No solutions found")
    
    return min(rows, key=lambda t: t[1])


def verify_assignment(assignment: Dict[str, int], 
                     axiom_vars: List[str],
                     goal_var: str) -> Tuple[bool, str]:
    """
    验证赋值是否满足证明要求
    
    Args:
        assignment: 变量赋值
        axiom_vars: 公理变量名列表
        goal_var: 目标变量名
        
    Returns:
        (是否成功, 消息)
    """
    # 检查所有公理是否为真
    for ax_var in axiom_vars:
        if assignment.get(ax_var, 0) != 1:
            return False, f"公理 {ax_var} 未满足（值为 {assignment.get(ax_var, 0)}）"
    
    # 检查目标是否为真
    if assignment.get(goal_var, 0) != 1:
        return False, f"目标 {goal_var} 未满足（值为 {assignment.get(goal_var, 0)}）"
    
    return True, "所有约束满足"


def extract_proof_path(assignment: Dict[str, int], 
                       var_info: Dict[str, Any]) -> List[str]:
    """
    从赋值中提取证明路径
    
    Args:
        assignment: 变量赋值
        var_info: 变量信息（来自 QUBOBuilder）
        
    Returns:
        证明步骤列表
    """
    steps = []
    
    # 添加公理
    axiom_vars = var_info.get("axiom_vars", [])
    formula_map = var_info.get("formula_map", {})
    
    for ax_var in axiom_vars:
        if assignment.get(ax_var, 0) == 1:
            formula = formula_map.get(ax_var, ax_var)
            steps.append(f"公理: {formula}")
    
    # 查找激活的规则
    for var_name, value in assignment.items():
        if var_name.startswith("Rule_") and value == 1:
            steps.append(f"应用规则: {var_name}")
    
    # 添加目标
    goal_var = var_info.get("goal_var")
    if goal_var and assignment.get(goal_var, 0) == 1:
        formula = formula_map.get(goal_var, goal_var)
        steps.append(f"结论: {formula} ✓")
    
    return steps


def format_assignment(assignment: Dict[str, int], 
                     show_zeros: bool = False) -> str:
    """
    格式化赋值输出
    
    Args:
        assignment: 变量赋值
        show_zeros: 是否显示值为 0 的变量
        
    Returns:
        格式化字符串
    """
    lines = []
    
    # 按变量名排序
    sorted_vars = sorted(assignment.items())
    
    for var_name, value in sorted_vars:
        if value == 1 or show_zeros:
            lines.append(f"  {var_name} = {value}")
    
    return "\n".join(lines)

