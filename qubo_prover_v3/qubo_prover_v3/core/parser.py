"""
命题逻辑公式解析器
将字符串解析为 AST
"""

from __future__ import annotations
from .ast import Var, Not, And, Or, Imply, Expr


class Lexer:
    """词法分析器"""
    
    def __init__(self, s: str):
        self.s = s.replace(" ", "")  # 移除空格
        self.i = 0
    
    def peek(self) -> str:
        """查看当前字符（或双字符运算符）"""
        if self.s[self.i:self.i+2] == "->":
            return "->"
        return self.s[self.i:self.i+1]
    
    def eat(self, t: str) -> bool:
        """尝试消费指定的 token"""
        if self.s[self.i:].startswith(t):
            self.i += len(t)
            return True
        return False
    
    def eof(self) -> bool:
        """是否到达输入末尾"""
        return self.i >= len(self.s)


def parse(sentence: str) -> Expr:
    """
    解析命题逻辑公式
    
    语法（优先级从低到高）：
        Imply  ::= Or ('->' Or)*
        Or     ::= And ('|' And)*
        And    ::= Unary ('&' Unary)*
        Unary  ::= '~' Unary | Primary
        Primary ::= '(' Imply ')' | Var
        Var    ::= [A-Za-z_][A-Za-z0-9_]*
    
    Args:
        sentence: 公式字符串，如 "P -> Q"
        
    Returns:
        解析后的 AST
        
    Raises:
        ValueError: 解析错误
    """
    lexer = Lexer(sentence)
    expr = _parse_imply(lexer)
    if not lexer.eof():
        raise ValueError(f"Unexpected input at '{lexer.s[lexer.i:]}' in '{sentence}'")
    return expr


def _parse_imply(lx: Lexer) -> Expr:
    """解析蕴涵（最低优先级）"""
    expr = _parse_or(lx)
    while lx.eat("->"):
        right = _parse_or(lx)
        expr = Imply(expr, right)
    return expr


def _parse_or(lx: Lexer) -> Expr:
    """解析析取"""
    expr = _parse_and(lx)
    while lx.eat("|"):
        right = _parse_and(lx)
        expr = Or(expr, right)
    return expr


def _parse_and(lx: Lexer) -> Expr:
    """解析合取"""
    expr = _parse_unary(lx)
    while lx.eat("&"):
        right = _parse_unary(lx)
        expr = And(expr, right)
    return expr


def _parse_unary(lx: Lexer) -> Expr:
    """解析一元运算符（否定）和基本表达式"""
    if lx.eat("~"):
        return Not(_parse_unary(lx))
    if lx.eat("("):
        expr = _parse_imply(lx)
        if not lx.eat(")"):
            raise ValueError("Missing closing parenthesis")
        return expr
    
    # 解析变量名
    start = lx.i
    while not lx.eof() and (lx.peek().isalnum() or lx.peek() == "_"):
        lx.i += 1
    
    if lx.i == start:
        raise ValueError(f"Expected variable or '(' or '~' at position {lx.i}")
    
    name = lx.s[start:lx.i]
    return Var(name)

