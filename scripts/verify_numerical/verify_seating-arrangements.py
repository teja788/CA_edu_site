"""Verifier for foundation/quantitative-aptitude/seating-arrangements.json (P3 Ch 11).

Seating puzzles are pure reasoning, so most questions are `numerical: false` and
carry no verifier. The functions below cover only the `numerical: true`
questions — those whose answer is a COUNT that follows from the stem's own
clues: how many persons sit between two people, how many sit to one side, how
many are in the row, how many face a given way, and the position-formula
questions.

Nothing is copied from the answer key. Each counting question is modelled from
scratch — a row is a Python list of seats, a circle is a ring of seats, and the
people are placed by brute-forcing every arrangement that satisfies the clues.
The computed count is then mapped to an option key through a dict of the four
option values, so a wrong key in the bank surfaces as a KeyError or as a
mismatch the runner reports.

Conventions used below, matching the notes exactly:
  * A single row is numbered 1..n from the reader's left to the reader's right.
    When the row faces NORTH, a person's own left is the lower seat number and
    their own right is the higher seat number (left/right align with the page).
  * "m-th from the left" is seat m; "k-th from the right" in a row of n is seat
    n - k + 1; so a person m-th from the left and k-th from the right fixes
    n = m + k - 1.
  * Persons strictly between seats p and q (p < q) number q - p - 1.
  * A circle is numbered 1..n clockwise. Facing the centre, a person's right is
    the anticlockwise neighbour and their left is the clockwise neighbour; the
    two reverse when the person faces outward. Persons strictly between X and Y
    counted clockwise from X number (posY - posX - 1) mod n.
"""

from __future__ import annotations

from itertools import permutations


# ------------------------------------------------------------ shared helpers


def solve_row(names, n, constraints):
    """Return the unique seat map {name: seat} for a row of n seats (1..n).

    `constraints` is a list of predicates taking the seat map and returning
    True when satisfied. The function asserts that exactly one arrangement
    survives, so an under-determined puzzle fails loudly instead of guessing.
    """
    solutions = []
    for perm in permutations(range(1, n + 1), len(names)):
        seat = dict(zip(names, perm))
        if all(c(seat) for c in constraints):
            solutions.append(seat)
    assert len(solutions) == 1, "row puzzle is not uniquely determined: %d layouts" % len(solutions)
    return solutions[0]


def solve_circle(names, n, constraints, anchor=None):
    """Return the unique seat map for a circle numbered 1..n clockwise.

    `anchor` = (name, seat) pins one person to kill the rotational symmetry, so
    the layout is unique as a genuine seating rather than up to rotation.
    """
    fixed = {}
    free = list(names)
    seats = list(range(1, n + 1))
    if anchor is not None:
        aname, aseat = anchor
        fixed[aname] = aseat
        free = [x for x in names if x != aname]
        seats = [s for s in seats if s != aseat]
    solutions = []
    for perm in permutations(seats, len(free)):
        seat = dict(fixed)
        seat.update(dict(zip(free, perm)))
        if all(c(seat) for c in constraints):
            solutions.append(seat)
    assert len(solutions) == 1, "circle puzzle is not uniquely determined: %d layouts" % len(solutions)
    return solutions[0]


def between_row(seat, x, y):
    """Persons strictly between x and y in a row."""
    return abs(seat[x] - seat[y]) - 1


def cw(s, k, n):
    """The seat k steps clockwise from seat s on a circle of n (1-based)."""
    return ((s - 1 + k) % n) + 1


def acw(s, k, n):
    """The seat k steps anticlockwise from seat s on a circle of n (1-based)."""
    return ((s - 1 - k) % n) + 1


def between_cw(seat, x, y, n):
    """Persons strictly between x and y counted clockwise from x."""
    return (seat[y] - seat[x] - 1) % n


# --------------------------------------------------- reusable puzzle layouts


def puzzle_A():
    # Six friends P, Q, R, S, T, U in a row facing north.
    # R extreme left; T immediately right of R; P has two persons to his left;
    # S immediately right of P; Q extreme right; U immediately left of Q.
    names = ["P", "Q", "R", "S", "T", "U"]
    cons = [
        lambda s: s["R"] == 1,
        lambda s: s["T"] == s["R"] + 1,
        lambda s: s["P"] == 3,               # exactly two persons (seats 1,2) to P's left
        lambda s: s["S"] == s["P"] + 1,
        lambda s: s["Q"] == 6,
        lambda s: s["U"] == s["Q"] - 1,
    ]
    return solve_row(names, 6, cons)


