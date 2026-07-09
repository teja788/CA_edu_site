"""Experiments module: SQLite run registry, parallel grid runner, leaderboard /
compare, and the train/holdout evaluation lockout.

Submodules are imported directly by callers (CLI, tests) so importing this
package stays cheap and workers can import ``runner`` without pulling the DB
layer.
"""

from __future__ import annotations
