"""Verifier for foundation/quantitative-aptitude/blood-relations.json (P3 Ch 12).

Blood-relations answers are usually a relationship WORD (father's sister = aunt),
which is reasoning, not computation, so those questions are flagged
`"numerical": false` and carry no verifier here. The functions below cover only
the COUNTING questions — how many members, how many are female, how many
generations, how many children, how many couples.

Each function encodes the family described in the stem as small Python data —
a list of members with a gender, a set of marriage pairs, or a chain of
parent-to-child links — then COMPUTES the count and maps it to an option key
through a dict of the option values. Nothing is copied from the answer key, so
a wrong key in the bank surfaces as a KeyError or as a mismatch the runner
reports.
"""

from __future__ import annotations


# ------------------------------------------------------------ shared helpers


def generations_in_chain(links):
    """Number of distinct levels on a straight parent-to-child chain.

    `links` is a list of (parent, child) pairs forming one descending line.
    The generation count is the number of distinct people on the line.
    """
    people = []
    for parent, child in links:
        if parent not in people:
            people.append(parent)
        if child not in people:
            people.append(child)
    return len(people)


def count_gender(members, want):
    """Count members whose gender equals `want`; members is [(name, gender)]."""
    return sum(1 for _name, gender in members if gender == want)


# ------------------------------------------------------ counting questions


def q_f3c12_005():
    # P father of Q, Q father of R, R father of S — one descending line.
    links = [("P", "Q"), ("Q", "R"), ("R", "S")]
    gens = generations_in_chain(links)
    key = {3: "A", 4: "B", 5: "C", 2: "D"}[gens]
    return {"answer": key, "computed": "%d generations" % gens}


def q_f3c12_013():
    # A=B couple; children C, D, E; C=F; C and F have child G. Count members.
    members = {"A", "B", "C", "D", "E", "F", "G"}
    n = len(members)
    key = {6: "A", 7: "B", 8: "C", 5: "D"}[n]
    return {"answer": key, "computed": "%d members" % n}


def q_f3c12_014():
    # M=N; their son O = P; their daughter Q = R. Count married couples.
    couples = {frozenset(("M", "N")), frozenset(("O", "P")), frozenset(("Q", "R"))}
    n = len(couples)
    key = {2: "A", 3: "B", 4: "C", 1: "D"}[n]
    return {"answer": key, "computed": "%d couples" % n}


def q_f3c12_035():
    # A man, his wife, his father, his mother, his two daughters. Count females.
    members = [
        ("man", "M"),
        ("wife", "F"),
        ("father", "M"),
        ("mother", "F"),
        ("daughter1", "F"),
        ("daughter2", "F"),
    ]
    females = count_gender(members, "F")
    key = {3: "A", 4: "B", 5: "C", 2: "D"}[females]
    return {"answer": key, "computed": "%d female" % females}


def q_f3c12_036():
    # A woman, her husband, her brother, her two sons, her daughter. Count males.
    members = [
        ("woman", "F"),
        ("husband", "M"),
        ("brother", "M"),
        ("son1", "M"),
        ("son2", "M"),
        ("daughter", "F"),
    ]
    males = count_gender(members, "M")
    key = {3: "A", 4: "B", 5: "C", 2: "D"}[males]
    return {"answer": key, "computed": "%d male" % males}


def q_f3c12_037():
    # W mother of X, X mother of Y, Y has son Z — one descending line.
    links = [("W", "X"), ("X", "Y"), ("Y", "Z")]
    gens = generations_in_chain(links)
    key = {2: "A", 3: "B", 4: "C", 5: "D"}[gens]
    return {"answer": key, "computed": "%d generations" % gens}


def q_f3c12_038():
    # Four sons, each with exactly one sister -> the sons SHARE one sister.
    sons = 4
    shared_sisters = 1  # one common sister, not one per son
    children = sons + shared_sisters
    key = {4: "A", 5: "B", 8: "C", 9: "D"}[children]
    return {"answer": key, "computed": "%d children" % children}


def q_f3c12_039():
    # Three children with 2, 3 and 1 children of their own. Count grandchildren.
    branches = [2, 3, 1]
    grandchildren = sum(branches)
    key = {3: "A", 5: "B", 6: "C", 7: "D"}[grandchildren]
    return {"answer": key, "computed": "%d grandchildren" % grandchildren}


def q_f3c12_040():
    # Grandfather, grandmother, two sons, two wives, three grandchildren.
    members = 2 + 2 + 2 + 3
    key = {8: "A", 9: "B", 10: "C", 7: "D"}[members]
    return {"answer": key, "computed": "%d members" % members}


def q_f3c12_041():
    # Five daughters, each with exactly one brother -> ONE shared brother.
    daughters = 5
    sons = 1  # the single brother is common to all five daughters
    key = {1: "A", 5: "B", 2: "C", 6: "D"}[sons]
    return {"answer": key, "computed": "%d son(s)" % sons}


def q_f3c12_042():
    # G=H; sons J, K; daughter L; J=M; L=N; K unmarried. Count couples.
    couples = {frozenset(("G", "H")), frozenset(("J", "M")), frozenset(("L", "N"))}
    n = len(couples)  # K forms no couple
    key = {2: "A", 3: "B", 4: "C", 5: "D"}[n]
    return {"answer": key, "computed": "%d couples" % n}