def puzzle_B():
    # Five persons J, K, L, M, N in a row facing north.
    # N left end; K right end; L second to the left of K; M immediately left of L.
    names = ["J", "K", "L", "M", "N"]
    cons = [
        lambda s: s["N"] == 1,
        lambda s: s["K"] == 5,
        lambda s: s["L"] == s["K"] - 2,
        lambda s: s["M"] == s["L"] - 1,
    ]
    return solve_row(names, 5, cons)


def puzzle_C():
    # Two rows of four facing each other, columns 1..4 as the reader looks.
    # Row 1 (A, B, C, D) faces south; row 2 (P, Q, R, S) faces north.
    row1 = ["A", "B", "C", "D"]
    cons1 = [
        lambda s: s["B"] == 1,               # B at the left end as we look
        lambda s: s["A"] == s["B"] + 1,      # A immediately right of B as we look
        lambda s: s["C"] == 4,               # C at the right end as we look
    ]
    col1 = solve_row(row1, 4, cons1)         # -> B1 A2 D3 C4
    row2 = ["P", "Q", "R", "S"]
    cons2 = [
        lambda s: s["P"] == col1["B"],       # B faces P
        lambda s: s["Q"] == col1["A"],       # A faces Q
        lambda s: s["S"] == col1["C"],       # C faces S
        lambda s: s["R"] == col1["D"],       # D faces R
    ]
    col2 = solve_row(row2, 4, cons2)         # -> P1 Q2 R3 S4
    return col1, col2


def puzzle_D():
    # Eight persons around a circle facing the centre, seats 1..8 clockwise.
    # Facing centre: left = clockwise (+1), right = anticlockwise (-1).
    names = ["A", "B", "C", "D", "E", "F", "G", "H"]
    n = 8
    cons = [
        lambda s: s["F"] == cw(s["A"], 1, n),   # F immediately to A's left
        lambda s: s["C"] == cw(s["A"], 2, n),   # C second to A's left
        lambda s: s["B"] == cw(s["A"], 4, n),   # B fourth to A's left
        lambda s: s["G"] == cw(s["B"], 1, n),   # G immediately to B's left
        lambda s: s["D"] == cw(s["G"], 1, n),   # D immediately to G's left
        lambda s: s["E"] == acw(s["A"], 1, n),  # E immediately to A's right
        lambda s: s["H"] == acw(s["B"], 1, n),  # H immediately to B's right
    ]
    return solve_circle(names, n, cons, anchor=("A", 1))


# ------------------------------------------------ position-formula questions


def q_f3c11_005():
    # M is 6th from the left and 4th from the right: n = m + k - 1.
    m, k = 6, 4
    n = m + k - 1
    key = {9: "A", 10: "B", 8: "C", 11: "D"}[n]
    return {"answer": key, "computed": n}


def q_f3c11_006():
    # Row of 10: A 4th from left (seat 4), B 3rd from right (seat 10-3+1=8).
    n = 10
    a = 4
    b = n - 3 + 1
    between = abs(a - b) - 1
    key = {2: "A", 3: "B", 4: "C", 5: "D"}[between]
    return {"answer": key, "computed": between}


def q_f3c11_012():
    # 25 in a row, Ravi 11th from the left: persons to his right = n - position.
    n, pos = 25, 11
    right = n - pos
    key = {13: "A", 14: "B", 15: "C", 11: "D"}[right]
    return {"answer": key, "computed": right}


def q_f3c11_024():
    # Row of 15: X 5th from left (seat 5), Y 6th from right (seat 15-6+1=10).
    n = 15
    x = 5
    y = n - 6 + 1
    between = abs(x - y) - 1
    key = {3: "A", 5: "B", 4: "C", 6: "D"}[between]
    return {"answer": key, "computed": between}


def q_f3c11_025():
    # Row of 15: P 7th from the left; position from the right = n - m + 1.
    n, m = 15, 7
    from_right = n - m + 1
    key = {8: "A", 9: "B", 10: "C", 7: "D"}[from_right]
    return {"answer": key, "computed": from_right}


def q_f3c11_038():
    # A is 10th from the left and 5th from the right: n = m + k - 1.
    m, k = 10, 5
    n = m + k - 1
    key = {15: "A", 14: "B", 13: "C", 16: "D"}[n]
    return {"answer": key, "computed": n}


def q_f3c11_042():
    # Row of 40, 16th from the left; position from the right = n - m + 1.
    n, m = 40, 16
    from_right = n - m + 1
    key = {24: "A", 25: "B", 26: "C", 16: "D"}[from_right]
    return {"answer": key, "computed": from_right}


