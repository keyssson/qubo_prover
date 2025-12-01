"""
QUBO 编码测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qubo_prover.logic.parser import parse
from qubo_prover.qubo.encoder import FormulaEncoder, encode_formula
from qubo_prover.qubo.builder import QUBOBuilder, build_qubo


class TestFormulaEncoder:
    """公式编码器测试"""
    
    def test_encode_variable(self):
        """测试变量编码"""
        encoder = FormulaEncoder()
        var = parse("P")
        
        encoded = encoder.encode(var)
        
        assert encoded.var_name == "P"
        assert encoded.is_atomic
        assert encoded.formula == var
    
    def test_encode_negation(self):
        """测试否定编码"""
        encoder = FormulaEncoder()
        formula = parse("~P")
        
        encoded = encoder.encode(formula)
        
        assert not encoded.is_atomic
        assert "Not" in encoded.var_name
        # 应该有结构约束
        assert len(encoder.get_constraints()) > 0
    
    def test_encode_implication(self):
        """测试蕴涵编码"""
        encoder = FormulaEncoder()
        formula = parse("P -> Q")
        
        encoded = encoder.encode(formula)
        
        assert not encoded.is_atomic
        assert "Imp" in encoded.var_name
        # 应该编码 P, Q, 和 P->Q
        assert len(encoder.get_all_vars()) >= 3
    
    def test_encode_conjunction(self):
        """测试合取编码"""
        encoder = FormulaEncoder()
        formula = parse("P & Q")
        
        encoded = encoder.encode(formula)
        
        assert not encoded.is_atomic
        assert "And" in encoded.var_name
    
    def test_encode_disjunction(self):
        """测试析取编码"""
        encoder = FormulaEncoder()
        formula = parse("P | Q")
        
        encoded = encoder.encode(formula)
        
        assert not encoded.is_atomic
        assert "Or" in encoded.var_name
    
    def test_encode_reuse(self):
        """测试重复编码（应该复用）"""
        encoder = FormulaEncoder()
        formula = parse("P")
        
        enc1 = encoder.encode(formula)
        enc2 = encoder.encode(formula)
        
        assert enc1.var_name == enc2.var_name
        assert enc1.qubo_var is enc2.qubo_var


class TestQUBOBuilder:
    """QUBO 构建器测试"""
    
    def test_build_simple(self):
        """测试简单 QUBO 构建"""
        builder = QUBOBuilder(verbose=False)
        
        problem = builder.build(["P"], "P")
        
        assert problem.model is not None
        assert len(problem.axiom_vars) == 1
        assert problem.goal_var is not None
    
    def test_build_modus_ponens(self):
        """测试 Modus Ponens QUBO"""
        builder = QUBOBuilder(verbose=False)
        
        problem = builder.build(["P", "P -> Q"], "Q")
        
        assert len(problem.axiom_vars) == 2
        assert len(problem.var_map) >= 3  # P, Q, P->Q
    
    def test_build_with_weights(self):
        """测试带权重的 QUBO"""
        builder = QUBOBuilder(verbose=False)
        
        rule_weights = {
            "modus_ponens": 0.9,
            "modus_tollens": 0.5
        }
        
        problem = builder.build(["P", "P -> Q"], "Q", rule_weights)
        
        assert problem.model is not None
    
    def test_variable_info(self):
        """测试变量信息"""
        builder = QUBOBuilder(verbose=False)
        
        problem = builder.build(["P", "P -> Q"], "Q")
        
        var_info = builder.get_variable_info()
        
        assert "all_vars" in var_info
        assert "prop_vars" in var_info
        assert "axiom_vars" in var_info
        assert "goal_var" in var_info


class TestBuildQubo:
    """build_qubo 便捷函数测试"""
    
    def test_build_qubo_function(self):
        """测试 build_qubo 函数"""
        problem = build_qubo(["P", "P -> Q"], "Q", verbose=False)
        
        assert problem.model is not None
        assert problem.bqm is not None
        assert problem.qubo_dict is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

