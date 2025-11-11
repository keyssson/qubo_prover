"""
神经引导的 QUBO 构建器
结合神经网络预测的规则权重来构建 QUBO 问题
"""

from typing import List, Dict, Tuple, Any, Optional
import torch
from ..core.qubo_builder import QUBOBuilder
from .rule_selector import RuleSelectorNetwork
from .feature_encoder import FeatureEncoder


# 规则名称映射：神经网络名称 -> QUBO 规则库名称
RULE_NAME_MAPPING = {
    "modus_ponens": "modus_ponens",
    "modus_tollens": "modus_tollens",
    "and_elimination_left": "and_elim_left",
    "and_elimination_right": "and_elim_right",
    "and_introduction": "and_intro",
    "or_introduction_left": "or_intro",
    "or_introduction_right": "or_intro",  # 规则库只有一个 or_intro
    "double_negation": "double_neg_elim",
}


class NeuralGuidedQUBOBuilder(QUBOBuilder):
    """
    神经引导的 QUBO 构建器
    
    继承自 QUBOBuilder，增加神经网络预测的动态权重功能
    """
    
    def __init__(self,
                 model_path: Optional[str] = None,
                 axiom_penalty: float = 100.0,
                 structure_penalty: float = 10.0,
                 base_rule_penalty: float = 5.0,
                 use_neural_weights: bool = True):
        """
        初始化神经引导构建器
        
        Args:
            model_path: 训练好的模型路径
            axiom_penalty: 公理约束的惩罚系数
            structure_penalty: 结构约束的惩罚系数
            base_rule_penalty: 规则约束的基础惩罚系数
            use_neural_weights: 是否使用神经网络权重
        """
        super().__init__(axiom_penalty, structure_penalty, base_rule_penalty)
        
        self.use_neural_weights = use_neural_weights
        self.base_rule_penalty = base_rule_penalty
        self.rule_weights: Dict[str, float] = {}
        
        # 初始化神经网络组件
        if use_neural_weights:
            self.feature_encoder = FeatureEncoder()
            self.rule_selector = RuleSelectorNetwork()
            
            # 加载训练好的模型
            if model_path:
                self.load_model(model_path)
                print(f"✓ 已加载神经网络模型: {model_path}")
            else:
                print("⚠ 未指定模型路径，将使用未训练的网络")
        else:
            print("ℹ 使用固定权重模式（不使用神经网络）")
    
    def load_model(self, model_path: str):
        """加载训练好的模型"""
        try:
            self.rule_selector.load_state_dict(
                torch.load(model_path, map_location='cpu', weights_only=True)
            )
            self.rule_selector.eval()
            print(f"✓ 模型加载成功")
        except Exception as e:
            print(f"✗ 模型加载失败: {e}")
            raise
    
    def predict_rule_weights(self, axioms: List[str], goal: str) -> Dict[str, float]:
        """
        使用神经网络预测规则权重
        
        Args:
            axioms: 公理列表
            goal: 目标
            
        Returns:
            规则权重字典 {rule_name: weight}
        """
        if not self.use_neural_weights:
            # 返回均匀权重
            return {name: 1.0 for name in RuleSelectorNetwork.RULE_NAMES}
        
        # 1. 编码特征
        features = self.feature_encoder.encode(axioms, goal)
        
        # 2. 预测权重
        weights = self.rule_selector.predict_rule_weights(features)
        
        # 3. 映射到 QUBO 规则库名称
        qubo_weights = {}
        for neural_name, weight in weights.items():
            qubo_name = RULE_NAME_MAPPING.get(neural_name)
            if qubo_name:
                # 如果多个神经网络规则映射到同一个 QUBO 规则，取最大值
                if qubo_name in qubo_weights:
                    qubo_weights[qubo_name] = max(qubo_weights[qubo_name], weight)
                else:
                    qubo_weights[qubo_name] = weight
        
        return qubo_weights
    
    def build(self, axioms: List[str], goal: str) -> Tuple[Any, Dict, float]:
        """
        构建神经引导的 QUBO 问题
        
        Args:
            axioms: 公理字符串列表
            goal: 目标字符串
            
        Returns:
            (PyQUBO Model, 变量映射, offset)
        """
        # 1. 预测规则权重
        print(f"\n[神经网络预测阶段]")
        self.rule_weights = self.predict_rule_weights(axioms, goal)
        
        print(f"预测的规则权重:")
        for rule_name, weight in sorted(self.rule_weights.items(), key=lambda x: -x[1]):
            if weight > 0.5:  # 只显示权重 > 0.5 的规则
                print(f"  {rule_name}: {weight:.4f}")
        
        # 2. 调用父类的 build 方法
        return super().build(axioms, goal)
    
    def get_rule_penalty(self, rule_name: str) -> float:
        """
        获取特定规则的惩罚系数
        
        根据神经网络预测的权重动态调整：
        - 权重高的规则 -> 惩罚系数低 -> 更容易被使用
        - 权重低的规则 -> 惩罚系数高 -> 不太容易被使用
        
        Args:
            rule_name: QUBO 规则库中的规则名称
            
        Returns:
            惩罚系数
        """
        if not self.use_neural_weights or rule_name not in self.rule_weights:
            return self.base_rule_penalty
        
        weight = self.rule_weights[rule_name]
        
        # 转换公式：penalty = base_penalty * (2 - weight)
        # weight = 1.0 -> penalty = base_penalty * 1.0 (最小惩罚)
        # weight = 0.5 -> penalty = base_penalty * 1.5
        # weight = 0.0 -> penalty = base_penalty * 2.0 (最大惩罚)
        penalty = self.base_rule_penalty * (2.0 - weight)
        
        return penalty

