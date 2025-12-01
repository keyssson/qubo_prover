"""
命题逻辑公式解析器

支持的语法：
    Iff    ::= Imply ('<->' Imply)*
    Imply  ::= Or ('->' Or)*
    Or     ::= And ('|' And)*
    And    ::= Unary ('&' Unary)*
    Unary  ::= '~' Unary | Primary
    Primary ::= '(' Iff ')' | Var
    Var    ::= [A-Za-z_][A-Za-z0-9_]*

运算符优先级（从低到高）：
    1. <->  双条件（等价）
    2. ->   蕴涵
    3. |    析取（或）
    4. &    合取（与）
    5. ~    否定（非）

示例：
    parse("P")           -> Var("P")
    parse("~P")          -> Not(Var("P"))
    parse("P & Q")       -> And(Var("P"), Var("Q"))
    parse("P | Q")       -> Or(Var("P"), Var("Q"))
    parse("P -> Q")      -> Imply(Var("P"), Var("Q"))
    parse("P <-> Q")     -> Iff(Var("P"), Var("Q"))
    parse("P & Q -> R")  -> Imply(And(Var("P"), Var("Q")), Var("R"))
"""

from __future__ import annotations
from .ast import Expr, Var, Not, And, Or, Imply, Iff


class ParseError(Exception):
    """解析错误"""
    pass


class Lexer:
    """词法分析器"""
    
    # 多字符运算符（按长度降序排列以优先匹配）
    MULTI_CHAR_OPS = ["<->", "->"]
    
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self._skip_whitespace()
    
    def _skip_whitespace(self):
        """跳过空白字符"""
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1
    
    def peek(self) -> str:
        """
        查看当前 token（不消费）
        
        Returns:
            当前 token，或空字符串表示 EOF
        """
        if self.pos >= len(self.text):
            return ""
        
        # 检查多字符运算符
        for op in self.MULTI_CHAR_OPS:
            if self.text[self.pos:].startswith(op):
                return op
        
        return self.text[self.pos]
    
    def advance(self, count: int = 1):
        """
        前进指定字符数
        
        Args:
            count: 前进的字符数
        """
        self.pos += count
        self._skip_whitespace()
    
    def eat(self, expected: str) -> bool:
        """
        尝试消费指定的 token
        
        Args:
            expected: 期望的 token
            
        Returns:
            是否成功消费
        """
        if self.peek() == expected:
            self.advance(len(expected))
            return True
        return False
    
    def expect(self, expected: str):
        """
        期望并消费指定的 token，否则抛出异常
        
        Args:
            expected: 期望的 token
            
        Raises:
            ParseError: token 不匹配
        """
        if not self.eat(expected):
            raise ParseError(
                f"Expected '{expected}' at position {self.pos}, "
                f"got '{self.peek()}' in '{self.text}'"
            )
    
    def is_eof(self) -> bool:
        """是否到达输入末尾"""
        return self.pos >= len(self.text)
    
    def read_identifier(self) -> str:
        """
        读取标识符（变量名）
        
        Returns:
            标识符字符串
            
        Raises:
            ParseError: 无效的标识符
        """
        start = self.pos
        
        # 首字符必须是字母或下划线
        if self.pos < len(self.text) and (self.text[self.pos].isalpha() or self.text[self.pos] == '_'):
            self.pos += 1
            # 后续字符可以是字母、数字或下划线
            while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
                self.pos += 1
        
        if self.pos == start:
            raise ParseError(
                f"Expected identifier at position {self.pos} in '{self.text}'"
            )
        
        result = self.text[start:self.pos]
        self._skip_whitespace()
        return result


def parse(text: str) -> Expr:
    """
    解析命题逻辑公式
    
    Args:
        text: 公式字符串
        
    Returns:
        解析后的 AST
        
    Raises:
        ParseError: 解析错误
        
    Examples:
        >>> parse("P")
        Var('P')
        >>> parse("P -> Q")
        Imply(Var('P'), Var('Q'))
        >>> parse("~(P & Q)")
        Not(And(Var('P'), Var('Q')))
    """
    if not text or not text.strip():
        raise ParseError("Empty input")
    
    lexer = Lexer(text)
    result = _parse_iff(lexer)
    
    if not lexer.is_eof():
        raise ParseError(
            f"Unexpected input at position {lexer.pos}: "
            f"'{lexer.text[lexer.pos:]}' in '{text}'"
        )
    
    return result


def _parse_iff(lexer: Lexer) -> Expr:
    """解析双条件（等价）"""
    left = _parse_imply(lexer)
    
    while lexer.eat("<->"):
        right = _parse_imply(lexer)
        left = Iff(left, right)
    
    return left


def _parse_imply(lexer: Lexer) -> Expr:
    """解析蕴涵"""
    left = _parse_or(lexer)
    
    while lexer.eat("->"):
        right = _parse_or(lexer)
        left = Imply(left, right)
    
    return left


def _parse_or(lexer: Lexer) -> Expr:
    """解析析取"""
    left = _parse_and(lexer)
    
    while lexer.eat("|"):
        right = _parse_and(lexer)
        left = Or(left, right)
    
    return left


def _parse_and(lexer: Lexer) -> Expr:
    """解析合取"""
    left = _parse_unary(lexer)
    
    while lexer.eat("&"):
        right = _parse_unary(lexer)
        left = And(left, right)
    
    return left


def _parse_unary(lexer: Lexer) -> Expr:
    """解析一元运算符"""
    if lexer.eat("~"):
        operand = _parse_unary(lexer)
        return Not(operand)
    
    return _parse_primary(lexer)


def _parse_primary(lexer: Lexer) -> Expr:
    """解析基本表达式"""
    # 括号表达式
    if lexer.eat("("):
        expr = _parse_iff(lexer)
        lexer.expect(")")
        return expr
    
    # 变量
    name = lexer.read_identifier()
    return Var(name)


# ============================================================
# 便捷函数
# ============================================================

def parse_many(texts: list[str]) -> list[Expr]:
    """
    解析多个公式
    
    Args:
        texts: 公式字符串列表
        
    Returns:
        AST 列表
    """
    return [parse(t) for t in texts]


def parse_axioms(axiom_str: str, delimiter: str = ";") -> list[Expr]:
    """
    解析由分隔符分隔的公理字符串
    
    Args:
        axiom_str: 公理字符串，如 "P; P->Q; Q->R"
        delimiter: 分隔符
        
    Returns:
        公理 AST 列表
    """
    parts = [s.strip() for s in axiom_str.split(delimiter) if s.strip()]
    return parse_many(parts)

