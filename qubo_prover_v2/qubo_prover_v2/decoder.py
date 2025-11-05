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
    从赋值中提取详细的证明路径

    Args:
        assignment: 变量赋值
        var_info: 变量信息（来自 QUBOBuilder）

    Returns:
        证明步骤列表
    """
    steps = []

    # 获取信息
    axiom_vars = var_info.get("axiom_vars", [])
    formula_map = var_info.get("formula_map", {})
    axiom_formulas = var_info.get("axiom_formulas", [])
    goal_formula = var_info.get("goal_formula", "")

    # 步骤 1: 显示公理
    steps.append("【步骤 1】公理（已知为真）:")
    for i, ax_var in enumerate(axiom_vars):
        formula = formula_map.get(ax_var, ax_var)
        if assignment.get(ax_var, 0) == 1:
            steps.append(f"  ✓ 公理 {i+1}: {formula}")
        else:
            steps.append(f"  ✗ 公理 {i+1}: {formula} [警告: 未满足]")
    steps.append("")

    # 步骤 2: 显示命题变量赋值
    steps.append("【步骤 2】命题变量赋值:")
    prop_vars = {}
    for var_name, val in sorted(assignment.items()):
        # 只显示单字母命题变量
        if len(var_name) == 1 and var_name.isupper():
            prop_vars[var_name] = val
            truth_str = "真(True)" if val == 1 else "假(False)"
            steps.append(f"  {var_name} = {truth_str}")
    steps.append("")

    # 步骤 3: 推理过程
    steps.append("【步骤 3】推理过程:")

    # 分析推理逻辑
    inference_steps = _analyze_inference_logic(axiom_formulas, goal_formula, prop_vars, assignment)
    for step in inference_steps:
        steps.append(f"  {step}")
    steps.append("")

    # 步骤 4: 结论
    steps.append("【步骤 4】结论:")
    goal_var = var_info.get("goal_var")
    if goal_var and assignment.get(goal_var, 0) == 1:
        steps.append(f"  ✓ 目标 {goal_formula} 得证")
        steps.append(f"  证明完成！")
    else:
        steps.append(f"  ✗ 目标 {goal_formula} 未得证")
        steps.append(f"  证明失败！")

    return steps


def _analyze_inference_logic(axiom_formulas: List[str], goal_formula: str,
                             prop_vars: Dict[str, int], assignment: Dict[str, int]) -> List[str]:
    """
    分析推理逻辑，生成详细的推理步骤

    Args:
        axiom_formulas: 公理公式字符串列表
        goal_formula: 目标公式字符串
        prop_vars: 命题变量赋值
        assignment: 完整赋值

    Returns:
        推理步骤列表
    """
    steps = []

    # 检测 Modus Ponens: P, P->Q ⊢ Q
    for i, ax1 in enumerate(axiom_formulas):
        # 检查是否是单个命题变量
        if ax1 in prop_vars and prop_vars[ax1] == 1:
            for j, ax2 in enumerate(axiom_formulas):
                # 检查是否是蕴涵式 P->Q
                if "->" in ax2:
                    parts = ax2.split("->")
                    if len(parts) == 2:
                        left = parts[0].strip().strip("()")
                        right = parts[1].strip().strip("()")
                        if left == ax1:
                            steps.append(f"由公理 {i+1} ({ax1}=真) 和公理 {j+1} ({ax1}→{right})，")
                            steps.append(f"  根据 Modus Ponens 规则，得 {right}=真")

    # 检测 Modus Tollens: P->Q, ~Q ⊢ ~P
    for i, ax1 in enumerate(axiom_formulas):
        if "->" in ax1:
            parts = ax1.split("->")
            if len(parts) == 2:
                left = parts[0].strip().strip("()")
                right = parts[1].strip().strip("()")

                for j, ax2 in enumerate(axiom_formulas):
                    # 检查是否是 ~Q
                    if ax2.startswith("~"):
                        negated = ax2[1:].strip().strip("()")
                        if negated == right:
                            steps.append(f"由公理 {i+1} ({left}→{right}) 和公理 {j+1} (~{right}=真)，")
                            steps.append(f"  根据 Modus Tollens 规则（反证法）：")
                            steps.append(f"    假设 {left}=真，则由 {left}→{right} 得 {right}=真")
                            steps.append(f"    但 ~{right}=真，即 {right}=假，矛盾！")
                            steps.append(f"    因此 {left}=假，即 ~{left}=真")

    # 检测 And-Elimination: P&Q ⊢ P 或 P&Q ⊢ Q
    for i, ax in enumerate(axiom_formulas):
        if "&" in ax:
            parts = ax.split("&")
            if len(parts) == 2:
                left = parts[0].strip().strip("()")
                right = parts[1].strip().strip("()")
                steps.append(f"由公理 {i+1} ({left}∧{right}=真)，")
                steps.append(f"  根据合取消除规则，得 {left}=真 且 {right}=真")

    # 检查是否使用了推理规则变量
    rule_vars = [k for k in assignment.keys() if k.startswith("Rule_")]
    if rule_vars:
        for rule_var in rule_vars:
            if assignment.get(rule_var, 0) == 1:
                rule_name = rule_var.replace("Rule_", "").replace("_", " → ")
                steps.append(f"（系统激活了推理规则变量: {rule_name}）")

    if not steps:
        steps.append("（直接由公理和命题变量赋值得出结论）")

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

