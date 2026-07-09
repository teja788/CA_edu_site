"""Template for a user-plugin signal.

Every module in `strategies/signals/custom/` whose filename does NOT start
with `_` is auto-discovered and imported at process startup (the first call
to `strategies.registry.ensure_discovered`, which every registry lookup
triggers lazily). So a new indicator is exactly one file: copy this template,
decorate a function with `@register_signal(...)`, and it registers itself —
immediately usable by name in strategy YAML (`signals: [{id: ..., name:
"my_indicator", params: {...}}]`), in both the vectorized and event-driven
engines, with zero other code changes.

This file itself is named `_template.py` (leading underscore) and is
therefore SKIPPED by discovery — copying it as-is, un-renamed, is a safe
no-op and will NOT register `my_indicator`.

To add a new signal:

  1. Copy this file to `strategies/signals/custom/<your_signal_name>.py`
     — a real filename, WITHOUT the leading underscore.
  2. Rename the function and the string passed to `register_signal(...)`
     (that string, lowercased, is the name strategies reference in YAML).
  3. Implement the point-in-time (PIT) rule: the value at row t of the
     returned Series may depend ONLY on `df` at rows <= t. Concretely:
       - OK: `df["close"].rolling(window).mean()`, `.expanding()`, `.ewm()`,
         `.shift(+n)` (n >= 0, looks backward), anything computed row-by-row
         from the past.
       - NOT OK: `.shift(-n)` (n > 0, reaches into the future),
         `df["close"].mean()` / `.max()` broadcast to every row (a
         full-sample statistic "sees" rows after t), slicing with
         `df.iloc[t + 1:]`, or joining against data dated after the row.
  4. Every custom signal is automatically covered by the look-ahead
     detector test suite (`tests/strategies/test_lookahead_detector.py`) the
     next time it runs — no test-writing required. A signal that violates
     the PIT rule will make that suite FAIL LOUDLY, naming the signal; it is
     not a silent bug.

See also `docs/adding_signals.md` for the full registry contract (tiers,
defaults, caching, cross-timeframe use).
"""

from __future__ import annotations

import pandas as pd

from tradingos.strategies.registry import register_signal


@register_signal(
    "my_indicator",  # <-- rename: this is the name used in strategy YAML
    description="One-line description of what this indicator measures.",
    tier="custom",
    window=20,  # <-- every keyword here is a default; a YAML `params:` block overrides it
)
def my_indicator(df: pd.DataFrame, **params) -> pd.Series:
    """fn(df, **params) -> pd.Series aligned to df.index.

    Args:
        df: one symbol's OHLCV frame — columns at least
            open/high/low/close/volume (plus optionally
            total_return_close), index a tz-naive IST DatetimeIndex,
            ascending, no duplicates.
        params: this signal's registered `defaults` merged with whatever the
            strategy YAML's `params:` block overrides (YAML wins on
            conflict). Read every value you need out of `params` — do not
            rely on Python default arguments here, since `compute_signal`
            always calls this function with the fully-merged dict as
            keywords.

    Returns:
        A pandas Series with the SAME length and index as `df`. Values are
        cast to float64 by the registry after this function returns.

    PIT rule (enforced by the look-ahead detector, not just convention):
    the value at row t must be computable from `df.loc[:t]` alone. The
    example below — a trailing rolling mean of close — is causal by
    construction, because a pandas `.rolling()` window ending at t never
    reads rows after t.
    """
    window = params["window"]
    return df["close"].rolling(window=window, min_periods=window).mean()
