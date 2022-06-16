from collections import defaultdict
from itertools import combinations, chain
from typing import Iterator, Optional, Set

from more_itertools import powerset

from datatypes import KnowledgeBase, Alphabet, Valuation, Formula


def print_knowledge_base(knowledge_base: KnowledgeBase):
    print("{", ', '.join(map(str, knowledge_base)), "}")


def all_valuations(alphabet: Alphabet, complete: bool = False) -> Iterator[Valuation]:
    subsets = powerset(alphabet)
    for subset in subsets:
        valuation = defaultdict(lambda: False)
        for atom in subset:
            valuation[atom] = True
        if complete:
            for atom in alphabet:
                if atom not in subset:
                    valuation[atom] = False
        yield valuation


def print_valuation(valuation: Valuation, alphabet: Optional[Alphabet] = None):
    trues = set()
    falses = set()
    for atom, value in valuation.items():
        if value:
            trues.add(atom)
        else:
            falses.add(atom)
    if alphabet is not None:
        falses.update(alphabet - trues)
        alph_str_len = len(''.join(map(str, alphabet)))
        pad = alph_str_len + len(alphabet) - 1
    else:
        alph_str_len = len(''.join(map(str, trues))) + len(''.join(map(str, falses)))
        pad = alph_str_len + len(trues) + len(falses)

    print("{", ' '.join(map(str, trues)).ljust(pad), "}", "{", ' '.join(map(str, falses)).ljust(pad), "}")


def models(formulas: Set[Formula], alphabet: Optional[Alphabet] = None) -> Iterator[Valuation]:
    if alphabet is None:
        alphabet = {atom for formula in formulas for atom in formula.atoms}
    for valuation in all_valuations(alphabet):
        if all(formula.evaluate(valuation) for formula in formulas):
            yield valuation


def sat(formulas: Set[Formula], alphabet: Optional[Alphabet] = None) -> bool:
    model = next(models(formulas, alphabet), None)
    return model is not None


def unsat(formulas: Set[Formula], alphabet: Optional[Alphabet] = None) -> bool:
    return not sat(formulas, alphabet)

def entails(formulas: Set[Formula], formula: Formula) -> bool:
    return unsat(formulas | {-formula})

def valid(formulas: Set[Formula], alphabet: Optional[Alphabet] = None) -> bool:
    if alphabet is None:
        alphabet = {atom for formula in formulas for atom in formula.atoms}
    for valuation in all_valuations(alphabet):
        if any(not formula.evaluate(valuation) for formula in formulas):
            return False
    return True


def materialized(knowledge_base: KnowledgeBase) -> Set[Formula]:
    return {statement.materialize() for statement in knowledge_base}
