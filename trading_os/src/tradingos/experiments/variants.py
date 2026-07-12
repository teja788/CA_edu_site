"""Generic strategy-variant harness — one command per hypothesis.

Replaces the ~180-line copy-pasted adhoc batch scripts (``scripts/adhoc/
batch1_m2_improvements.py``, ``batch2_m2_overlays.py``) with a single library
function plus a ``platform experiments run-variants`` command. Given a base
:class:`StrategyConfig` and a mapping of variant name -> flat dotted-path
override dict, :func:`run_variants`:

* builds and RE-VALIDATES each variant's config by applying the overrides onto
  a dump of the base and reconstructing a ``StrategyConfig`` (so an illegal
  combo fails LOUDLY for that variant only — recorded as ``status="error"`` —
  without aborting the batch, exactly as the grid runner does per variant);
* loads market data ONCE for the whole batch — the union of every variant's
  universe pool, every filter/regime ``symbol`` param, and every
  ``SignalSpec.benchmark``;
* per variant runs the recorded engine, computes metrics, writes the four
  adhoc artifact files (``net_equity_curve.csv``, ``trades.csv``,
  ``per_stock_pnl.csv``, ``summary.json``) under
  ``artifacts_dir/adhoc/{family}/<ts>/``, registers an ``ExperimentRun`` row
  (owner hard rule: persist EVERY strategy run), and prints one JSON line; and
* finally writes ``{family_prefix}_comparison_<ts>.json`` across all variants
  and returns the per-variant stats list.

The dynamic traded-value universe, ``regime`` / ``vol_target`` overlays and
``SignalSpec.benchmark`` are all just config, so they flow through the override
mechanism and the data-loading union transparently — no special-casing here.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

import pandas as pd
from pydantic import BaseModel, ValidationError

from tradingos.config.gridexpand import _set_dotted
from tradingos.config.schemas import StrategyConfig
from tradingos.config.settings import Settings
from tradingos.core.errors import ConfigError, TradingOSError
from tradingos.core.logging import get_logger
from tradingos.core.models import Timeframe
from tradingos.core.timeutils import now_ist
from tradingos.engine.dataview import MarketData
from tradingos.experiments.runner import (
    _opt,
    _skew_kurt,
    code_git_hash,
    make_engine,
    make_universe_resolver,
)

logger = get_logger(__name__)


# --------------------------------------------------------------------------- #
# Dotted-path override application                                             #
# --------------------------------------------------------------------------- #
def _to_plain(value: Any) -> Any:
    """Recursively convert pydantic models to plain dicts so an override value
    can be dropped into a ``model_dump`` dict and re-validated. Scalars, lists
    and dicts pass through (their members are converted too)."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="python")
    if isinstance(value, (list, tuple)):
        return [_to_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_plain(v) for k, v in value.items()}
    return value


def _apply_override(dump: dict[str, Any], path: str, value: Any) -> None:
    """Set dotted ``path`` to ``value`` inside a ``model_dump`` dict, in place.

    Two addressing forms (mirrors the grid sweep addressing):

    * ``signals.<signal_id>.<field...>`` — delegates to the grid runner's
      by-id signal addressing (list position is not stable; the id is).
    * any other dotted path — walks nested config mappings key by key. An
      optional spec that is currently ``None`` (e.g. ``score``, ``regime``,
      ``vol_target``) is opened up to a fresh mapping so a nested field can be
      set on it; a single-segment path replaces a whole top-level field (e.g.
      ``signals``, ``regime``, ``capital``). A path that names a key the config
      does not have raises ``ConfigError`` (a silent no-op would misreport what
      the variant actually ran).
    """
    value = _to_plain(value)
    parts = path.split(".")
    if not all(parts):
        raise ConfigError(f"malformed override path {path!r}")

    # by-id signal addressing (reuse the grid runner's implementation).
    if parts[0] == "signals" and len(parts) >= 3:
        _set_dotted(dump, path, value)
        return

    node: Any = dump
    walked: list[str] = []
    for key in parts[:-1]:
        walked.append(key)
        if not isinstance(node, dict) or key not in node:
            raise ConfigError(
                f"override path {path!r}: {'.'.join(walked)!r} does not exist in the config"
            )
        if node[key] is None:
            node[key] = {}
        elif not isinstance(node[key], dict):
            raise ConfigError(
                f"override path {path!r}: cannot descend into {'.'.join(walked)!r} "
                "(not a mapping)"
            )
        node = node[key]

    leaf = parts[-1]
    if not isinstance(node, dict) or leaf not in node:
        raise ConfigError(
            f"override path {path!r}: leaf {leaf!r} does not exist under "
            f"{'.'.join(walked) or '<root>'!r}"
        )
    node[leaf] = value


