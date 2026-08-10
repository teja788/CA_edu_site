"""Verifier for foundation/quantitative-aptitude/direction-sense-test.json (P3 Ch 10).

Every function recomputes its answer from the stem's own parameters. Nothing is
copied from the answer key: each computed value (a distance, a heading, or a
turning angle) is mapped to an option key through a dict of the four option
values, so a wrong key in the bank surfaces as a KeyError or as a mismatch the
runner reports.

Convention used throughout — the same one the notes draw on paper:
  * A walk lives on an integer grid with the start at (0, 0).
  * East adds to x, West subtracts; North adds to y, South subtracts.
  * The shortest distance from the start is sqrt(x^2 + y^2), returned as an
    exact int when x^2 + y^2 is a perfect square (every intended answer is a
    Pythagorean triple, so it always is) and as a float otherwise.
  * A `Walk` also carries a heading, so "turn left/right then walk forward"
    questions track facing and position separately. Left = 90 degrees
    anticlockwise, right = 90 degrees clockwise.
"""

from __future__ import annotations

import math

# Eight compass directions as unit(ish) grid vectors. Only cardinal moves are
# used for distances, so every finish point has integer coordinates.
DIRS = {
    "N": (0, 1),
    "S": (0, -1),
    "E": (1, 0),
    "W": (-1, 0),
    "NE": (1, 1),
    "NW": (-1, 1),
    "SE": (1, -1),
    "SW": (-1, -1),
}
VEC_TO_CARDINAL = {(0, 1): "N", (0, -1): "S", (1, 0): "E", (-1, 0): "W"}

# Clockwise order of the eight points, used for turning-angle questions.
CW8 = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def dist_from_origin(x, y):
    """Straight-line distance from (0, 0), exact int on a perfect square."""
    d2 = x * x + y * y
    r = math.isqrt(d2)
    return r if r * r == d2 else math.sqrt(d2)


def resultant_dir(x, y):
    """The eight-point compass direction of (x, y) seen from the origin."""
    sx = (x > 0) - (x < 0)
    sy = (y > 0) - (y < 0)
    if sx == 0 and sy == 0:
        return "origin"
    if sx == 0:
        return "N" if sy > 0 else "S"
    if sy == 0:
        return "E" if sx > 0 else "W"
    return ("N" if sy > 0 else "S") + ("E" if sx > 0 else "W")


def angle_cw(a, b):
    """Degrees turned clockwise to face b starting from a."""
    return ((CW8.index(b) - CW8.index(a)) % 8) * 45


def angle_acw(a, b):
    """Degrees turned anticlockwise to face b starting from a."""
    return ((CW8.index(a) - CW8.index(b)) % 8) * 45


class Walk:
    """A walker on the grid, tracking position (x, y) and heading."""

    def __init__(self, facing="N"):
        self.x = 0
        self.y = 0
        self.h = DIRS[facing]

    def go(self, direction, dist):
        """Move dist along an absolute cardinal direction."""
        dx, dy = DIRS[direction]
        self.x += dx * dist
        self.y += dy * dist
        return self

    def left(self):
        """Turn 90 degrees anticlockwise: (dx, dy) -> (-dy, dx)."""
        dx, dy = self.h
        self.h = (-dy, dx)
        return self

    def right(self):
        """Turn 90 degrees clockwise: (dx, dy) -> (dy, -dx)."""
        dx, dy = self.h
        self.h = (dy, -dx)
        return self

    def forward(self, dist):
        """Move dist along the current heading."""
        self.x += self.h[0] * dist
        self.y += self.h[1] * dist
        return self

    def dist(self):
        return dist_from_origin(self.x, self.y)

    def heading(self):
        return VEC_TO_CARDINAL[self.h]

    def dir_from_start(self):
        return resultant_dir(self.x, self.y)


# --------------------------------------------- S 1 the compass and its degrees


def q_f3c10_004():
    # Degrees turned clockwise from North to South-East.
    deg = angle_cw("N", "SE")
    key = {90: "A", 135: "B", 45: "C", 225: "D"}[deg]
    return {"answer": key, "computed": "%d degrees" % deg}


def q_f3c10_005():
    # Degrees turned anticlockwise from East to North.
    deg = angle_acw("E", "N")
    key = {270: "A", 180: "B", 90: "C", 45: "D"}[deg]
    return {"answer": key, "computed": "%d degrees" % deg}


# ---------------------------------- S 2-3 single- and multi-leg distance walks


