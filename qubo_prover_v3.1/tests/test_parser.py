"""
解析器测试
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qubo_prover.logic.parser import parse, ParseError
from qubo_prover.logic.ast import Var, Not, And, Or, Imply, Iff


class TestParser:
    """解析器测试"""
    
    def test_parse_variable(self):
        """测试变量解析"""
        result = parse("P")
        assert result == Var("P")
        
        result = parse("Foo")
        assert result == Var("Foo")
        
        result = parse("X1")
        assert result == Var("X1")
    
    def test_parse_negation(self):
        """测试否定解析"""
        result = parse("~P")
        assert result == Not(Var("P"))
        
        result = parse("~~P")
        assert result == Not(Not(Var("P")))
    
    def test_parse_conjunction(self):
        """测试合取解析"""
        result = parse("P & Q")
        assert result == And(Var("P"), Var("Q"))
        
        result = parse("P&Q&R")
        # 左结合
        assert result == And(And(Var("P"), Var("Q")), Var("R"))
    
    def test_parse_disjunction(self):
        """测试析取解析"""
        result = parse("P | Q")
        assert result == Or(Var("P"), Var("Q"))
    
    def test_parse_implication(self):
        """测试蕴涵解析"""
        result = parse("P -> Q")
        assert result == Imply(Var("P"), Var("Q"))
        
        # 蕴涵链
        result = parse("P -> Q -> R")
        assert result == Imply(Imply(Var("P"), Var("Q")), Var("R"))
    
    def test_parse_biconditional(self):
        """测试等价解析"""
        result = parse("P <-> Q")
        assert result == Iff(Var("P"), Var("Q"))
    
    def test_parse_parentheses(self):
        """测试括号解析"""
        result = parse("(P)")
        assert result == Var("P")
        
        result = parse("(P & Q)")
        assert result == And(Var("P"), Var("Q"))
        
        result = parse("(P | Q) -> R")
        assert result == Imply(Or(Var("P"), Var("Q")), Var("R"))
    
    def test_parse_complex(self):
        """测试复杂公式解析"""
        # Modus Ponens 形式
        result = parse("P & (P -> Q)")
        expected = And(Var("P"), Imply(Var("P"), Var("Q")))
        assert result == expected
        
        # 复杂嵌套
        result = parse("~(P & Q) -> (~P | ~Q)")
        expected = Imply(
            Not(And(Var("P"), Var("Q"))),
            Or(Not(Var("P")), Not(Var("Q")))
        )
        assert result == expected
    
    def test_parse_priority(self):
        """测试运算符优先级"""
        # ~ 优先于 &
        result = parse("~P & Q")
        assert result == And(Not(Var("P")), Var("Q"))
        
        # & 优先于 |
        result = parse("P | Q & R")
        assert result == Or(Var("P"), And(Var("Q"), Var("R")))
        
        # | 优先于 ->
        result = parse("P -> Q | R")
        assert result == Imply(Var("P"), Or(Var("Q"), Var("R")))
    
    def test_parse_whitespace(self):
        """测试空白处理"""
        assert parse("P") == parse(" P ")
        assert parse("P->Q") == parse("P -> Q")
        assert parse("P&Q") == parse("P & Q")
    
    def test_parse_error(self):
        """测试解析错误"""
        with pytest.raises(ParseError):
            parse("")
        
        with pytest.raises(ParseError):
            parse("P &")
        
        with pytest.raises(ParseError):
            parse("(P")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