def build_variant_config(
    base: StrategyConfig, name: str, overrides: dict[str, Any]
) -> StrategyConfig:
    """Apply ``overrides`` (dotted path -> value) onto ``base`` and RE-VALIDATE.

    The base is dumped, each override applied, ``name`` set, and a fresh
    ``StrategyConfig`` constructed from the merged dump so every pydantic
    validator reruns — an illegal combination (e.g. ``selection.n`` above
    ``exit_rank``, or a dynamic universe without a symbol pool) fails here
    exactly as hand-written YAML would.
    """
    dump = base.model_dump(mode="python")
    for path, value in overrides.items():
        _apply_override(dump, path, value)
    dump["name"] = name
    try:
        return StrategyConfig.model_validate(dump)
    except ValidationError as exc:
        raise ConfigError(f"variant {name!r} produced an invalid config:\n{exc}") from exc


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
def _max_drawdown(equity: pd.Series) -> float:
    """Peak-to-trough max drawdown of an equity curve (<= 0), 0 if empty.

    Matches the adhoc batch scripts' local helper so reproduced summaries are
    byte-for-byte comparable."""
    if len(equity) == 0:
        return 0.0
    peak = equity.cummax()
    return float((equity / peak - 1.0).min())


def _iso(d: date | None) -> str | None:
    return d.isoformat() if d is not None else None


def _symbols_for(config: StrategyConfig, store: Any, timeframe: Timeframe) -> set[str]:
    """Every symbol this config needs loaded: its universe pool (or every stored
    symbol when the pool is implicit) plus every filter/regime ``symbol`` param
    and every ``SignalSpec.benchmark`` — so a single load serves the batch."""
    load: set[str] = set(config.universe.symbols or [])
    if not load:
        load = set(store.symbols(timeframe))
    for fspec in config.filters:
        routed = fspec.params.get("symbol")
        if routed:
            load.add(str(routed))
    if config.regime is not None:
        load.add(config.regime.symbol)
    for sig in config.signals:
        if sig.benchmark:
            load.add(sig.benchmark)
    return load


def _kind(config: StrategyConfig) -> str:
    n = config.selection.n
    if config.universe.dynamic_top_n is not None:
        return f"portfolio top-{n}, dynamic top-{config.universe.dynamic_top_n}"
    return f"portfolio top-{n}"


def _run_one(
    cfg: StrategyConfig,
    variant_name: str,
    overrides: dict[str, Any],
    data: MarketData,
    settings: Settings,
    *,
    family_prefix: str,
    run_ts: Any,
    git_hash: str,
) -> dict[str, Any]:
    """Run one variant: engine -> metrics -> four artifact files -> DB row.

    Returns the summary stats dict (identical shape to the batch scripts')."""
    from tradingos.analytics.metrics import compute_metrics
    from tradingos.experiments.db import session_scope
    from tradingos.experiments.models import ExperimentRun

    family = f"adhoc_{variant_name}_{family_prefix}"
    run_dir = (
        settings.artifacts_dir / "adhoc" / family / run_ts.strftime("%Y-%m-%d_%H%M%S")
    )
    run_dir.mkdir(parents=True, exist_ok=True)

    started = now_ist()
    res = make_engine(cfg.engine).run(cfg, data, make_universe_resolver(settings))
    finished = now_ist()
    metrics = compute_metrics(res)

    capital = cfg.capital
    neq = res.equity.sort_index()
    npnl = float(neq.iloc[-1]) - capital
    gpnl = float(res.gross_equity.sort_index().iloc[-1]) - capital
    trades = pd.DataFrame(
        [
            {
                "symbol": t.symbol,
                "qty": t.qty,
                "entry_ts": t.entry_ts,
                "exit_ts": t.exit_ts,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "gross_pnl": round(t.gross_pnl, 0),
                "costs": round(t.costs, 0),
                "net_pnl": round(t.net_pnl, 0),
                "exit_reason": t.exit_reason,
            }
            for t in res.trades
        ]
    )
    stats = {
        "variant": variant_name,
        "kind": _kind(cfg),
        "net_return_pct": round(npnl / capital * 100, 1),
        "net_max_dd_pct": round(_max_drawdown(neq) * 100, 1),
        "total_trades": len(res.trades),
        "total_charges": round(gpnl - npnl, 0),
        "sharpe": metrics.get("sharpe"),
        "exit_reasons": (
            trades.exit_reason.value_counts().to_dict() if len(trades) else {}
        ),
    }

    # -- artifacts (the four adhoc files) --------------------------------
    neq.to_csv(run_dir / "net_equity_curve.csv")
    trades.to_csv(run_dir / "trades.csv", index=False)
    if len(trades):
        (
            trades.groupby("symbol")
            .agg(
                trades=("net_pnl", "size"),
                net_pnl=("net_pnl", "sum"),
                gross_pnl=("gross_pnl", "sum"),
                costs=("costs", "sum"),
            )
            .sort_values("net_pnl", ascending=False)
            .to_csv(run_dir / "per_stock_pnl.csv")
        )
    (run_dir / "summary.json").write_text(json.dumps(stats, indent=2, default=str))

    # -- persist the run (owner hard rule) -------------------------------
    returns = res.equity.pct_change().dropna()
    ret_skew, ret_kurt = _skew_kurt(returns)
    with session_scope(settings) as session:
        session.add(
            ExperimentRun(
                family=family,
                variant_name=variant_name,
                config_hash=cfg.config_hash(),
                config_json=json.dumps(cfg.model_dump(mode="json")),
                overrides_json=json.dumps(overrides, default=str),
                code_git_hash=git_hash,
                snapshot_id=data.snapshot_id,
                engine=cfg.engine.value,
                status="done",
                error=None,
                started_at=started,
                finished_at=finished,
                artifacts_path=str(run_dir),
                is_holdout=False,
                train_end=None,
                sharpe=_opt(metrics.get("sharpe")),
                cagr=_opt(metrics.get("cagr")),
                max_drawdown=_opt(metrics.get("max_drawdown")),
                calmar=_opt(metrics.get("calmar")),
                vol=_opt(metrics.get("vol")),
                total_costs_pct=_opt(metrics.get("total_costs_pct")),
                final_equity=_opt(metrics.get("final_equity")),
                n_trades=_opt(metrics.get("n_trades")),
                n_bars=int(len(returns)),
                ret_skew=_opt(ret_skew),
                ret_kurt=_opt(ret_kurt),
                metrics_json=json.dumps(metrics),
                warnings_json=json.dumps(list(res.warnings)),
            )
        )
    return stats


