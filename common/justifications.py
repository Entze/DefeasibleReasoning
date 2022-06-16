from typing import Set, FrozenSet, Tuple

from more_itertools import powerset

from datatypes import KnowledgeBase, Formula, Normally
from util import entails, materialized


def separate(knowledge_base: KnowledgeBase) -> Tuple[KnowledgeBase, KnowledgeBase]:
    T = {statement for statement in knowledge_base if statement.is_classical}
    return T, knowledge_base - T


def justifications(classical_statements: KnowledgeBase, defeasible_statements: KnowledgeBase, formula: Formula) -> Set[
    FrozenSet[Normally]]:
    max_size = float('inf')
    js = set()
    for c in powerset(defeasible_statements):
        if len(c) <= max_size:
            candidate: FrozenSet[Formula] = set(c)
            if entails(materialized(candidate | classical_statements), -formula):
                if len(candidate) < max_size:
                    js.clear()
                max_size = len(candidate)
                js.add(frozenset(candidate))

    return js