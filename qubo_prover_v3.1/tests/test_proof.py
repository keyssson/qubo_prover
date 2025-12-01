"""
证明系统测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qubo_prover.logic.parser import parse
from qubo_prover.logic.evaluator import entails
from qubo_prover.proof.rules import (
    ModusPonens, ModusTollens, AndIntro, AndElimLeft, AndElimRight,
    OrIntroLeft, OrElim, DoubleNegElim, apply_all_rules
)
from qubo_prover.proof.search import prove, SearchConfig, SearchStrategy


class TestRules:
    """推理规则测试"""
    
    def test_modus_ponens(self):
        """测试 Modus Ponens"""
        p = parse("P")
        p_implies_q = parse("P -> Q")
        q = parse("Q")
        
        kb = {p, p_implies_q}
        mp = ModusPonens()
        
        results = list(mp.apply(kb, q))
        assert len(results) > 0
        assert results[0].conclusion == q
    
    def test_modus_tollens(self):
        """测试 Modus Tollens"""
        p_implies_q = parse("P -> Q")
        not_q = parse("~Q")
        not_p = parse("~P")
        
        kb = {p_implies_q, not_q}
        mt = ModusTollens()
        
        results = list(mt.apply(kb, not_p))
        assert len(results) > 0
        assert results[0].conclusion == not_p
    
    def test_and_intro(self):
        """测试合取引入"""
        p = parse("P")
        q = parse("Q")
        p_and_q = parse("P & Q")
        
        kb = {p, q}
        rule = AndIntro()
        
        results = list(rule.apply(kb, p_and_q))
        assert len(results) > 0
    
    def test_and_elim(self):
        """测试合取消除"""
        p_and_q = parse("P & Q")
        p = parse("P")
        q = parse("Q")
        
        kb = {p_and_q}
        
        left_rule = AndElimLeft()
        right_rule = AndElimRight()
        
        left_results = list(left_rule.apply(kb, p))
        right_results = list(right_rule.apply(kb, q))
        
        assert len(left_results) > 0
        assert left_results[0].conclusion == p
        assert len(right_results) > 0
        assert right_results[0].conclusion == q
    
    def test_double_neg_elim(self):
        """测试双重否定消除"""
        not_not_p = parse("~~P")
        p = parse("P")
        
        kb = {not_not_p}
        rule = DoubleNegElim()
        
        results = list(rule.apply(kb, p))
        assert len(results) > 0
        assert results[0].conclusion == p


class TestProofSearch:
    """证明搜索测试"""
    
    def test_trivial_proof(self):
        """测试简单证明（目标在公理中）"""
        axioms = [parse("P")]
        goal = parse("P")
        
        result = prove(axioms, goal)
        assert result.success
    
    def test_modus_ponens_proof(self):
        """测试 Modus Ponens 证明"""
        axioms = [parse("P"), parse("P -> Q")]
        goal = parse("Q")
        
        result = prove(axioms, goal)
        assert result.success
    
    def test_chain_proof(self):
        """测试推理链证明"""
        axioms = [
            parse("P"),
            parse("P -> Q"),
            parse("Q -> R")
        ]
        goal = parse("R")
        
        result = prove(axioms, goal)
        assert result.success
    
    def test_and_elim_proof(self):
        """测试合取消除证明"""
        axioms = [parse("P & Q")]
        goal = parse("P")
        
        result = prove(axioms, goal)
        assert result.success
    
    def test_invalid_proof(self):
        """测试无效证明"""
        axioms = [parse("P")]
        goal = parse("Q")  # Q 不能从 P 推出
        
        result = prove(axioms, goal)
        assert not result.success


class TestSemanticEntailment:
    """语义蕴涵测试"""
    
    def test_modus_ponens_valid(self):
        """测试 MP 的有效性"""
        axioms = [parse("P"), parse("P -> Q")]
        goal = parse("Q")
        
        assert entails(axioms, goal)
    
    def test_modus_tollens_valid(self):
        """测试 MT 的有效性"""
        axioms = [parse("P -> Q"), parse("~Q")]
        goal = parse("~P")
        
        assert entails(axioms, goal)
    
    def test_invalid_entailment(self):
        """测试无效蕴涵"""
        axioms = [parse("P")]
        goal = parse("Q")
        
        assert not entails(axioms, goal)
    
    def test_syllogism(self):
        """测试三段论"""
        axioms = [
            parse("P"),
            parse("P -> Q"),
            parse("Q -> R")
        ]
        goal = parse("R")
        
        assert entails(axioms, goal)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