# --------------------------------------------------------------------------- #
# Public entry point                                                           #
# --------------------------------------------------------------------------- #
def run_variants(
    base: StrategyConfig,
    variants: dict[str, dict[str, Any]],
    settings: Settings,
    *,
    family_prefix: str,
    data: MarketData | None = None,
) -> list[dict[str, Any]]:
    """Run every variant of ``base`` and persist/print/return their stats.

    Parameters
    ----------
    base
        The baseline config; each variant is ``base`` with its overrides applied
        and re-validated.
    variants
        ``{variant_name: {dotted_path: value, ...}}``. An override may replace a
        whole top-level field (``"signals": [...]``) or set a nested one
        (``"selection.exit_rank": 50``, ``"score.weights": {...}``).
    settings
        Provides ``artifacts_dir`` and the experiments DB path.
    family_prefix
        Names the batch: each variant registers under family
        ``adhoc_{variant}_{family_prefix}`` and the comparison file is
        ``{family_prefix}_comparison_<ts>.json``.
    data
        Pre-loaded market data (tests / callers that already hold a frame). When
        ``None`` the union of symbols across all variants is loaded ONCE from a
        ``BarStore``.

    Returns the per-variant stats list (done variants carry the batch summary
    shape; a variant whose config is illegal or whose run raised carries
    ``{"variant", "status": "error", "message"}``).
    """
    run_ts = now_ist()
    git_hash = code_git_hash()

    # -- build + validate every variant up front (per-variant errors) -----
    built: dict[str, StrategyConfig] = {}
    build_errors: dict[str, str] = {}
    for name, overrides in variants.items():
        try:
            built[name] = build_variant_config(
                base, f"{family_prefix}_{name}", overrides
            )
        except TradingOSError as exc:
            build_errors[name] = str(exc)
            logger.warning("variant %s failed to build: %s", name, exc)

    # -- load market data ONCE for the whole batch ------------------------
    if data is None:
        from tradingos.data.store import BarStore

        store = BarStore(settings)
        timeframe = base.timeframe
        symbols: set[str] = set()
        for cfg in built.values():
            symbols.update(_symbols_for(cfg, store, timeframe))
        data = store.load_market_data(sorted(symbols), timeframe)

    # -- run every variant (in declared order) ----------------------------
    stats: list[dict[str, Any]] = []
    for name, overrides in variants.items():
        if name in build_errors:
            stat: dict[str, Any] = {
                "variant": name,
                "status": "error",
                "message": build_errors[name],
            }
        else:
            try:
                stat = _run_one(
                    built[name],
                    name,
                    overrides,
                    data,
                    settings,
                    family_prefix=family_prefix,
                    run_ts=run_ts,
                    git_hash=git_hash,
                )
            except Exception as exc:  # noqa: BLE001 — one bad variant must not kill the batch
                logger.warning("variant %s failed to run: %s", name, exc)
                stat = {
                    "variant": name,
                    "status": "error",
                    "message": str(exc) or exc.__class__.__name__,
                }
        stats.append(stat)
        print(json.dumps(stat, default=str), flush=True)

    # -- comparison file across all variants ------------------------------
    out = (
        settings.artifacts_dir
        / "adhoc"
        / f"{family_prefix}_comparison_{run_ts.strftime('%Y-%m-%d_%H%M%S')}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "run_at": run_ts.isoformat(timespec="seconds"),
                "family_prefix": family_prefix,
                "window": {"start": _iso(base.start), "end": _iso(base.end)},
                "n_variants": len(stats),
                "variants": stats,
            },
            indent=2,
            default=str,
        )
    )
    print(f"comparison -> {out}", flush=True)
    return stats


__all__ = ["run_variants", "build_variant_config"]
