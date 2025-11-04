from __future__ import annotations
from typing import List, Tuple
from .ast import Var, Not, And, Or, Imply, Expr


class Lexer:
	def __init__(self, s: str):
		self.s = s.replace(" ", "")
		self.i = 0

	def peek(self) -> str:
		return self.s[self.i:self.i+2] if self.s[self.i:self.i+2] == "->" else self.s[self.i:self.i+1]

	def eat(self, t: str) -> bool:
		if self.s[self.i:].startswith(t):
			self.i += len(t)
			return True
		return False

	def eof(self) -> bool:
		return self.i >= len(self.s)


def parse(sentence: str) -> Expr:
	lexer = Lexer(sentence)
	expr = _parse_imply(lexer)
	if not lexer.eof():
		raise ValueError(f"Unexpected input at {lexer.s[lexer.i:]} in '{sentence}'")
	return expr


def _parse_imply(lx: Lexer) -> Expr:
	expr = _parse_or(lx)
	while lx.eat("->"):
		right = _parse_or(lx)
		expr = Imply(expr, right)
	return expr


def _parse_or(lx: Lexer) -> Expr:
	expr = _parse_and(lx)
	while lx.eat("|"):
		right = _parse_and(lx)
		expr = Or(expr, right)
	return expr


def _parse_and(lx: Lexer) -> Expr:
	expr = _parse_unary(lx)
	while lx.eat("&"):
		right = _parse_unary(lx)
		expr = And(expr, right)
	return expr


def _parse_unary(lx: Lexer) -> Expr:
	if lx.eat("~"):
		return Not(_parse_unary(lx))
	if lx.eat("("):
		expr = _parse_imply(lx)
		if not lx.eat(")"):
			raise ValueError("Missing closing parenthesis")
		return expr
	# variable: contiguous letters/numbers/underscores
	start = lx.i
	while not lx.eof() and lx.peek().isalnum() or (not lx.eof() and lx.peek() == "_"):
		lx.i += 1
	if lx.i == start:
		raise ValueError("Expected variable or '(' or '~'")
	name = lx.s[start:lx.i]
	return Var(name)
