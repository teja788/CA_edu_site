# Go-live runbook

Operational runbook for the single operator (the owner) taking a strategy
live on Zerodha Kite Connect. Checklist and incident guide, not a design
doc — see `CLAUDE.md` for architecture and `docs/assumptions.md` for every
accuracy-relevant modeling assumption.

Commands below assume the live CLI (`tradingos.cli.live_cmds`) exposes:

- `uv run platform live run <strategy.yaml> --once|--schedule [--live]`
- `uv run platform live status <strategy.yaml>`
- `uv run platform live reconcile <strategy.yaml>`
- `uv run platform live killswitch status|engage|disengage`

and the existing paper CLI (`tradingos.cli.paper_cmds`):

- `uv run platform paper run <strategy.yaml> --once|--schedule`
- `uv run platform paper report <strategy.yaml> [--date YYYY-MM-DD]`
- `uv run platform paper status <strategy.yaml>`

## 1. Scope & non-negotiables

- **There is no Kite sandbox.** Paper mode (`paper/broker.py::PaperBroker`,
  live ticks + a virtual ledger) is the only sandbox this platform has —
  nothing skips it.
- **Dry-run is the default for `live run`.** It logs the exact orders it
  would place without sending them to Kite. `--live` is the explicit,
  separate opt-in flag — never assume a command is safe because it says
  "live"; check for `--live`.
- **The kill switch and pre-trade risk checks are always on**, in paper and
  live alike — there is no config flag to disable
  `broker/risk.py::PreTradeRiskChecker` or `broker/killswitch.py::KillSwitch`.
- **Nothing is promoted to live capital without passing the promotion gate
  in Section 4.** No exceptions for "just testing with ₹500."

## 2. Prerequisites (one-time)

1. **Kite Connect app.** Create one at https://developers.kite.trade/apps.
   Put credentials in `.env` (copy from `.env.example`, git-ignored — never
   commit `.env`): `TOS_KITE_API_KEY`, `TOS_KITE_API_SECRET`,
   `TOS_KITE_USER_ID`, and optionally `TOS_KITE_PASSWORD` /
   `TOS_KITE_TOTP_SECRET` (enable the TOTP-assisted login below).
   `Settings` (`config/settings.py`) reads every `TOS_`-prefixed variable
   from `.env` or the environment; nothing is hardcoded.
2. **Registered static IP — required for order placement.** Kite Connect
   requires a static IP registered against the app before it accepts
   order-placement calls (historical/quote data is unaffected). Configure
   it in the Kite developer console (developers.kite.trade/apps → your
   app). Running `live run --schedule --live` from a machine without that
   IP means orders are rejected even though data/websocket calls keep
   working — settle the hosting before your first live session.
3. **Telegram bot (optional but strongly recommended).** Set
   `TOS_TELEGRAM_BOT_TOKEN` and `TOS_TELEGRAM_CHAT_ID`.
   `core/alerts.py::TelegramAlerter` is a silent no-op unless BOTH are set
   — without it you get no fill/rejection/risk/token-expiry alerts and are
   flying blind between manual `status` checks.
4. **Instruments synced.** The live/paper runner resolves instrument tokens
   from the `data/instruments.py` token↔symbol table (`token_for`) and
   fails loudly with a `warning:` line per unresolved symbol if it's stale.
5. **Holiday calendar current.** `data/calendar.py::NSECalendar` gates
   trading-day checks in the risk checker and the scheduler; a stale
   calendar can skip a real trading day or attempt to trade a holiday.

## 3. Daily token flow

Kite access tokens expire once per trading day (reset around market open,
~6 AM). `data/auth.py::KiteAuth` caches the token by IST calendar date; a
token cached under a previous date is stale, not silently reused
(`get_access_token` raises `AuthError`).

**Morning login (before 09:00 IST, ahead of the 09:15 open):**
- Preferred: `uv run platform data login`, which runs
  `KiteAuth.interactive_login`. It prints the Kite login URL, opens it in a
  browser, and starts a one-shot local HTTP server on
  `127.0.0.1:<TOS_KITE_REDIRECT_PORT>` (default 8721) to capture
  `request_token` from the redirect automatically, falling back to a manual
  paste prompt if that server can't bind or capture in time. The token is
  exchanged and cached to `<data_dir>/kite_token.json`, dated today.