def q_f3c10_006():
    d = Walk("E").forward(4).left().forward(3).dist()
    key = {7: "A", 1: "B", 5: "C", 12: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_007():
    d = Walk("N").forward(8).right().forward(6).dist()
    key = {14: "A", 10: "B", 2: "C", 48: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_008():
    d = Walk().go("W", 5).go("S", 12).dist()
    key = {17: "A", 7: "B", 13: "C", 60: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_009():
    d = Walk().go("S", 24).go("E", 7).dist()
    key = {31: "A", 25: "B", 17: "C", 168: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_010():
    d = Walk().go("E", 15).go("N", 8).dist()
    key = {23: "A", 7: "B", 17: "C", 120: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_011():
    d = Walk().go("N", 9).go("W", 12).dist()
    key = {21: "A", 15: "B", 3: "C", 108: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_012():
    w = Walk().go("E", 3).go("N", 4)
    pair = (w.dist(), w.dir_from_start())
    key = {(7, "NE"): "A", (5, "NE"): "B", (5, "SW"): "C", (1, "NE"): "D"}[pair]
    return {"answer": key, "computed": "%s m, %s" % pair}


def q_f3c10_013():
    d = Walk().go("E", 10).go("W", 4).dist()
    key = {14: "A", 6: "B", 40: "C", 4: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_014():
    d = Walk().go("E", 6).go("N", 8).go("W", 6).dist()
    key = {20: "A", 12: "B", 8: "C", 10: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_015():
    d = Walk().go("N", 10).go("E", 5).go("S", 10).dist()
    key = {25: "A", 5: "B", 15: "C", 20: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_016():
    d = Walk().go("N", 4).go("E", 4).go("S", 4).go("W", 4).dist()
    key = {16: "A", 8: "B", 4: "C", 0: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_017():
    d = Walk().go("E", 3).go("N", 4).go("E", 3).go("N", 4).dist()
    key = {14: "A", 10: "B", 7: "C", 100: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_018():
    d = Walk().go("S", 5).go("W", 12).go("N", 5).dist()
    key = {22: "A", 2: "B", 12: "C", 13: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_019():
    d = Walk().go("N", 10).go("E", 6).go("S", 2).dist()
    key = {18: "A", 10: "B", 4: "C", 14: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_020():
    d = Walk().go("E", 12).go("N", 9).go("S", 4).dist()
    key = {25: "A", 13: "B", 17: "C", 5: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_021():
    d = Walk().go("N", 15).go("E", 12).go("W", 4).dist()
    key = {31: "A", 23: "B", 17: "C", 7: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_022():
    d = Walk().go("E", 5).go("N", 12).go("E", 4).dist()
    key = {21: "A", 15: "B", 3: "C", 25: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_023():
    d = Walk().go("E", 24).go("W", 4).go("N", 21).dist()
    key = {49: "A", 41: "B", 29: "C", 45: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_024():
    d = Walk().go("S", 7).go("E", 24).dist()
    key = {31: "A", 17: "B", 25: "C", 168: "D"}[d]
    return {"answer": key, "computed": d}


# ------------------------------------------------------- S 4 turns and heading


def q_f3c10_029():
    h = Walk("E").right().right().right().heading()
    key = {"E": "A", "S": "B", "W": "C", "N": "D"}[h]
    return {"answer": key, "computed": "facing %s" % h}


def q_f3c10_030():
    w = Walk("N")
    for _ in range(5):
        w.right()
    key = {"N": "A", "E": "B", "S": "C", "W": "D"}[w.heading()]
    return {"answer": key, "computed": "facing %s" % w.heading()}


def q_f3c10_032():
    # 270 degrees clockwise equals this many degrees anticlockwise.
    deg = (360 - 270) % 360
    key = {270: "A", 180: "B", 90: "C", 360: "D"}[deg]
    return {"answer": key, "computed": "%d degrees anticlockwise" % deg}


def q_f3c10_033():
    d = Walk("N").forward(12).right().forward(5).dist()
    key = {17: "A", 7: "B", 13: "C", 60: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_034():
    d = Walk("N").forward(6).right().forward(8).right().forward(6).dist()
    key = {20: "A", 8: "B", 12: "C", 10: "D"}[d]
    return {"answer": key, "computed": d}


# ------------------------------- S 6 opposite-direction gap between two people


def q_f3c10_042():
    # One runner at 6 North, the other at 8 South of the same start.
    ax, ay = 0, 6
    bx, by = 0, -8
    d = dist_from_origin(ax - bx, ay - by)
    key = {2: "A", 14: "B", 10: "C", 48: "D"}[d]
    return {"answer": key, "computed": d}


# --------------------------------------------- S 7 harder mixed walks


def q_f3c10_048():
    d = Walk().go("N", 26).go("E", 10).go("S", 2).go("W", 3).dist()
    key = {41: "A", 25: "B", 33: "C", 17: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_049():
    d = Walk("E").forward(15).left().forward(13).left().forward(3).left().forward(8).dist()
    key = {39: "A", 13: "B", 17: "C", 7: "D"}[d]
    return {"answer": key, "computed": d}


def q_f3c10_050():
    w = Walk().go("E", 5).go("N", 15).go("E", 4).go("S", 3)
    pair = (w.dist(), w.dir_from_start())
    key = {(21, "NE"): "A", (15, "NE"): "B", (15, "SW"): "C", (3, "NE"): "D"}[pair]
    return {"answer": key, "computed": "%s m, %s" % pair}
