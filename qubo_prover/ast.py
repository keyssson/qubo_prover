from dataclasses import dataclass
from typing import Union


class Sentence:
	pass


@dataclass(frozen=True)
class Var(Sentence):
	name: str


@dataclass(frozen=True)
class Not(Sentence):
	operand: Sentence


@dataclass(frozen=True)
class And(Sentence):
	left: Sentence
	right: Sentence


@dataclass(frozen=True)
class Or(Sentence):
	left: Sentence
	right: Sentence


@dataclass(frozen=True)
class Imply(Sentence):
	left: Sentence
	right: Sentence


Expr = Union[Var, Not, And, Or, Imply]
