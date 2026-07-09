# Adding a signal, factor, or filter

`strategies/registry.py` is the single namespace every strategy YAML draws
from. It holds two independent registries — **signals** (indicators that
produce a per-symbol numeric time series) and **filters** (regime/eligibility
gates that produce a per-symbol boolean time series) — but both share the
same lookup pattern, the same point-in-time (PIT) contract, and the same
look-ahead certification.

## The three signal tiers

One flat namespace, no prefixing needed in YAML — a strategy just says
`{name: rsi, params: {length: 14}}` and the registry resolves it regardless
of which tier it came from:

| Tier      | Lives in                          | Examples                                             |
|-----------|------------------------------------|-------------------------------------------------------|
| `builtin` | `strategies/signals/builtin.py`    | `pandas-ta` wrappers — RSI, MACD, ATR, Bollinger Bands, ADX, Stochastic, SuperTrend, Donchian, Keltner, OBV, ROC, CCI, VWAP, SMA/EMA, ... |
| `factor`  | `strategies/signals/factors.py`    | quant factors — returns over window, realized vol, risk-adjusted momentum, distance from 52-week high, return smoothness, beta, residual momentum vs index |
| `custom`  | `strategies/signals/custom/*.py`   | your own plugins, auto-discovered at startup |

Filters (`index_above_ma`, `min_price`, ...) live in `strategies/filters.py`
and are registered with `register_filter`, referenced by name in a
strategy's `filters:` list.

## Referencing a signal or filter from YAML

A `StrategyConfig` (see `config/schemas.py`) never imports Python signal
code — it only stores names + params:

```yaml
signals:
  - id: mom_12_1              # local id, used by score.weights
    name: risk_adjusted_momentum  # registry lookup key (case-insensitive)
    params: {window: 252, skip: 21, vol_window: 63}

score:
  type: weighted_zscore
  weights: {mom_12_1: 1.0}

filters:
  - name: index_above_ma
    params: {window: 200}
```

Loading a YAML (`config.loader.load_strategy`) never touches the registry —
signal/filter *names* are only resolved when a strategy actually runs. This
is what makes "new strategies are YAML + registered components only" true:
adding a strategy never requires touching engine code, and a typo in a
`name:` field is only caught when the engine calls `registry.get_signal(...)`
(a `ConfigError` naming the unknown signal and listing known ones).

## Adding a custom signal

1. Copy `strategies/signals/custom/_template.py` to a new file in the same
   directory **without** the leading underscore — e.g.
   `strategies/signals/custom/earnings_momentum.py`. Files starting with `_`
   are skipped by discovery, which is why the template itself never
   registers anything.
2. Decorate a `fn(df: pd.DataFrame, **params) -> pd.Series` with
   `@register_signal("your_name", description=..., tier="custom",
   **defaults)`. Every keyword after `tier=` becomes a default, overridable
   per-strategy via the YAML `params:` block (YAML wins on conflict; see
   `registry.compute_signal`, which merges `{**sig.defaults, **params}`).
3. That's it — `strategies.registry.ensure_discovered()` (called lazily by
   every `get_signal`/`get_filter`/`list_signals` call) imports every
   non-underscore module under `signals/custom/` once per process, so the
   new signal is immediately usable by name in strategy YAML, in **both**
   the vectorized and event-driven engines, with no other code changes.

## The point-in-time (PIT) contract

Every signal and filter must obey one rule: **the value at row t may depend
only on `df.loc[:t]`** — never on rows after t. This is not a convention,
it's a framework guarantee enforced two ways:

- **Precomputation + slicing**: `engine/dataview.py::SignalStore` computes a
  signal once over a symbol's *full* history for speed, then
  `DataView.signal_series` / `DataView.signal` slice the result down to
  `now`'s visibility cutoff before a strategy ever sees it. This only works
  if the signal itself never reached into the future while precomputing.
- **Automated certification**: `tests/strategies/test_lookahead_detector.py`
  iterates every signal in `registry.list_signals()` and every registered
  filter, computes each on a synthetic frame, then re-computes on that frame
  truncated at several probe timestamps and asserts the value at each probe
  point is identical whether or not later rows existed. **Any newly
  registered signal — builtin, factor, or a custom plugin you just added —
  is automatically covered by this suite the next time it runs.** You do
  not write a look-ahead test per signal; a signal that leaks the future
  makes the shared suite fail loudly, naming the offending signal.

Safe building blocks: `.rolling()`, `.expanding()`, `.ewm()`, `.shift(+n)`
(n >= 0). Unsafe: `.shift(-n)` (n > 0), any full-sample statistic
(`df["close"].mean()` broadcast to every row), `df.iloc[t+1:]`, or joining
against data dated after the current row.

## Cross-timeframe consumption

A signal can be computed on one timeframe and consumed by a strategy running
on another (e.g. a daily 200-DMA regime filter feeding an intraday
strategy). Two pieces make this work together:

- `config.schemas.SignalSpec.timeframe` (default `Timeframe.DAY`) — tags
  *which* timeframe's data a signal instance is computed on, independent of
  the strategy's own `timeframe:`.
- `engine.dataview.DataView.signal` / `.signal_series` accept a `timeframe=`
  argument. When it differs from the `DataView`'s primary timeframe, the
  lookup is routed to that timeframe's attached `SignalStore` (from the
  `aux` mapping passed to `DataView.__init__`) instead of the primary one.
  Each timeframe has its own visibility cutoff (`_visible_cutoff`), so a
  daily aux signal is only visible once its bar has actually closed (15:30
  IST), never mid-session — the same look-ahead guard applies regardless of
  which timeframe a value came from. Requesting a timeframe that was never
  attached to the run raises `DataError`, not a silent `None`.

## Caching

Signal values are precomputed once per `(symbol, signal name, params, data
snapshot)` key (`registry.signal_cache_key`, keyed via a stable
`json.dumps(..., sort_keys=True)` hash) and stored in `SignalStore`. A
100-combo parameter grid that shares the same signal+params across many
strategy variants never recomputes it — this is why signal functions should
be pure functions of `(df, params)` with no hidden state.
