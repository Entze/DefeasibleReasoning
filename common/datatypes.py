from dataclasses import dataclass, field
from enum import IntEnum
from typing import Mapping
from typing import TypeVar, Set, Union, Optional


@dataclass(frozen=True, order=True)
class Atom:
    symbol: str

    def __str__(self):
        return self.symbol


Alphabet = Set[Atom]
Valuation = Mapping[Atom, bool]


class Connective(IntEnum):
    And = 0
    Or = 1
    Implies = 2

    def __str__(self):
        if self is Connective.And:
            return "∧"
        elif self is Connective.Or:
            return "∨"
        elif self is Connective.Implies:
            return "→"
        else:
            assert False, "Unhandled Connective.__str__: {} = {}".format(self.name, self.value)

    def evaluate(self, left: bool, right: bool):
        if self is Connective.And:
            return left and right
        elif self is Connective.Or:
            return left or right
        elif self is Connective.Implies:
            return not left or right
        else:
            assert False, "Unhandled Connective.evaluate: {} = {}".format(self.name, self.value)


ForwardFormula = TypeVar('ForwardFormula', bound='Formula')


@dataclass(frozen=True, order=True)
class Literal:
    atom: Atom
    sign: bool = field(default=True)

    def __str__(self):
        sign_str = ""
        if not self.sign:
            sign_str = "¬"
        return "{}{}".format(sign_str, self.atom)

    def __repr__(self):
        return str(self)

    def __neg__(self):
        return Literal(self.atom, not self.sign)

    def __and__(self, other):
        left = Formula(self)
        right = other
        if isinstance(other, Literal):
            right = Formula(right)
        return Formula(left, Connective.And, right)

    def __or__(self, other):
        left = Formula(self)
        right = other
        if isinstance(other, Literal):
            right = Formula(right)
        return Formula(left, Connective.Or, right)

    def __rshift__(self, other):
        left = Formula(self)
        right = other
        if isinstance(other, Literal):
            right = Formula(right)
        return Formula(left, Connective.Implies, right)

    def __truediv__(self, other):
        left = Formula(self)
        right = other
        if isinstance(other, Literal):
            right = Formula(other)
        return Normally(left, right)


@dataclass(frozen=True, order=True)
class Top(Literal):
    atom: Atom = field(default=Atom('⊤'), init=False)
    sign: bool = field(default=True, init=False)

    def __str__(self):
        return str(self.atom)

    def __repr__(self):
        return str(self)

    def __neg__(self):
        return Bot()

    def __and__(self, other):
        if isinstance(other, Literal):
            return Formula(other)
        return other

    def __or__(self, other):
        return Formula(Top())


@dataclass(frozen=True, order=True)
class Bot(Literal):
    atom: Atom = field(default=Atom('⊥'), init=False)
    sign: bool = field(default=False, init=False)

    def __neg__(self):
        return Top()

    def __str__(self):
        return str(self.atom)

    def __and__(self, other):
        return Formula(Bot())

    def __or__(self, other):
        if isinstance(other, Literal):
            return Formula(other)
        return other

