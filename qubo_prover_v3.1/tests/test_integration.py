"""
集成测试 - 端到端证明测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qubo_prover.logic.parser import parse
from qubo_prover.logic.evaluator import entails
from qubo_prover.proof.search import prove
from qubo_prover.qubo.builder import build_qubo


class TestEndToEndProofs:
    """端到端证明测试"""
    
    def test_trivial_proof(self):
        """测试简单证明：P ⊢ P"""
        axioms = [parse("P")]
        goal = parse("P")
        
        # 语义检查
        assert entails(axioms, goal)
        
        # 符号证明
        result = prove(axioms, goal)
        assert result.success
    
    def test_modus_ponens(self):
        """测试 Modus Ponens: P, P→Q ⊢ Q"""
        axioms = [parse("P"), parse("P -> Q")]
        goal = parse("Q")
        
        assert entails(axioms, goal)
        
        result = prove(axioms, goal)
        assert result.success
    
    def test_modus_tollens(self):
        """测试 Modus Tollens: P→Q, ~Q ⊢ ~P"""
        axioms = [parse("P -> Q"), parse("~Q")]
        goal = parse("~P")
        
        assert entails(axioms, goal)
        
        result = prove(axioms, goal)
        assert result.success
    
    def test_syllogism(self):
        """测试三段论: P, P→Q, Q→R ⊢ R"""
        axioms = [
            parse("P"),
            parse("P -> Q"),
            parse("Q -> R")
        ]
        goal = parse("R")
        
        assert entails(axioms, goal)
        
        result = prove(axioms, goal)
        assert result.success
    
    def test_and_elimination(self):
        """测试合取消除: P∧Q ⊢ P"""
        axioms = [parse("P & Q")]
        goal = parse("P")
        
        assert entails(axioms, goal)
        
        result = prove(axioms, goal)
        assert result.success
    
    def test_double_negation(self):
        """测试双重否定: ~~P ⊢ P"""
        axioms = [parse("~~P")]
        goal = parse("P")
        
        assert entails(axioms, goal)
        
        result = prove(axioms, goal)
        assert result.success
    
    def test_invalid_inference(self):
        """测试无效推理: P ⊬ Q"""
        axioms = [parse("P")]
        goal = parse("Q")
        
        # 语义上不蕴涵
        assert not entails(axioms, goal)
        
        # 证明应该失败
        result = prove(axioms, goal)
        assert not result.success


class TestQUBOIntegration:
    """QUBO 集成测试"""
    
    def test_qubo_build_and_solve_concept(self):
        """测试 QUBO 构建（概念验证）"""
        # 构建 QUBO
        problem = build_qubo(["P", "P -> Q"], "Q", verbose=False)
        
        # 验证 QUBO 结构
        assert problem.model is not None
        assert len(problem.qubo_dict) > 0
        assert len(problem.axiom_vars) == 2
        assert problem.goal_var is not None
        
        # 检查变量映射
        var_names = list(problem.var_map.keys())
        assert "P" in var_names
        assert "Q" in var_names
    
    def test_qubo_different_problems(self):
        """测试不同问题的 QUBO 构建"""
        problems = [
            (["P"], "P"),
            (["P", "P -> Q"], "Q"),
            (["P -> Q", "~Q"], "~P"),
            (["P & Q"], "P"),
        ]
        
        for axioms, goal in problems:
            problem = build_qubo(axioms, goal, verbose=False)
            assert problem.model is not None
            assert problem.bqm is not None


class TestComplexProofs:
    """复杂证明测试"""
    
    def test_longer_chain(self):
        """测试更长的推理链"""
        axioms = [
            parse("A"),
            parse("A -> B"),
            parse("B -> C"),
            parse("C -> D"),
        ]
        goal = parse("D")
        
        assert entails(axioms, goal)
    
    def test_multiple_premises(self):
        """测试多前提"""
        axioms = [
            parse("P"),
            parse("Q"),
            parse("(P & Q) -> R"),
        ]
        goal = parse("R")
        
        # 需要先合取引入得到 P&Q，再 MP 得到 R
        assert entails(axioms, goal)
    
    def test_de_morgan(self):
        """测试德摩根定律相关"""
        # ~(P & Q) -> (~P | ~Q) 是永真的
        # 但作为推理需要更多规则
        axioms = [parse("~(P & Q)")]
        goal = parse("~P | ~Q")
        
        # 这是有效的，但需要德摩根定律
        assert entails(axioms, goal)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

