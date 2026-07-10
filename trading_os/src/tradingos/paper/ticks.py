"""Live tick recording (append-only Parquet) and Kite WebSocket streaming.

Two independent concerns live here:

- `TickRecorder` / `read_ticks`: durable, restart-safe storage of raw ticks as
  Parquet "part files" under `<ticks_dir>/<YYYY-MM-DD>/`. Never rewrites an
  existing part file; each flush writes a brand new one.
- `TickStreamer`: a thin wrapper around `kiteconnect.KiteTicker` that maps raw
  Kite tick dicts to `core.models.Tick`, feeds the recorder, and invokes a
  caller-supplied callback. Not exercised against the live Kite service in
  tests -- a `ticker_factory` is injected so tests can supply a fake.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any, ClassVar

import polars as pl

from tradingos.broker.base import TickCallback
from tradingos.core.errors import ConfigError
from tradingos.core.logging import get_logger
from tradingos.core.models import Tick
from tradingos.core.timeutils import now_ist, to_naive_ist

logger = get_logger(__name__)

# Canonical storage-seam schema for recorded ticks.
TICK_SCHEMA: dict[str, pl.DataType | type[pl.DataType]] = {
    "symbol": pl.Utf8,
    "instrument_token": pl.Int64,
    "ts": pl.Datetime("us"),
    "last_price": pl.Float64,
    "bid": pl.Float64,
    "ask": pl.Float64,
    "volume": pl.Int64,
}

# Default KiteTicker auto-reconnect params (match kiteconnect.KiteTicker's own
# class defaults; passed explicitly for documentation/clarity).
_DEFAULT_RECONNECT_MAX_TRIES = 50
_DEFAULT_RECONNECT_MAX_DELAY = 60


def _atomic_write_parquet(df: pl.DataFrame, path: Path) -> None:
    """Write `df` to `path` atomically (mirrors data/store.py::BarStore._atomic_write).

    Used here to write brand-new part files safely (never touches existing
    files, but a crash mid-write must never leave a half-written part file).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        df.write_parquet(tmp_path)
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


class TickRecorder:
    """Buffers ticks and appends them to Parquet part files:

        <ticks_dir>/<YYYY-MM-DD>/part-<seq:05d>-<uuid8>.parquet

    where the date is `tick.ts`'s date (IST) and `seq` is a counter local to
    this instance (starts at 0 each time a `TickRecorder` is constructed).
    The uuid8 suffix guarantees restart-safety: a new instance never picks a
    filename that collides with a part file written by a previous instance,
    so existing files are never rewritten.

    Columns: symbol(str), instrument_token(int64), ts(datetime us),
    last_price(f64), bid(f64, null ok), ask(f64, null ok), volume(int64, null ok).
    """

    def __init__(self, ticks_dir: Path, flush_every: int = 500) -> None:
        self._ticks_dir = Path(ticks_dir)
        self._flush_every = flush_every
        self._buffer: list[Tick] = []
        self._seq = 0

    def record(self, tick: Tick) -> None:
        """Buffer `tick`; auto-flushes once the buffer reaches `flush_every`."""
        self._buffer.append(tick)
        if len(self._buffer) >= self._flush_every:
            self.flush()

    def flush(self) -> list[Path]:
        """Write all buffered ticks to part file(s), grouped by IST date.

        Returns the paths written (empty list if the buffer was empty).
        """
        if not self._buffer:
            return []
        buffer, self._buffer = self._buffer, []

        by_day: dict[date, list[Tick]] = {}
        for tick in buffer:
            ts = to_naive_ist(tick.ts)
            by_day.setdefault(ts.date(), []).append(tick)

        paths: list[Path] = []
        # Deterministic order across days for reproducible test assertions.
        for day in sorted(by_day):
            paths.append(self._write_part(day, by_day[day]))
        return paths

    def _write_part(self, day: date, ticks: list[Tick]) -> Path:
        day_dir = self._ticks_dir / day.isoformat()
        df = pl.DataFrame(
            {
                "symbol": [t.symbol for t in ticks],
                "instrument_token": [t.instrument_token for t in ticks],
                "ts": [to_naive_ist(t.ts) for t in ticks],
                "last_price": [t.last_price for t in ticks],
                "bid": [t.bid for t in ticks],
                "ask": [t.ask for t in ticks],
                "volume": [t.volume for t in ticks],
            },
            schema=TICK_SCHEMA,
        )
        name = f"part-{self._seq:05d}-{uuid.uuid4().hex[:8]}.parquet"
        self._seq += 1
        path = day_dir / name
        _atomic_write_parquet(df, path)
        logger.info("recorded %d tick(s) to %s", len(ticks), path)
        return path

    def close(self) -> None:
        """Flush any remaining buffered ticks."""
        self.flush()


def read_ticks(ticks_dir: Path, day: date, symbol: str | None = None) -> pl.DataFrame:
    """Read all part files for `day`, concatenated and sorted by ts.

    Returns an empty (but schema-correct) frame if no part files exist for
    that day, or if `symbol` filters out every row.
    """
    day_dir = Path(ticks_dir) / day.isoformat()
    parts = sorted(day_dir.glob("part-*.parquet")) if day_dir.exists() else []
    if not parts:
        return pl.DataFrame(schema=TICK_SCHEMA)

    df = pl.concat([pl.read_parquet(p) for p in parts], how="vertical")
    if symbol is not None:
        df = df.filter(pl.col("symbol") == symbol)
    return df.sort("ts")