- Optional: if `TOS_KITE_USER_ID`, `TOS_KITE_PASSWORD` and
  `TOS_KITE_TOTP_SECRET` are all set, `uv run platform data login --totp`
  (`KiteAuth.totp_login`) drives Kite's *unofficial* web login + TOTP
  endpoints with no browser interaction.
  These endpoints are undocumented and can change or break without notice
  — keep interactive login as the reliable fallback.

**Mid-session expiry:** an expired/revoked token triggers a Telegram
"Token expiry" alert (`TelegramAlerter.alert_token_expiry`) and every
subsequent order placement fails with `AuthError` until you re-login.
Working orders already placed are unaffected; nothing new goes out until
you re-authenticate.

## 4. Promotion gate: backtest → paper → live

A strategy may go live **only after all of the following hold**:

1. **Event-engine validation.** Run on both engines and reconciled per
   `tests/engine/test_reconciliation.py`'s tolerances (final equity within
   1%, costs within 5%, curve divergence within 2%). The vectorized engine
   alone is never sufficient — same-close fills, no order book, no partial
   fills (`docs/assumptions.md`).
2. **≥ 4 weeks of paper sessions** — `uv run platform paper run
   <strategy.yaml> --schedule` run continuously on real ticks, not repeated
   `--once` catch-ups.
3. **EOD divergence report reviewed daily** (`uv run platform paper report
   <strategy.yaml>`, or the report the session-close job writes to
   `<artifacts_dir>/paper/<strategy.name>/eod-<date>.html`). Track
   `cum_diff_pct` (paper vs reference backtest equity, normalized to their
   first common date). **Starting threshold: |cumulative divergence|
   within 1–2%** — a starting point, not a hardcoded limit; the owner sets
   the number per strategy and revisits it as evidence accumulates. A
   breach means investigate before continuing to count paper days toward
   the gate.
4. **Zero unexplained paper rejections in the final week** — check
   `uv run platform paper status <strategy.yaml>` and REJECTED orders in
   the paper store. Every rejection must be explained (e.g. a known paper
   limitation from Section 8); an unexplained one likely means a sizing,
   risk-limit, or data problem that will also bite live.