# ----------------------------------------------- single-row puzzle questions


def q_f3c11_009():
    # Puzzle A: persons between P and Q.
    seat = puzzle_A()
    c = between_row(seat, "P", "Q")
    key = {3: "A", 2: "B", 1: "C", 4: "D"}[c]
    return {"answer": key, "computed": "layout=%s, between=%d" % (_row_str(seat), c)}


def q_f3c11_011():
    # Puzzle A: persons seated to the right of P (higher seat numbers).
    seat = puzzle_A()
    c = sum(1 for name, s in seat.items() if s > seat["P"])
    key = {2: "A", 4: "B", 3: "C", 5: "D"}[c]
    return {"answer": key, "computed": c}


def q_f3c11_036():
    # Puzzle A: persons seated to the left of S (lower seat numbers).
    seat = puzzle_A()
    c = sum(1 for name, s in seat.items() if s < seat["S"])
    key = {2: "A", 3: "B", 4: "C", 1: "D"}[c]
    return {"answer": key, "computed": c}


def q_f3c11_048():
    # Puzzle B: persons between M and K.
    seat = puzzle_B()
    c = between_row(seat, "M", "K")
    key = {1: "A", 2: "B", 3: "C", 4: "D"}[c]
    return {"answer": key, "computed": "layout=%s, between=%d" % (_row_str(seat), c)}


def _row_str(seat):
    return " ".join(name for name, _ in sorted(seat.items(), key=lambda kv: kv[1]))


# -------------------------------------------------- two-row puzzle questions


def q_f3c11_017():
    # Puzzle C, row 1: persons between B and C.
    col1, _ = puzzle_C()
    c = abs(col1["B"] - col1["C"]) - 1
    key = {1: "A", 2: "B", 3: "C", 0: "D"}[c]
    return {"answer": key, "computed": c}


def q_f3c11_044():
    # Puzzle C, row 2: persons between P and S.
    _, col2 = puzzle_C()
    c = abs(col2["P"] - col2["S"]) - 1
    key = {3: "A", 1: "B", 2: "C", 4: "D"}[c]
    return {"answer": key, "computed": c}


# --------------------------------------------------- circle puzzle questions


def q_f3c11_019():
    # Puzzle D: persons between A and B counted clockwise from A.
    seat = puzzle_D()
    c = between_cw(seat, "A", "B", 8)
    key = {4: "A", 3: "B", 2: "C", 5: "D"}[c]
    return {"answer": key, "computed": "order=%s, between=%d" % (_circle_str(seat), c)}


def q_f3c11_040():
    # Puzzle D: persons between E and G counted clockwise from E.
    seat = puzzle_D()
    c = between_cw(seat, "E", "G", 8)
    key = {4: "A", 6: "B", 5: "C", 3: "D"}[c]
    return {"answer": key, "computed": "order=%s, between=%d" % (_circle_str(seat), c)}


def _circle_str(seat):
    return " ".join(name for name, _ in sorted(seat.items(), key=lambda kv: kv[1]))


def q_f3c11_021():
    # Circle of 8 facing centre, X and Y exactly opposite: strictly between on
    # either arc = n/2 - 1.
    n = 8
    c = n // 2 - 1
    key = {3: "A", 4: "B", 2: "C", 6: "D"}[c]
    return {"answer": key, "computed": c}


def q_f3c11_046():
    # Circle of 12 facing centre, two persons exactly opposite: between on one
    # arc = n/2 - 1.
    n = 12
    c = n // 2 - 1
    key = {6: "A", 5: "B", 7: "C", 4: "D"}[c]
    return {"answer": key, "computed": c}


# ------------------------------------------------- facing-direction counting


def q_f3c11_023():
    # Eight persons around a circle; P, R, T and V face outward, the rest face
    # the centre. How many face the centre?
    everyone = ["P", "Q", "R", "S", "T", "U", "V", "W"]
    outward = ["P", "R", "T", "V"]
    centre = [x for x in everyone if x not in outward]
    c = len(centre)
    key = {5: "A", 3: "B", 4: "C", 8: "D"}[c]
    return {"answer": key, "computed": c}


# ------------------------------------------------------- grid (classroom)


def q_f3c11_031():
    # 3x3 classroom grid, all facing the front. The centre student is in row 2;
    # strictly in front of her is the whole of row 1 = 3 students.
    cols = 3
    rows_in_front = 1          # only row 1 is ahead of the centre (row 2)
    c = rows_in_front * cols
    key = {2: "A", 3: "B", 6: "C", 4: "D"}[c]
    return {"answer": key, "computed": c}
