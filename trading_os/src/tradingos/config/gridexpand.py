"""Parameter-grid expansion: GridSpec sweeps -> concrete StrategyConfigs.

A sweep maps DOTTED CONFIG PATHS to lists of values (see
`config.schemas.GridSpec`), e.g.::

    {"signals.mom.params.window": [126, 189, 252], "selection.n": [20, 25, 30]}

expands to the 9-combo cartesian product. Two addressing forms:

* ``signals.<signal_id>.<...>`` — addresses the SignalSpec whose ``id`` equals
  ``<signal_id>`` inside the ``signals`` list (list position is NOT stable
  across edits; the id is).
* any other dotted path — walks nested config mappings key by key.

Every expanded combo is re-validated through the full pydantic model, so a
sweep can never produce a config that hand-written YAML could not (e.g. a
``selection.n`` above ``exit_rank`` raises exactly as it would when loaded
from a file). Invalid combos fail LOUDLY with the offending overrides named —
silently skipping them would misreport the number of trials, which the
Deflated Sharpe computation depends on.

Expansion order is deterministic (sweep keys sorted, itertools.product), so a
grid always yields the same variant numbering — variant names (and therefore
artifacts paths and run records) are reproducible across machines.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any

from tradingos.config.loader import parse_model
from tradingos.config.schemas import GridSpec, StrategyConfig
from tradingos.core.errors import ConfigError


@dataclass(frozen=True)
class GridVariant:
    """One expanded grid point: the concrete config plus the overrides that
    produced it (dotted path -> value), for run records and leaderboards."""

    config: StrategyConfig
    overrides: dict[str, Any] = field(default_factory=dict)


def _set_dotted(dump: dict[str, Any], path: str, value: Any) -> None:
    """Set ``path`` (dotted) to ``value`` inside a model_dump dict, in place."""
    parts = path.split(".")
    if not all(parts):
        raise ConfigError(f"malformed sweep path {path!r}")

    node: Any = dump
    walked: list[str] = []

    if parts[0] == "signals":
        if len(parts) < 3:
            raise ConfigError(
                f"sweep path {path!r} must be signals.<signal_id>.<field...>"
            )
        sig_id = parts[1]
        matches = [s for s in dump.get("signals", []) if s.get("id") == sig_id]
        if not matches:
            known = [s.get("id") for s in dump.get("signals", [])]
            raise ConfigError(
                f"sweep path {path!r}: no signal with id {sig_id!r} (have {known})"
            )
        node = matches[0]
        walked = ["signals", sig_id]
        parts = parts[2:]

    for key in parts[:-1]:
        walked.append(key)
        if not isinstance(node, dict) or key not in node:
            raise ConfigError(
                f"sweep path {path!r}: {'.'.join(walked)!r} does not exist in the config"
            )
        node = node[key]
    leaf = parts[-1]
    if not isinstance(node, dict) or leaf not in node:
        raise ConfigError(
            f"sweep path {path!r}: leaf {leaf!r} does not exist under "
            f"{'.'.join(walked) or '<root>'!r}"
        )
    node[leaf] = value


def expand_grid(base: StrategyConfig, sweep: dict[str, list[Any]]) -> list[GridVariant]:
    """Expand ``sweep`` against ``base`` into concrete, validated configs.

    Empty sweep -> the base config untouched (single variant, no rename).
    Otherwise each variant's ``name`` is ``<base.name>__<i:04d>`` in
    deterministic order so artifacts and run records never collide.
    """
    if not sweep:
        return [GridVariant(config=base, overrides={})]
    for path, values in sweep.items():
        if not isinstance(values, list) or not values:
            raise ConfigError(f"sweep values for {path!r} must be a non-empty list")

    keys = sorted(sweep)
    variants: list[GridVariant] = []
    for i, combo in enumerate(itertools.product(*(sweep[k] for k in keys))):
        overrides = dict(zip(keys, combo, strict=True))
        dump = base.model_dump(mode="python")
        for path, value in overrides.items():
            _set_dotted(dump, path, value)
        dump["name"] = f"{base.name}__{i:04d}"
        try:
            config = parse_model(StrategyConfig, dump, source=f"grid variant {overrides}")
        except ConfigError as exc:
            raise ConfigError(
                f"grid combo {overrides} produces an invalid config: {exc}"
            ) from exc
        variants.append(GridVariant(config=config, overrides=overrides))
    return variants


def expand_gridspec(grid: GridSpec) -> list[GridVariant]:
    """Expand a full GridSpec: applies ``grid.engine`` to every variant."""
    base = grid.base.model_copy(update={"engine": grid.engine})
    return expand_grid(base, grid.sweep)


__all__ = ["GridVariant", "expand_grid", "expand_gridspec"]
