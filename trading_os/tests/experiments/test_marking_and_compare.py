"""Marking (``is_marked``) + the multi-run family/baseline comparison report.

Covers: the tiny additive migration for pre-existing registries, the
mark/unset toggle, ``--families`` glob selection, known-answer delta
arithmetic in ``compare_runs``/``to_markdown_table``, and the
default-baseline-is-latest-marked rule.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from sqlmodel import Session, select
from typer.testing import CliRunner

from tradingos.cli import main as cli_main
from tradingos.config.settings import Settings
from tradingos.core.errors import DataError
from tradingos.experiments.db import get_engine, session_scope
from tradingos.experiments.leaderboard import (
    compare_runs,
    get_run,
    latest_marked_run,
    mark_run,
    to_markdown_table,
)
from tradingos.experiments.models import ExperimentRun

runner = CliRunner()


def _run(
    *,
    family: str,
    variant_name: str,
    finished_at: datetime,
    sharpe: float | None,
    max_drawdown: float | None,
    n_trades: float | None,
    total_costs_pct: float | None,
    final_equity: float | None,
    metrics: dict[str, Any] | None = None,
    capital: float = 1_000_000.0,
    status: str = "done",
    is_marked: bool = False,
) -> ExperimentRun:
    """A synthetic ExperimentRun row with sane defaults for unused fields."""
    return ExperimentRun(
        family=family,
        variant_name=variant_name,
        config_hash="hash-" + variant_name,
        config_json=json.dumps({"capital": capital}),
        overrides_json="{}",
        code_git_hash="deadbeef",
        snapshot_id="snap1",
        engine="event",
        status=status,
        started_at=finished_at,
        finished_at=finished_at,
        artifacts_path=f"/tmp/{family}/{variant_name}",
        is_holdout=False,
        sharpe=sharpe,
        max_drawdown=max_drawdown,
        n_trades=n_trades,
        total_costs_pct=total_costs_pct,
        final_equity=final_equity,
        metrics_json=json.dumps(metrics or {}),
        is_marked=is_marked,
    )


# --------------------------------------------------------------------------- #
# mark / unset                                                                #
# --------------------------------------------------------------------------- #
def test_mark_then_unset_toggles_flag(exp_settings: Settings) -> None:
    with session_scope(exp_settings) as session:
        row = _run(
            family="fam",
            variant_name="v1",
            finished_at=datetime(2024, 1, 1),
            sharpe=1.0,
            max_drawdown=-0.1,
            n_trades=10,
            total_costs_pct=0.01,
            final_equity=1_100_000,
        )
        session.add(row)
        session.flush()
        run_id = row.id
    assert run_id is not None

    marked = mark_run(run_id, exp_settings, marked=True)
    assert marked.is_marked is True

    with Session(get_engine(exp_settings)) as session:
        persisted = session.get(ExperimentRun, run_id)
        assert persisted is not None
        assert persisted.is_marked is True

    unmarked = mark_run(run_id, exp_settings, marked=False)
    assert unmarked.is_marked is False

    with Session(get_engine(exp_settings)) as session:
        persisted = session.get(ExperimentRun, run_id)
        assert persisted is not None
        assert persisted.is_marked is False


def test_mark_unknown_run_raises(exp_settings: Settings) -> None:
    with pytest.raises(DataError):
        mark_run(9999, exp_settings)


def test_cli_mark_and_unset(cli_env: tuple[Settings, Path]) -> None:
    settings, yaml_path = cli_env
    res_run = runner.invoke(
        cli_main.app,
        ["experiments", "run", str(yaml_path), "--parallel", "1", "--holdout-years", "0.5"],
    )
    assert res_run.exit_code == 0, res_run.output

    res_mark = runner.invoke(cli_main.app, ["experiments", "mark", "1"])
    assert res_mark.exit_code == 0, res_mark.output
    assert "marked" in res_mark.output
    assert get_run(1, settings).is_marked is True

    res_unset = runner.invoke(cli_main.app, ["experiments", "mark", "1", "--unset"])
    assert res_unset.exit_code == 0, res_unset.output
    assert "unmarked" in res_unset.output
    assert get_run(1, settings).is_marked is False


# --------------------------------------------------------------------------- #
# migration: pre-existing registry file lacking is_marked                     #
# --------------------------------------------------------------------------- #
def test_migration_adds_is_marked_column_and_preserves_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.sqlite"

    # Hand-build the PRE-MIGRATION schema (mirrors the real on-disk shape:
    # every ExperimentRun column except is_marked), then insert one row via
    # raw SQL — exactly the "DB created without the column" scenario.
    con = sqlite3.connect(db_path)
    con.execute(
        """
        CREATE TABLE experimentrun (
            id INTEGER PRIMARY KEY,
            family VARCHAR NOT NULL,
            variant_name VARCHAR NOT NULL,
            config_hash VARCHAR NOT NULL,
            config_json VARCHAR NOT NULL,
            overrides_json VARCHAR NOT NULL,
            code_git_hash VARCHAR NOT NULL,
            snapshot_id VARCHAR NOT NULL,
            engine VARCHAR NOT NULL,
            status VARCHAR NOT NULL,
            error VARCHAR,
            started_at DATETIME NOT NULL,
            finished_at DATETIME NOT NULL,
            artifacts_path VARCHAR NOT NULL,
            is_holdout BOOLEAN NOT NULL,
            train_end DATE,
            sharpe FLOAT,
            cagr FLOAT,
            max_drawdown FLOAT,
            calmar FLOAT,
            vol FLOAT,
            total_costs_pct FLOAT,
            final_equity FLOAT,
            n_trades FLOAT,
            n_bars INTEGER,
            ret_skew FLOAT,
            ret_kurt FLOAT,
            metrics_json VARCHAR NOT NULL,
            warnings_json VARCHAR NOT NULL DEFAULT '[]'
        )
        """
    )
    con.execute(
        """
        INSERT INTO experimentrun (
            family, variant_name, config_hash, config_json, overrides_json,
            code_git_hash, snapshot_id, engine, status, started_at, finished_at,
            artifacts_path, is_holdout, sharpe, metrics_json
        ) VALUES (
            'legacy_fam', 'legacy_v1', 'h1', '{}', '{}',
            'gh1', 'snap1', 'event', 'done', '2024-01-01 00:00:00', '2024-01-01 00:00:00',
            '/tmp/legacy', 0, 1.23, '{}'
        )
        """
    )
    con.commit()
    con.close()

    settings = Settings(
        data_dir=tmp_path / "data", artifacts_dir=tmp_path, _env_file=None
    )
    # experiments_db_path is artifacts_dir / "experiments.sqlite"; point the
    # legacy file at exactly that path.
    (tmp_path / "experiments.sqlite").unlink(missing_ok=True)
    db_path.rename(tmp_path / "experiments.sqlite")

    # Opening the engine must run the additive migration without touching data.
    eng = get_engine(settings)
    with eng.connect() as conn:
        cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(experimentrun)")}
    assert "is_marked" in cols

    with Session(eng) as session:
        rows = list(session.exec(select(ExperimentRun)).all())
    assert len(rows) == 1
    assert rows[0].family == "legacy_fam"
    assert rows[0].variant_name == "legacy_v1"
    assert rows[0].sharpe == pytest.approx(1.23)
    assert rows[0].is_marked is False  # backfilled default, not lost/rewritten

    # Idempotent: opening again (already-migrated schema) must not error or
    # touch the row.
    eng2 = get_engine(settings)
    with Session(eng2) as session:
        rows2 = list(session.exec(select(ExperimentRun)).all())
    assert len(rows2) == 1


# --------------------------------------------------------------------------- #
# compare_runs: family glob + known-answer delta arithmetic                   #
# --------------------------------------------------------------------------- #
@pytest.fixture()
def compare_settings(exp_settings: Settings) -> Settings:
    """Three synthetic 'done' runs: a marked baseline + a candidate under the
    same family glob, plus a distractor in an unrelated family."""
    with session_scope(exp_settings) as session:
        baseline = _run(
            family="adhoc_b2_baseline",
            variant_name="base",
            finished_at=datetime(2024, 1, 1),
            sharpe=1.0,
            max_drawdown=-0.10,
            n_trades=50,
            total_costs_pct=0.01,
            final_equity=1_100_000,
            metrics={"total_return": 0.10, "max_drawdown": -0.10},
            is_marked=True,
        )
        candidate = _run(
            family="adhoc_b2_v2",
            variant_name="v2",
            finished_at=datetime(2024, 2, 1),
            sharpe=1.5,
            max_drawdown=-0.08,
            n_trades=40,
            total_costs_pct=0.008,
            final_equity=1_200_000,
            metrics={"total_return": 0.20, "max_drawdown": -0.08},
        )
        # fallback path: no total_return in metrics_json -> derived from
        # final_equity / capital (config_json capital = 1_000_000).
        fallback = _run(
            family="adhoc_b2_v3",
            variant_name="v3",
            finished_at=datetime(2024, 3, 1),
            sharpe=2.0,
            max_drawdown=-0.05,
            n_trades=30,
            total_costs_pct=0.006,
            final_equity=1_300_000,
            metrics={"max_drawdown": -0.05},  # total_return deliberately absent
        )
        distractor = _run(
            family="other_family",
            variant_name="x",
            finished_at=datetime(2024, 2, 1),
            sharpe=0.5,
            max_drawdown=-0.30,
            n_trades=5,
            total_costs_pct=0.02,
            final_equity=900_000,
            metrics={"total_return": -0.10, "max_drawdown": -0.30},
        )
        session.add_all([baseline, candidate, fallback, distractor])
    return exp_settings


def test_latest_marked_run_is_default_baseline(compare_settings: Settings) -> None:
    row = latest_marked_run(compare_settings)
    assert row is not None
    assert row.variant_name == "base"


def test_compare_runs_family_glob_excludes_other_families(
    compare_settings: Settings,
) -> None:
    board = compare_runs(compare_settings, families="adhoc_b2*")
    assert set(board["family"]) == {"adhoc_b2_baseline", "adhoc_b2_v2", "adhoc_b2_v3"}
    assert "other_family" not in set(board["family"])


def test_compare_runs_known_answer_deltas_vs_default_baseline(
    compare_settings: Settings,
) -> None:
    board = compare_runs(compare_settings, families="adhoc_b2*")
    board = board.set_index("family")

    base = board.loc["adhoc_b2_baseline"]
    assert bool(base["is_baseline"]) is True
    assert base["net_return_pct"] == pytest.approx(10.0)
    assert base["max_drawdown_pct"] == pytest.approx(-10.0)
    assert base["delta_net_pp"] == pytest.approx(0.0)
    assert base["delta_dd_pp"] == pytest.approx(0.0)
    assert base["delta_sharpe"] == pytest.approx(0.0)
    assert "(baseline)" in base["variant_name"]

    v2 = board.loc["adhoc_b2_v2"]
    assert v2["net_return_pct"] == pytest.approx(20.0)
    assert v2["max_drawdown_pct"] == pytest.approx(-8.0)
    assert v2["delta_net_pp"] == pytest.approx(10.0)  # 20.0 - 10.0
    assert v2["delta_dd_pp"] == pytest.approx(2.0)  # -8.0 - (-10.0)
    assert v2["delta_sharpe"] == pytest.approx(0.5)  # 1.5 - 1.0

    # fallback path: total_return absent -> final_equity/capital - 1
    # = 1_300_000 / 1_000_000 - 1 = 0.30 -> 30.0 pp
    v3 = board.loc["adhoc_b2_v3"]
    assert v3["net_return_pct"] == pytest.approx(30.0)
    assert v3["delta_net_pp"] == pytest.approx(20.0)  # 30.0 - 10.0


def test_compare_runs_explicit_baseline_overrides_marked(
    compare_settings: Settings,
) -> None:
    with session_scope(compare_settings) as session:
        v2_id = session.exec(
            select(ExperimentRun).where(ExperimentRun.variant_name == "v2")
        ).one().id

    board = compare_runs(compare_settings, families="adhoc_b2*", baseline=v2_id)
    board = board.set_index("family")
    assert bool(board.loc["adhoc_b2_v2"]["is_baseline"]) is True
    assert bool(board.loc["adhoc_b2_baseline"]["is_baseline"]) is False
    # baseline is now v2 (net 20.0); the marked-baseline row's delta is vs v2
    assert board.loc["adhoc_b2_baseline"]["delta_net_pp"] == pytest.approx(-10.0)


def test_compare_runs_baseline_included_even_outside_family_glob(
    compare_settings: Settings,
) -> None:
    with session_scope(compare_settings) as session:
        other_id = session.exec(
            select(ExperimentRun).where(ExperimentRun.family == "other_family")
        ).one().id

    board = compare_runs(compare_settings, families="adhoc_b2*", baseline=other_id)
    assert "other_family" in set(board["family"])  # baseline forced in


def test_compare_runs_no_baseline_gives_nan_deltas(exp_settings: Settings) -> None:
    with session_scope(exp_settings) as session:
        session.add(
            _run(
                family="fam",
                variant_name="solo",
                finished_at=datetime(2024, 1, 1),
                sharpe=1.0,
                max_drawdown=-0.1,
                n_trades=10,
                total_costs_pct=0.01,
                final_equity=1_100_000,
                metrics={"total_return": 0.10},
            )
        )
    board = compare_runs(exp_settings)
    assert len(board) == 1
    import math

    assert math.isnan(board.iloc[0]["delta_net_pp"])


def test_to_markdown_table_contains_expected_deltas(compare_settings: Settings) -> None:
    board = compare_runs(compare_settings, families="adhoc_b2*")
    md = to_markdown_table(board)

    assert md.startswith("| id | family |")
    assert "(baseline)" in md
    # known-answer cells from the arithmetic test above
    assert "20.00" in md  # v2 net_return_pct
    assert "10.00" in md  # delta_net_pp for v2 (and base net_return_pct)
    assert "0.50" in md  # delta_sharpe for v2


def test_to_markdown_table_empty_board() -> None:
    import pandas as pd

    assert to_markdown_table(pd.DataFrame(columns=["id"])) == "(no runs to compare)"


# --------------------------------------------------------------------------- #
# CLI: compare --families/--baseline/--markdown, legacy mode still works      #
# --------------------------------------------------------------------------- #
def test_cli_compare_markdown_with_families_and_baseline(
    cli_env: tuple[Settings, Path],
) -> None:
    settings, yaml_path = cli_env
    res_run = runner.invoke(
        cli_main.app,
        ["experiments", "run", str(yaml_path), "--parallel", "1", "--holdout-years", "0.5"],
    )
    assert res_run.exit_code == 0, res_run.output

    res_mark = runner.invoke(cli_main.app, ["experiments", "mark", "1"])
    assert res_mark.exit_code == 0, res_mark.output

    res_cmp = runner.invoke(
        cli_main.app,
        ["experiments", "compare", "--families", "cli_fam*", "--markdown"],
    )
    assert res_cmp.exit_code == 0, res_cmp.output
    assert "(baseline)" in res_cmp.output
    assert "delta_net_pp" in res_cmp.output

    res_plain = runner.invoke(
        cli_main.app, ["experiments", "compare", "--families", "cli_fam*"]
    )
    assert res_plain.exit_code == 0, res_plain.output
    assert "delta_net_pp" in res_plain.output


def test_cli_compare_rejects_mixed_legacy_and_multi_mode(
    cli_env: tuple[Settings, Path],
) -> None:
    settings, yaml_path = cli_env
    res_run = runner.invoke(
        cli_main.app,
        ["experiments", "run", str(yaml_path), "--parallel", "1", "--holdout-years", "0.5"],
    )
    assert res_run.exit_code == 0, res_run.output

    res = runner.invoke(
        cli_main.app,
        ["experiments", "compare", "1", "2", "--families", "cli_fam*"],
    )
    assert res.exit_code != 0
    assert "error:" in res.output