@dataclass(frozen=True, order=True)
class Formula:
    left: Union[ForwardFormula, Literal]
    connective: Optional[Connective] = field(default=None)
    right: Union[ForwardFormula, None] = field(default=None)

    def __str__(self):
        left_str = str(self.left)
        connective_str = ""
        if self.connective is not None:
            connective_str = " {}".format(self.connective)
        right_str = ""
        if self.right is not None:
            if self.right.left == Bot() and self.right.right is None:
                left_str = "¬({})".format(left_str)
                connective_str = ""
            else:
                right_str = " {}".format(self.right)
        return "{}{}{}".format(left_str, connective_str, right_str)

    def __repr__(self):
        return str(self)

    def evaluate(self, valuation: Valuation) -> bool:
        if isinstance(self.left, Literal):
            value_left = self.__evaluate_literal(self.left, valuation)
        else:
            assert isinstance(self.left, Formula), "Unknown type for Formula.left. {}: {}".format(
                type(self.left).__name__, self.left)
            value_left = self.left.evaluate(valuation)
        if self.connective is not None and self.right is None:
            raise TypeError("Formula.connective present, despite Formula.right missing.")
        elif self.connective is None and self.right is not None:
            raise TypeError("Formula.connective missing, despite Formula.right present.")

        if self.connective is None and self.right is None:
            return value_left
        else:
            assert isinstance(self.right, Formula), "Unknown type for Formula.right. {}: {}".format(
                type(self.right).__name__, self.right)
            value_right = self.right.evaluate(valuation)

            return self.connective.evaluate(value_left, value_right)

    def __evaluate_literal(self, literal: Literal, valuation: Valuation) -> bool:
        if isinstance(literal, Top) or isinstance(literal, Bot):
            return literal.sign
        else:
            # get assigned truth value of atom (per default false) and flip the result if negated
            return bool(valuation.get(literal.atom, False) ^ (not literal.sign))

    @property
    def literals(self) -> Set[Literal]:
        literals = set()
        if isinstance(self.left, Literal):
            if not isinstance(self.left, Top) and not isinstance(self.left, Bot):
                literals.add(self.left)
        else:
            assert isinstance(self.left, Formula), "Unknown type for Formula.right. {}: {}".format(
                type(self.left).__name__, self.left)
            literals.update(self.left.literals)
        if self.right is not None:
            assert isinstance(self.right, Formula), "Unknown type for Formula.right. {}: {}".format(
                type(self.right).__name__, self.right)
            literals.update(self.right.literals)
        return literals

    @property
    def atoms(self) -> Set[Atom]:
        return {literal.atom for literal in self.literals}

    def __neg__(self):
        if self.connective is not None and self.right is None:
            raise TypeError("Formula.connective present, despite Formula.right missing.")
        elif self.connective is None and self.right is not None:
            raise TypeError("Formula.connective missing, despite Formula.right present.")

        if self.connective is None and self.right is None:
            return Formula(-self.left)
        elif self.connective is Connective.And:
            return Formula(-self.left, Connective.Or, -self.right)
        elif self.connective is Connective.Or:
            return Formula(-self.left, Connective.And, -self.right)
        elif self.connective is Connective.Implies:
            if self.right.left == Bot() and self.right.right is None:
                return self.left
            return Formula(self, Connective.Implies, Formula(Bot()))
        else:
            assert False, "Unknown Formula.connective. {} = {}.".format(self.connective.name, self.connective.value)

    def __and__(self, other):
        left = self
        right = other
        if isinstance(other, Literal):
            right = Formula(right)
        return Formula(left, Connective.And, right)

    def __or__(self, other):
        left = self
        right = other
        if isinstance(other, Literal):
            right = Formula(right)
        return Formula(left, Connective.Or, right)

    def __rshift__(self, other):
        left = self
        right = other
        if isinstance(other, Literal):
            right = Formula(right)
        return Formula(left, Connective.Implies, right)

    def __truediv__(self, other):
        left = self
        right = other
        if isinstance(other, Literal):
            right = Formula(other)
        return Normally(left, right)

    def __call__(self, valuation: Valuation) -> bool:
        return self.evaluate(valuation)


@dataclass(frozen=True, order=True)
class Normally:
    left: Formula
    right: Formula

    def __str__(self):
        if self.right.left == Bot() and self.right.right is None and self.left.right.left == Bot() and self.left.right.right is None:
            return str(self.left.left)
        return "{} |~ {}".format(self.left, self.right)

    def __repr__(self):
        return str(self)

    @property
    def literals(self) -> Set[Literal]:
        return {literal for formula in (self.left, self.right) for literal in formula.literals}

    @property
    def atoms(self) -> Set[Atom]:
        return {atom for formula in (self.left, self.right) for atom in formula.atoms}

    @property
    def is_classical(self) -> bool:
        return self.right.left == Bot() and self.right.right is None

    def materialize(self):
        if self.right.left == Bot() and self.right.right is None:
            if self.left.right.left == Bot() and self.left.right.right is None:
                return self.left.left
            return -self.left
        return self.left >> self.right


KnowledgeBase = Set[Normally]