5. **A full dry-run live session whose intended orders match the paper
   session's orders for the same day** — `uv run platform live run
   <strategy.yaml> --once` (dry-run, default) on a day paper also traded;
   diff the logged intended orders against that day's paper fills.
   Mismatches must be understood (usually config/universe drift) before
   going live.

Do not shortcut this under time pressure. A strategy that fails step 3 or 4
goes back to paper, not to "smaller live position as a compromise."

## 5. Going live (first session)

1. `uv run platform live killswitch status` — confirm **disengaged**; if
   engaged from a previous incident, resolve the cause first, then
   `uv run platform live killswitch disengage`.
2. Token fresh — completed today's login (Section 3).
3. Data synced for the day (instruments + any pre-open sync jobs).
4. `uv run platform live run <strategy.yaml> --once` (dry-run, no
   `--live`). Read the intended orders line by line — symbols, sides,
   quantities, estimated prices — against your own mental model before
   proceeding.
5. Only then: `uv run platform live run <strategy.yaml> --schedule --live`,
   started with **small capital** relative to the strategy's eventual
   target allocation. Watch the first fills as they happen and confirm
   Telegram alerts are arriving.
6. After the open settles, `uv run platform live reconcile
   <strategy.yaml>` to confirm the broker's order book matches what the
   platform believes it placed.

Stay at the terminal (or with Telegram reachable) through at least the
first reconcile pass — do not walk away during the first live session.

## 6. Daily operations

**Morning (before 09:15 IST):** complete the token login; sync data; run
`uv run platform live killswitch status` to confirm disengaged. `live run
--schedule` retries open-of-day placement every minute from 09:15 to 09:25
IST (an idempotent retry window, mirroring `paper/runner.py`'s scheduler),
so a switch disengaged a few minutes late can still recover that morning's
orders.

**During the session:** run `uv run platform live reconcile
<strategy.yaml>` periodically (at minimum once after the open, once before
the close). It polls the broker's order book and diffs it against the
platform's own order state. A mismatch — a fill the platform never
recorded, or an order state the broker reports that the platform didn't
expect — means the platform's view has drifted from the broker's. Place no
new orders for that strategy until you understand it; when in doubt,
`killswitch engage` (Section 7) while you investigate.

**Close (after 15:30 IST):** the session-close job (15:35 IST under
`--schedule`) marks positions to the day's official closes, snapshots
equity, and (paper) writes the EOD report. Review the EOD divergence report
and re-check the Section 4 threshold even after go-live — the promotion
gate becomes ongoing monitoring, it doesn't end at go-live.

**Restart-after-crash procedure:**
- Positions and cash are never stored directly — the broker rebuilds state
  by replaying the append-only fill log (`store.all_fills()`) through a
  fresh `Ledger` on construction (`paper/broker.py::_replay`). Just restart
  the runner; do not try to manually reconstruct state.
- A fill and its order's post-fill state are persisted in one SQLite
  transaction, so a crash mid-fill can never leave a replayable fill beside
  a still-OPEN order row that would double-fill on replay.
- Run `live reconcile` immediately after any restart: it is what detects an
  order placed with the broker before the crash but never recorded locally
  — a gap replay alone cannot see, since replay only knows fills already in
  the local store.
- The platform never double-places on restart: every order carries a
  deterministic `client_order_id`, and `place_order` treats one already
  stored as non-PENDING as a re-place, not a new order.

## 7. Incidents

**Runaway or wrong orders:**
```
uv run platform live killswitch engage --reason "runaway orders" --strategy <strategy.yaml>
```
Halts all new placement platform-wide (not just one strategy) and — because
`--strategy` is given — cancels that strategy's open orders. Without
`--strategy` the switch still engages but open orders are NOT touched (the
command prints a warning; handle them in Kite's web console). It works by
writing `{"engaged_at": ..., "reason": ...}` to the kill-switch file. **Default path: `<data_dir>/KILL_SWITCH`**
(`Settings.kill_switch_path`, i.e. `data/KILL_SWITCH` relative to the
project root by default). If the CLI itself is broken, engage by hand —
presence, not content, is the signal:
```
touch data/KILL_SWITCH
```
Every process (paper runner, live runner, any operator shell) checks this
same file. Disengage only once the cause is understood:
`uv run platform live killswitch disengage` (or delete the file).

**Token expired mid-session:** see Section 3 — Telegram "Token expiry"
alert fires, orders fail with `AuthError`. Re-login immediately; no
kill-switch action needed unless you also see unexplained order state
(treat that as a reconciliation incident too).

**WebSocket/tick loss:** `paper/ticks.py::TickStreamer` auto-reconnects
(Kite's own `reconnect=True`) and logs a warning per attempt, escalating if
attempts are exhausted (`on_noreconnect`). A short reconnect is
self-healing. If exhausted, quotes stop updating and working orders that
need a fresh quote stall — engage the kill switch if you can't confirm
quotes are flowing again promptly; stale quotes feeding a live fill
decision is exactly the failure mode the platform exists to avoid.

**Divergence breach:** halt (engage the kill switch if live), investigate
the cause (data drift, universe change, a bug). **Do not retune the live
strategy in place** to close the gap — that is the overfitting-to-noise
failure the promotion gate exists to prevent. Fix root cause, re-validate
through the full gate before resuming.

**Broker/API outage:** engage the kill switch immediately. If you are not
certain what positions you hold at the broker, phone Zerodha support or
check Kite's own web terminal directly — don't trust the platform's
last-known state until `live reconcile` succeeds after the outage clears.

## 8. Limits & known model gaps

From `docs/assumptions.md`'s "Paper trading" section — gaps in what paper
has validated, not gaps in live trading itself, so a strategy graduating
from paper must not silently depend on what paper never tested:

- **No partial fills in paper.** A paper order either fills in full or
  stays working — no volume-participation model like the event engine.
  Live fills can legitimately partial-fill in ways paper never exercised.
- **No T+1 settlement in paper.** Paper lets a same-day CNC buy be sold the
  same day; Zerodha would block that live. A strategy relying on same-day
  round-trips behaves differently — and likely fails — once live.
- **SL / SL-M orders are unsupported in paper** (rejected at placement — no
  intrabar path exists to trigger a stop off a single last-traded tick).
  **A live strategy must not depend on stop orders the paper stage never
  validated** — if the design uses SL/SL-M, its stop logic hasn't been
  exercised end to end before go-live; treat that as an explicit open risk.
  Overlay-based stops evaluated by the strategy/runner itself (e.g. ATR
  trailing stops, not broker-side SL orders) are a separate mechanism and
  are exercised by paper.
- **Live charges in reports are estimates until contract notes are
  ingested.** `costs/model.py` computes charges from the versioned Zerodha
  schedule, not actual contract notes — whole-rupee rounding of STT/stamp
  duty per contract note is not modeled and can differ by up to ~₹1 per
  note. Don't treat live report P&L as reconciled against Zerodha's own
  statements until contract notes are ingested and cross-checked.
