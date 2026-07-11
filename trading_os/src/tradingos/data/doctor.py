"""Data-quality checks -- the engine behind the `platform data doctor` CLI.

`DataDoctor` runs a fixed set of deterministic checks over a symbol's raw
OHLCV bars and produces a `HealthReport` of `Finding`s. Everything here is
pure/read-only: it never mutates stored data, only reports on it.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Protocol

import polars as pl
from pydantic import BaseModel, Field

from tradingos.core.errors import DataError
from tradingos.core.logging import get_logger
from tradingos.core.models import Timeframe
from tradingos.core.timeutils import now_ist
from tradingos.data.calendar import NSECalendar

logger = get_logger(__name__)

# Rolling-window sizes for the volume-spike check. Daily: 60 trading days, per
# spec. Minute: approximated as 60 sessions' worth of one-minute bars (a full
# NSE session is 09:15-15:29, i.e. 375 one-minute bars) -- there is no spec
# for the "right" intraday window, this is a documented best-effort choice.
_MINUTE_BARS_PER_SESSION = 375
_VOLUME_WINDOW_BARS: dict[Timeframe, int] = {
    Timeframe.DAY: 60,
    Timeframe.MINUTE: 60 * _MINUTE_BARS_PER_SESSION,
}

_OUTLIER_RATIO = 0.40  # |close/prev_close - 1| > 40% => possible unadjusted corporate action
_VOLUME_SPIKE_MULTIPLE = 20.0  # volume > 20x rolling median
_ZERO_VOLUME_WARN_FRACTION = 0.05  # >5% of bars zero-volume => warn, else info
_STALE_TRADING_DAYS = 5
_PREVIEW_LIMIT = 5  # how many example dates/timestamps to inline in a message


class Finding(BaseModel):
    """One data-quality observation for a symbol/timeframe/check."""

    symbol: str
    timeframe: str
    check: str
    severity: Literal["info", "warn", "error"]
    message: str
    ts: datetime | None = None
    count: int = 1


class HealthReport(BaseModel):
    """Aggregate result of a `DataDoctor.run()` pass."""

    generated_at: datetime
    findings: list[Finding] = Field(default_factory=list)
    symbols_checked: int

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "warn"]

    def render(self) -> str:
        """Aligned plain-text report, findings grouped by symbol."""
        infos = len(self.findings) - len(self.errors) - len(self.warnings)
        lines: list[str] = [
            f"Data Health Report -- generated {self.generated_at.isoformat(sep=' ', timespec='seconds')}",
            f"symbols checked: {self.symbols_checked}  "
            f"errors: {len(self.errors)}  warnings: {len(self.warnings)}  info: {infos}",
            "",
        ]
        if not self.findings:
            lines.append("No findings. All checks passed.")
            return "\n".join(lines) + "\n"

        by_symbol: dict[str, list[Finding]] = {}
        for f in self.findings:
            by_symbol.setdefault(f.symbol, []).append(f)

        sev_rank = {"error": 0, "warn": 1, "info": 2}
        for symbol in sorted(by_symbol):
            rows = sorted(by_symbol[symbol], key=lambda f: (sev_rank[f.severity], f.check))
            sev_w = max(len(r.severity) for r in rows)
            check_w = max(len(r.check) for r in rows)
            lines.append(f"[{symbol}]")
            for r in rows:
                count_str = f"  (x{r.count})" if r.count > 1 else ""
                ts_str = f"  @ {r.ts.isoformat(sep=' ')}" if r.ts is not None else ""
                lines.append(
                    f"  {r.severity.upper():<{sev_w}}  {r.check:<{check_w}}  "
                    f"{r.message}{count_str}{ts_str}"
                )
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"


class BarStore(Protocol):
    """Pinned subset of the `tradingos.data.store` API `DataDoctor` needs.

    Defined here as a Protocol so `DataDoctor` can be constructed/tested
    against any object exposing these three methods, without importing the
    real store module (which is built in parallel).
    """

    def read_raw(self, symbol: str, timeframe: Timeframe) -> pl.DataFrame: ...

    def symbols(self, timeframe: Timeframe) -> list[str]: ...

    def last_ts(self, symbol: str, timeframe: Timeframe) -> datetime | None: ...


def _default_store() -> BarStore:
    # Imported lazily so this module doesn't hard-depend on the store module
    # at import time (it's being built in parallel and may not exist yet).
    from tradingos.data.store import BarStore as _RealBarStore  # type: ignore[import-not-found]

    return _RealBarStore()


class DataDoctor:
    """Runs data-quality checks over bars served by `store`."""

    def __init__(self, store: BarStore, calendar: NSECalendar | None = None) -> None:
        self.store = store
        self.calendar = calendar if calendar is not None else NSECalendar()

    # -- public API ----------------------------------------------------

    def run(
        self,
        timeframe: Timeframe,
        symbols: list[str] | None = None,
        *,
        today: date | None = None,
    ) -> HealthReport:
        syms = symbols if symbols is not None else self.store.symbols(timeframe)
        findings: list[Finding] = []
        for symbol in syms:
            findings.extend(self.check_symbol(symbol, timeframe, today=today))
        return HealthReport(generated_at=now_ist(), findings=findings, symbols_checked=len(syms))

    def check_symbol(
        self,
        symbol: str,
        timeframe: Timeframe,
        *,
        today: date | None = None,
    ) -> list[Finding]:
        today = today if today is not None else now_ist().date()
        try:
            df = self.store.read_raw(symbol, timeframe)
        except DataError as exc:
            # Unknown/never-synced symbol: report it, never crash the run.
            return [
                Finding(
                    symbol=symbol,
                    timeframe=timeframe.value,
                    check="no_data",
                    severity="error",
                    message=str(exc),
                )
            ]
        findings: list[Finding] = []

        if df.is_empty():
            findings.append(
                Finding(
                    symbol=symbol,
                    timeframe=timeframe.value,
                    check="no_data",
                    severity="warn",
                    message="no bars found",
                )
            )
            return findings

        df = df.sort("ts")

        findings.extend(self._check_duplicate_timestamps(symbol, timeframe, df))
        findings.extend(self._check_invalid_prices(symbol, timeframe, df))
        findings.extend(self._check_ohlc_consistency(symbol, timeframe, df))
        findings.extend(self._check_missing_trading_days(symbol, timeframe, df))
        findings.extend(self._check_minute_completeness(symbol, timeframe, df, today))
        findings.extend(self._check_extreme_outliers(symbol, timeframe, df))
        findings.extend(self._check_volume_anomalies(symbol, timeframe, df))
        findings.extend(self._check_staleness(symbol, timeframe, today))
        return findings

    # -- individual checks ----------------------------------------------

    @staticmethod
    def _check_duplicate_timestamps(
        symbol: str, timeframe: Timeframe, df: pl.DataFrame
    ) -> list[Finding]:
        n_unique = df.select(pl.col("ts").n_unique()).item()
        n_dupe_rows = df.height - n_unique
        if n_dupe_rows <= 0:
            return []
        dupe_ts = (
            df.group_by("ts")
            .agg(pl.len().alias("n"))
            .filter(pl.col("n") > 1)
            .sort("ts")
            .get_column("ts")
            .to_list()
        )
        return [
            Finding(
                symbol=symbol,
                timeframe=timeframe.value,
                check="duplicate_timestamps",
                severity="error",
                message=(
                    f"{n_dupe_rows} duplicate row(s) across {len(dupe_ts)} timestamp(s), "
                    f"first: {[str(t) for t in dupe_ts[:_PREVIEW_LIMIT]]}"
                ),
                ts=dupe_ts[0],
                count=n_dupe_rows,
            )
        ]

    @staticmethod
    def _check_invalid_prices(
        symbol: str, timeframe: Timeframe, df: pl.DataFrame
    ) -> list[Finding]:
        price_cols = ("open", "high", "low", "close")
        bad_mask = pl.any_horizontal(
            [pl.col(c).is_null() | (pl.col(c) <= 0) for c in price_cols]
        )
        bad = df.filter(bad_mask)
        if bad.is_empty():
            return []
        ts_list = bad.get_column("ts").to_list()
        return [
            Finding(
                symbol=symbol,
                timeframe=timeframe.value,
                check="invalid_price",
                severity="error",
                message=(
                    f"{bad.height} bar(s) with null/zero/negative open/high/low/close, "
                    f"first: {[str(t) for t in ts_list[:_PREVIEW_LIMIT]]}"
                ),
                ts=ts_list[0],
                count=bad.height,
            )
        ]

    @staticmethod
    def _check_ohlc_consistency(
        symbol: str, timeframe: Timeframe, df: pl.DataFrame
    ) -> list[Finding]:
        bad_mask = (
            (pl.col("high") < pl.col("low"))
            | (pl.col("open") < pl.col("low"))
            | (pl.col("open") > pl.col("high"))
            | (pl.col("close") < pl.col("low"))
            | (pl.col("close") > pl.col("high"))
        )
        bad = df.filter(bad_mask)
        if bad.is_empty():
            return []
        ts_list = bad.get_column("ts").to_list()
        return [
            Finding(
                symbol=symbol,
                timeframe=timeframe.value,
                check="ohlc_consistency",
                severity="error",
                message=(
                    f"{bad.height} bar(s) with high<low or open/close outside [low, high], "
                    f"first: {[str(t) for t in ts_list[:_PREVIEW_LIMIT]]}"
                ),
                ts=ts_list[0],
                count=bad.height,
            )
        ]

    def _check_missing_trading_days(
        self, symbol: str, timeframe: Timeframe, df: pl.DataFrame
    ) -> list[Finding]:
        present_dates = set(df.select(pl.col("ts").dt.date()).to_series().to_list())
        first_date, last_date = min(present_dates), max(present_dates)
        expected = set(self.calendar.trading_days(first_date, last_date))
        missing = sorted(expected - present_dates)
        if not missing:
            return []
        # Outside the calendar's holiday coverage, "expected" degrades to
        # weekday-only logic, so a real holiday looks like a missing bar.
        # Those are demoted to warnings (with the reason) instead of raising
        # false errors; genuinely covered years still error.
        covered_missing = [d for d in missing if self.calendar.covers(d.year)]
        uncovered_missing = [d for d in missing if not self.calendar.covers(d.year)]
        findings: list[Finding] = []
        if covered_missing:
            findings.append(
                Finding(
                    symbol=symbol,
                    timeframe=timeframe.value,
                    check="missing_trading_days",
                    severity="error",
                    message=(
                        f"{len(covered_missing)} trading day(s) missing between {first_date} and "
                        f"{last_date}, first: {[str(d) for d in covered_missing[:_PREVIEW_LIMIT]]}"
                    ),
                    ts=datetime.combine(covered_missing[0], datetime.min.time()),
                    count=len(covered_missing),
                )
            )
        if uncovered_missing:
            findings.append(
                Finding(
                    symbol=symbol,
                    timeframe=timeframe.value,
                    check="missing_trading_days",
                    severity="warn",
                    message=(
                        f"{len(uncovered_missing)} weekday(s) without bars fall OUTSIDE the "
                        "calendar's holiday coverage (weekday-only expectations; some may be "
                        "real NSE holidays) -- extend coverage via nse_holidays.csv to check "
                        f"them properly, first: "
                        f"{[str(d) for d in uncovered_missing[:_PREVIEW_LIMIT]]}"
                    ),
                    ts=datetime.combine(uncovered_missing[0], datetime.min.time()),
                    count=len(uncovered_missing),
                )
            )
        return findings

    def _check_minute_completeness(
        self, symbol: str, timeframe: Timeframe, df: pl.DataFrame, today: date
    ) -> list[Finding]:
        """Minute data only: every stored session should hold exactly
        _MINUTE_BARS_PER_SESSION one-minute bars (09:15-15:29). Exempt: the
        first stored session (listing-day partials are legitimate) and
        `today` (an intraday sync legitimately holds a partial session that
        the next sync tops up)."""
        if timeframe != Timeframe.MINUTE:
            return []
        counts = (
            df.group_by(pl.col("ts").dt.date().alias("session"))
            .agg(pl.len().alias("n_bars"))
            .sort("session")
        )
        first_session = counts.get_column("session")[0]
        bad = counts.filter(
            (pl.col("n_bars") != _MINUTE_BARS_PER_SESSION)
            & (pl.col("session") != first_session)
            & (pl.col("session") != today)
        )
        if bad.is_empty():
            return []
        dates = bad.get_column("session").to_list()
        n_bars = bad.get_column("n_bars").to_list()
        preview = [
            f"{d} ({n}/{_MINUTE_BARS_PER_SESSION})"
            for d, n in zip(dates[:_PREVIEW_LIMIT], n_bars, strict=False)
        ]
        return [
            Finding(
                symbol=symbol,
                timeframe=timeframe.value,
                check="minute_completeness",
                severity="warn",
                message=(
                    f"{bad.height} session(s) with a bar count != "
                    f"{_MINUTE_BARS_PER_SESSION} (expected one bar per minute "
                    "09:15-15:29; first stored session and today are exempt), "
                    f"first: {preview}"
                ),
                ts=datetime.combine(dates[0], datetime.min.time()),
                count=bad.height,
            )
        ]

    @staticmethod
    def _check_extreme_outliers(
        symbol: str, timeframe: Timeframe, df: pl.DataFrame
    ) -> list[Finding]:
        if df.height < 2:
            return []
        ratio = (pl.col("close") / pl.col("close").shift(1) - 1.0).alias("ratio")
        flagged = df.select("ts", ratio).filter(pl.col("ratio").abs() > _OUTLIER_RATIO)
        if flagged.is_empty():
            return []
        ts_list = flagged.get_column("ts").to_list()
        ratios = flagged.get_column("ratio").to_list()
        preview = [f"{t} ({r:+.1%})" for t, r in zip(ts_list[:_PREVIEW_LIMIT], ratios, strict=False)]
        return [
            Finding(
                symbol=symbol,
                timeframe=timeframe.value,
                check="extreme_outlier",
                severity="warn",
                message=(
                    f"{flagged.height} bar(s) with |close/prev_close - 1| > "
                    f"{_OUTLIER_RATIO:.0%} (possible unadjusted corporate action -- "
                    f"cross-check the corporate-actions table), first: {preview}"
                ),
                ts=ts_list[0],
                count=flagged.height,
            )
        ]

    @staticmethod
    def _check_volume_anomalies(
        symbol: str, timeframe: Timeframe, df: pl.DataFrame
    ) -> list[Finding]:
        findings: list[Finding] = []
        total = df.height

        zero_vol = df.filter(pl.col("volume") == 0)
        if not zero_vol.is_empty():
            frac = zero_vol.height / total
            ts_list = zero_vol.get_column("ts").to_list()
            severity: Literal["info", "warn"] = "warn" if frac > _ZERO_VOLUME_WARN_FRACTION else "info"
            findings.append(
                Finding(
                    symbol=symbol,
                    timeframe=timeframe.value,
                    check="zero_volume",
                    severity=severity,
                    message=(
                        f"{zero_vol.height}/{total} bar(s) ({frac:.1%}) have zero volume, "
                        f"first: {[str(t) for t in ts_list[:_PREVIEW_LIMIT]]}"
                    ),
                    ts=ts_list[0],
                    count=zero_vol.height,
                )
            )

        window = _VOLUME_WINDOW_BARS.get(timeframe, _VOLUME_WINDOW_BARS[Timeframe.DAY])
        min_periods = min(window, max(total // 6, 10))
        if total >= min_periods:
            median = pl.col("volume").shift(1).rolling_median(
                window_size=window, min_samples=min_periods
            )
            spike = df.select("ts", (pl.col("volume") / median).alias("mult")).filter(
                pl.col("mult") > _VOLUME_SPIKE_MULTIPLE
            )
            if not spike.is_empty():
                ts_list = spike.get_column("ts").to_list()
                mults = spike.get_column("mult").to_list()
                preview = [
                    f"{t} ({m:.0f}x)" for t, m in zip(ts_list[:_PREVIEW_LIMIT], mults, strict=False)
                ]
                findings.append(
                    Finding(
                        symbol=symbol,
                        timeframe=timeframe.value,
                        check="volume_spike",
                        severity="info",
                        message=(
                            f"{spike.height} bar(s) with volume > {_VOLUME_SPIKE_MULTIPLE:.0f}x "
                            f"the trailing {window}-bar rolling median, first: {preview}"
                        ),
                        ts=ts_list[0],
                        count=spike.height,
                    )
                )
        return findings

    def _check_staleness(
        self, symbol: str, timeframe: Timeframe, today: date
    ) -> list[Finding]:
        last_ts = self.store.last_ts(symbol, timeframe)
        if last_ts is None:
            return []
        cutoff = today
        for _ in range(_STALE_TRADING_DAYS):
            cutoff = self.calendar.prev_trading_day(cutoff)
        if last_ts.date() >= cutoff:
            return []
        return [
            Finding(
                symbol=symbol,
                timeframe=timeframe.value,
                check="staleness",
                severity="warn",
                message=(
                    f"last bar at {last_ts} is more than {_STALE_TRADING_DAYS} trading "
                    f"day(s) old relative to {today}"
                ),
                ts=last_ts,
            )
        ]
