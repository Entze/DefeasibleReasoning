from numbers import Number
from typing import Mapping, Optional, Set

from frozendict import frozendict

from datatypes import KnowledgeBase, Valuation, Alphabet, Normally, Formula, Literal, Atom, Bot, Top
from util import all_valuations, print_knowledge_base, print_valuation, materialized, unsat, entails

RankedModel = Mapping[Valuation, Number]


def valuation_in_min(antecedent: Formula, valuation: Valuation, ranked_model: RankedModel) -> bool:
    i = ranked_model[valuation]
    for valuation, rank in ranked_model.items():
        if rank >= i:
            continue
        if antecedent(valuation):
            return False
    return True


def violates_statement(statement: Normally, valuation: Valuation, ranked_model: RankedModel):
    antecedent = statement.left
    if not valuation_in_min(antecedent, valuation, ranked_model):
        return False
    if statement.materialize()(valuation):
        return False
    return True


def minimal_ranked_model(knowledge_base: KnowledgeBase, alphabet: Optional[Alphabet] = None):
    if alphabet is None:
        alphabet = {atom for statement in knowledge_base for atom in statement.atoms}
    ranked_model = {}
    U = set(frozendict(valuation) for valuation in all_valuations(alphabet, True))
    for valuation in U:
        ranked_model[valuation] = 0
    i = 0
    V = U
    V_ = set()
    while True:
        V_ = V
        V = {valuation for valuation in U if ranked_model[valuation] == i and any(
            violates_statement(statement, valuation, ranked_model) for statement in knowledge_base)}
        if V == V_:
            for valuation in V:
                ranked_model[valuation] = float('inf')
            break  # Done
        else:
            i = i + 1
            for valuation in V:
                ranked_model[valuation] = i
    return ranked_model


StatementRanking = Mapping[Number, Set[Normally]]


def statement_ranking(knowledge_base: KnowledgeBase) -> StatementRanking:
    E = {0: knowledge_base}
    rank = {}
    i = 0
    while True:
        E[i + 1] = set()
        for statement in E[i]:
            if entails(materialized(E[i]), -statement.left):
                E[i + 1].add(statement)
        if E[i] == E[i + 1]:
            break
        rank[i] = E[i] - E[i + 1]
        i = i + 1
    rank[float('inf')] = E[i]
    return rank


def print_ranked_model(ranked_model: RankedModel, alphabet: Optional[Alphabet] = None):
    r = max(rank for rank in ranked_model.values() if rank < float('inf'))
    pad = len(str(r)) + 1
    if float('inf') in ranked_model.values():
        print('∞:'.rjust(pad), '-' * 8)
        for valuation, rank in ranked_model.items():
            if rank == float('inf'):
                print(' ' * (pad + 2), end='')
                print_valuation(valuation, alphabet)
    if len(ranked_model) > 1:
        for i in reversed(range(r + 1)):
            print('{}:'.format(i).rjust(pad), '-' * 8)
            for valuation, rank in ranked_model.items():
                if rank == i:
                    print(' ' * (pad + 2), end='')
                    print_valuation(valuation, alphabet)


def print_statement_ranking(statement_ranking: StatementRanking):
    r = len(statement_ranking) - (float('inf') in statement_ranking)
    pad = len(str(r)) + 1

    if len(statement_ranking) > 1:
        for i in range(r):
            print('{}:'.format(i).rjust(pad), end=' ')
            statements = statement_ranking[i]
            print_knowledge_base(statements)

    if float('inf') in statement_ranking.keys():
        print('∞:'.rjust(pad), end=' ')
        statements = statement_ranking[float('inf')]
        print_knowledge_base(statements)

