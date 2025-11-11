"""
训练数据生成器 - 自动生成逻辑证明问题和标签

功能：
1. 随机生成逻辑公式（公理和目标）
2. 使用 V2 的 QUBO 系统求解
3. 记录哪些规则被使用（作为训练标签）
4. 保存为训练数据
"""

import random
import json
import os
from typing import List, Tuple, Dict

# tqdm 是可选依赖
try:
    from tqdm import tqdm
except ImportError:
    # 如果没有 tqdm，使用简单的进度显示
    def tqdm(iterable, desc="", **kwargs):
        print(f"{desc}...")
        return iterable


class TrainingDataGenerator:
    """训练数据生成器"""
    
    # 可用的变量
    VARIABLES = ["P", "Q", "R", "S", "T"]
    
    # 逻辑运算符
    OPERATORS = ["->", "&", "|", "~"]
    
    def __init__(self, seed=42):
        """
        初始化生成器
        
        Args:
            seed: 随机种子
        """
        random.seed(seed)
        self.templates = self._create_templates()
    
    def _create_templates(self) -> List[Dict]:
        """
        创建问题模板
        
        Returns:
            模板列表，每个模板包含公理和目标的生成规则
        """
        templates = [
            # Modus Ponens: P, P->Q ⊢ Q
            {
                "name": "modus_ponens",
                "axioms": ["{A}", "{A}->{B}"],
                "goal": "{B}",
                "useful_rules": ["modus_ponens"],
            },
            # Modus Tollens: P->Q, ~Q ⊢ ~P
            {
                "name": "modus_tollens",
                "axioms": ["{A}->{B}", "~{B}"],
                "goal": "~{A}",
                "useful_rules": ["modus_tollens"],
            },
            # Syllogism: P->Q, Q->R ⊢ P->R
            {
                "name": "syllogism",
                "axioms": ["{A}->{B}", "{B}->{C}"],
                "goal": "{A}->{C}",
                "useful_rules": ["modus_ponens"],
            },
            # And Elimination: P&Q ⊢ P
            {
                "name": "and_elimination_left",
                "axioms": ["{A}&{B}"],
                "goal": "{A}",
                "useful_rules": ["and_elimination_left"],
            },
            # And Elimination: P&Q ⊢ Q
            {
                "name": "and_elimination_right",
                "axioms": ["{A}&{B}"],
                "goal": "{B}",
                "useful_rules": ["and_elimination_right"],
            },
            # And Introduction: P, Q ⊢ P&Q
            {
                "name": "and_introduction",
                "axioms": ["{A}", "{B}"],
                "goal": "{A}&{B}",
                "useful_rules": ["and_introduction"],
            },
            # Double Negation: ~~P ⊢ P
            {
                "name": "double_negation",
                "axioms": ["~~{A}"],
                "goal": "{A}",
                "useful_rules": ["double_negation"],
            },
            # Complex: P, P->Q, Q->R ⊢ R
            {
                "name": "complex_chain",
                "axioms": ["{A}", "{A}->{B}", "{B}->{C}"],
                "goal": "{C}",
                "useful_rules": ["modus_ponens"],
            },
        ]
        
        return templates
    
    def generate_problem(self) -> Dict:
        """
        生成一个随机问题
        
        Returns:
            问题字典，包含 axioms, goal, useful_rules, template_name
        """
        # 随机选择一个模板
        template = random.choice(self.templates)
        
        # 随机选择变量
        num_vars_needed = self._count_unique_vars(template)
        selected_vars = random.sample(self.VARIABLES, num_vars_needed)
        
        # 创建变量映射
        var_mapping = {}
        var_placeholders = sorted(set(
            placeholder
            for axiom in template["axioms"] + [template["goal"]]
            for placeholder in self._extract_placeholders(axiom)
        ))
        
        for i, placeholder in enumerate(var_placeholders):
            var_mapping[placeholder] = selected_vars[i]
        
        # 替换变量
        axioms = [
            self._replace_placeholders(axiom, var_mapping)
            for axiom in template["axioms"]
        ]
        goal = self._replace_placeholders(template["goal"], var_mapping)
        
        return {
            "axioms": axioms,
            "goal": goal,
            "useful_rules": template["useful_rules"],
            "template_name": template["name"],
        }
    
    def _count_unique_vars(self, template: Dict) -> int:
        """计算模板需要的唯一变量数"""
        placeholders = set()
        for axiom in template["axioms"] + [template["goal"]]:
            placeholders.update(self._extract_placeholders(axiom))
        return len(placeholders)
    
    def _extract_placeholders(self, formula: str) -> List[str]:
        """提取公式中的占位符，例如 {A}, {B}"""
        import re
        return re.findall(r'\{([A-Z])\}', formula)
    
    def _replace_placeholders(self, formula: str, mapping: Dict[str, str]) -> str:
        """替换占位符为实际变量"""
        result = formula
        for placeholder, var in mapping.items():
            result = result.replace(f"{{{placeholder}}}", var)
        return result
    
    def generate_dataset(self, num_samples: int) -> List[Dict]:
        """
        生成数据集
        
        Args:
            num_samples: 样本数量
        
        Returns:
            数据集列表
        """
        dataset = []
        
        print(f"生成 {num_samples} 个训练样本...")
        for _ in tqdm(range(num_samples)):
            problem = self.generate_problem()
            dataset.append(problem)
        
        return dataset
    
    def save_dataset(self, dataset: List[Dict], output_path: str):
        """
        保存数据集到文件
        
        Args:
            dataset: 数据集
            output_path: 输出文件路径
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"数据集已保存到: {output_path}")
        print(f"样本数量: {len(dataset)}")


# 示例用法
if __name__ == "__main__":
    generator = TrainingDataGenerator()
    
    # 生成几个示例
    print("生成示例问题：")
    print("=" * 60)
    for i in range(5):
        problem = generator.generate_problem()
        print(f"\n问题 {i+1} ({problem['template_name']}):")
        print(f"  公理: {problem['axioms']}")
        print(f"  目标: {problem['goal']}")
        print(f"  有用的规则: {problem['useful_rules']}")

