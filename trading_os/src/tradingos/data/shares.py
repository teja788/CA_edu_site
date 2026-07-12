"""Shares-outstanding lookups and market-cap / scaled-turnover panels.

Historical market cap is reconstructed from a CURRENT share-count snapshot and
the store's *adjusted* close: ``mcap(t) = latest_snapshot_shares × close(t)``.
This is split/bonus-invariant because the adjusted close is back-adjusted — a
split multiplies the share count and divides the adjusted price by the same
factor, so the product is unchanged. The residual error is genuine issuance
drift (QIPs, buybacks, ESOPs, rights) between snapshot dates. These are NOT
point-in-time share counts; the intended consumers are decile / quantile
screens (universe construction, a scaled-turnover churn screen), not
exact-value logic. See docs/assumptions.md.

Everything here is trivially causal: ``mcap_series`` is an element-wise product
against each bar's own adjusted close, and ``scaled_turnover_panel`` uses only
trailing rolling windows (no centering, no look-ahead).
"""

from __future__ import annotations

import pandas as pd
from sqlmodel import select

from tradingos.config.settings import Settings
from tradingos.data.actions import SharesOutstanding
from tradingos.data.meta import meta_session
from tradingos.engine.dataview import MarketData


def latest_shares(settings: Settings) -> dict[str, int]:
    """Latest shares-outstanding snapshot per symbol (max ``as_of`` wins).

    Returns ``{symbol: shares}`` using, for each symbol, the row with the
    greatest ``as_of`` date. Symbols with no snapshot are simply absent.
    """
    with meta_session(settings.meta_db_path) as session:
        rows = list(session.exec(select(SharesOutstanding)).all())
    latest: dict[str, SharesOutstanding] = {}
    for r in rows:
        current = latest.get(r.symbol)
        if current is None or r.as_of > current.as_of:
            latest[r.symbol] = r
    return {sym: r.shares for sym, r in latest.items()}


def mcap_series(symbol_frame: pd.DataFrame, shares: int) -> pd.Series:
    """Market-cap series ``shares × close`` for one symbol.

    The caller passes the *adjusted* OHLCV frame (indexed by tz-naive IST
    ``DatetimeIndex``); the result is aligned to that index and named ``mcap``.
    Element-wise against each bar's own close, so trivially causal and
    split/bonus-invariant (halving the adjusted close while doubling ``shares``
    yields an identical series).
    """
    return (symbol_frame["close"] * shares).rename("mcap")


def mcap_panel(data: MarketData, shares_by_symbol: dict[str, int]) -> pd.DataFrame:
    """Per-symbol market-cap series aligned into one wide frame (columns=symbols).

    Symbols in ``data`` with no share snapshot are ABSENT from the panel (no
    zero/NaN-filled placeholder column). Where a symbol has no bar on a given
    date the cell is NaN (outer-join alignment on the union of bar dates).
    """
    columns: dict[str, pd.Series] = {}
    for symbol in data.symbols:
        shares = shares_by_symbol.get(symbol)
        if shares is None:
            continue
        columns[symbol] = mcap_series(data.full_frame(symbol), shares)
    return pd.DataFrame(columns)


def scaled_turnover_panel(
    data: MarketData,
    shares_by_symbol: dict[str, int],
    window: int = 126,
) -> pd.DataFrame:
    """Rolling churn panel: median traded value over ``window`` bars ÷ market cap.

    Per symbol: the trailing ``window``-bar median of ``close × volume`` (rupee
    traded value) divided by ``mcap_series`` at each bar — a share-turnover
    (churn) metric that scales the raw traded value by company size. Uses
    ``min_periods=window`` so the first ``window-1`` bars are NaN, and only
    trailing windows, so it is causal. Symbols with no share snapshot are ABSENT
    from the panel (as in ``mcap_panel``).
    """
    columns: dict[str, pd.Series] = {}
    for symbol in data.symbols:
        shares = shares_by_symbol.get(symbol)
        if shares is None:
            continue
        frame = data.full_frame(symbol)
        traded_value = frame["close"] * frame["volume"]
        rolling_median = traded_value.rolling(window, min_periods=window).median()
        columns[symbol] = (rolling_median / mcap_series(frame, shares)).rename(symbol)
    return pd.DataFrame(columns)