def _top_of_book(levels: list[dict[str, Any]] | None) -> float | None:
    """First price level of a Kite depth side, or None if absent/zero."""
    if not levels:
        return None
    price = levels[0].get("price")
    return float(price) if price else None


class TickStreamer:
    """Wraps `kiteconnect.KiteTicker` for live tick ingestion.

    Not tested against the live Kite service: pass `ticker_factory` (any
    callable with the same constructor signature as `KiteTicker`) to inject a
    fake in tests. Enforces `MAX_INSTRUMENTS_PER_CONNECTION` (Kite's per-
    connection instrument cap) at construction time.

    On (re)connect, resubscribes the full token list in `MODE_FULL` -- this
    covers both the first connection and any auto-reconnect, since Kite
    invokes `on_connect` again after a successful reconnect.

    Each incoming Kite tick dict is mapped to a `core.models.Tick`:
    instrument_token, last_price, bid/ask from the first depth level (None if
    depth is absent or the price is 0), volume from volume_traded, ts from
    exchange_timestamp (falling back to last_trade_time, then now_ist()),
    normalized to tz-naive IST. Ticks for an unknown instrument_token are
    dropped with a logged warning. Every mapped tick is first handed to the
    recorder (if any), then to `on_tick`; exceptions raised by `on_tick` are
    caught and logged -- they never kill the stream.
    """

    MAX_INSTRUMENTS_PER_CONNECTION: ClassVar[int] = 3000

    def __init__(
        self,
        api_key: str,
        access_token: str,
        *,
        token_to_symbol: dict[int, str],
        on_tick: TickCallback,
        recorder: TickRecorder | None = None,
        on_disconnect: Callable[[str], None] | None = None,
        ticker_factory: Callable[..., Any] | None = None,
    ) -> None:
        if len(token_to_symbol) > self.MAX_INSTRUMENTS_PER_CONNECTION:
            raise ConfigError(
                f"TickStreamer supports at most {self.MAX_INSTRUMENTS_PER_CONNECTION} "
                f"instruments per connection, got {len(token_to_symbol)}"
            )
        self._token_to_symbol = dict(token_to_symbol)
        self._on_tick = on_tick
        self._recorder = recorder
        self._on_disconnect = on_disconnect

        if ticker_factory is None:
            from kiteconnect import KiteTicker

            ticker_factory = KiteTicker

        self._ticker = ticker_factory(
            api_key,
            access_token,
            reconnect=True,
            reconnect_max_tries=_DEFAULT_RECONNECT_MAX_TRIES,
            reconnect_max_delay=_DEFAULT_RECONNECT_MAX_DELAY,
        )
        self._ticker.on_ticks = self._on_ticks
        self._ticker.on_connect = self._on_connect
        self._ticker.on_close = self._on_close
        self._ticker.on_error = self._on_error
        self._ticker.on_reconnect = self._on_reconnect
        self._ticker.on_noreconnect = self._on_noreconnect

    # -- lifecycle --------------------------------------------------------

    def start(self, threaded: bool = True) -> None:
        self._ticker.connect(threaded=threaded)

    def stop(self) -> None:
        self._ticker.close()

    @property
    def is_connected(self) -> bool:
        return bool(self._ticker.is_connected())

    # -- KiteTicker callbacks ----------------------------------------------

    def _on_connect(self, ws: Any, response: Any) -> None:
        tokens = list(self._token_to_symbol)
        logger.info("tick stream connected; subscribing %d instrument(s)", len(tokens))
        ws.subscribe(tokens)
        ws.set_mode(ws.MODE_FULL, tokens)

    def _on_ticks(self, ws: Any, ticks: list[dict[str, Any]]) -> None:
        for raw in ticks:
            self._handle_tick(raw)

    def _on_close(self, ws: Any, code: Any, reason: Any) -> None:
        logger.warning("tick stream closed: %s %s", code, reason)

    def _on_error(self, ws: Any, code: Any, reason: Any) -> None:
        logger.warning("tick stream error: %s %s", code, reason)

    def _on_reconnect(self, ws: Any, attempts_count: int) -> None:
        logger.warning("tick stream reconnecting (attempt %d)", attempts_count)

    def _on_noreconnect(self, ws: Any) -> None:
        reason = "max reconnect attempts exhausted"
        logger.error("tick stream giving up: %s", reason)
        if self._on_disconnect is not None:
            self._on_disconnect(reason)

    # -- mapping ------------------------------------------------------------

    def _handle_tick(self, raw: dict[str, Any]) -> None:
        token = raw.get("instrument_token")
        symbol = self._token_to_symbol.get(token)
        if symbol is None:
            logger.warning("dropping tick for unknown instrument_token %s", token)
            return

        depth = raw.get("depth") or {}
        bid = _top_of_book(depth.get("buy"))
        ask = _top_of_book(depth.get("sell"))
        ts_raw = raw.get("exchange_timestamp") or raw.get("last_trade_time") or now_ist()

        tick = Tick(
            symbol=symbol,
            instrument_token=token,
            ts=to_naive_ist(ts_raw),
            last_price=raw["last_price"],
            bid=bid,
            ask=ask,
            volume=raw.get("volume_traded"),
        )

        if self._recorder is not None:
            self._recorder.record(tick)

        try:
            self._on_tick(tick)
        except Exception:
            logger.exception("on_tick callback raised; continuing stream")
