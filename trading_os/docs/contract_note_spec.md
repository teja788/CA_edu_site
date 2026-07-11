# Zerodha contract note — format spec for ingestion (researched 2026-07-11)

Grounding for the open audit item "contract-note ingestion": live/paper
`Fill.charges` are `CostModel` estimates until the broker's actual charges
are ingested. This documents what Zerodha actually provides, from public
sources (links at the bottom). Tag-level XML schema is NOT published — one
real export sample is still needed before the parser is written (see
"Blocking input" below).

## Where contract notes come from

- **Email ECN**: password-protected PDF (password = PAN in capitals) to the
  registered email at ~19:00 IST on every trade date.
- **Console self-serve** (the ingestion path):
  `console.zerodha.com/reports/downloads` → statement type **Contract note**
  → report type **PDF / XML / XLSX / SIGNED PDF** → date range → category
  (equity/currency/commodity). Constraints: max 365 days back per request,
  history available from Apr 2017, email download links expire in 7 days,
  bulk requests are slow.
- **No API**: Kite Connect does not serve contract notes; ingestion is a
  manual-export → CLI-import flow by design.

## Regulatory format

- Since **27 Jun 2025** (SEBI), brokers issue a **Common Contract Note with
  single VWAP**: ONE consolidated note per day regardless of how many
  exchanges the trades routed through; transaction charges of both
  exchanges are clubbed; exchange-wise trade breakdown moves to annexures.
- Zerodha's note is combined across NSE+BSE equity and NSE F&O. The note
  format previously changed on 1 Aug 2024 (exchange circular), so parsers
  must key on the note's own layout/version, not assume stability.

## Fields (per Zerodha's "how to interpret the contract note")

Trade details (Annexure A), one row per trade: Order No (exchange order
number), Order time, Trade No, Trade time, Security/Contract description,
Buy(B)/Sell(S), Exchange, Quantity, Gross Rate/Trade Price per unit,
Brokerage per unit, Net Rate per unit, Closing Rate per unit (derivatives
only), Net Total (before levies), Remarks. Equities carry a weighted
average price across exchanges (the single-VWAP mandate).

Obligation/charges summary (note-level, per segment): pay-in/pay-out
obligation (bracketed = payable), brokerage, **STT, exchange transaction
charges, SEBI turnover fee, stamp duty, GST** (CGST+SGST 9%+9% for
Karnataka-registered clients, IGST 18% otherwise), net amount
receivable/payable.

**NOT on the contract note:** DP charges (and call-and-trade) — those
appear only on the **funds statement** (Console → Funds → Statement →
XLSX/CSV) and, annually, in the AGS "other credits and debits" sheet.

## Ingestion design implications

1. **Format to ingest: XML** (machine-readable, no PAN-password PDF
   parsing). Tag names/nesting are undocumented publicly — pin them from a
   real sample before writing the parser.
2. **Two sources to fully true-up `Fill.charges`:** contract-note XML
   (brokerage/STT/exchange txn/SEBI/stamp/GST) **plus** funds-statement
   CSV for DP charges. The existing `CostModel` DP handling
   (once-per-scrip-per-day) reconciles against the ledger entry, not the
   note.
3. **Granularity mismatch:** the platform records charges per Fill; the
   note reports most levies at note/segment level with per-note
   whole-rupee rounding of STT/stamp (already documented in
   assumptions.md). Ingestion should therefore (a) store the note-level
   actuals as the source of truth, (b) prorate to fills by turnover only
   for display/analytics — mirroring how the ledger prorates clipped-sell
   charges — and (c) emit a daily reconciliation line: Σ estimates vs note
   actuals, flagging drift beyond the known ~₹1/note rounding.
4. **Join keys:** trade rows carry exchange Order No + Trade No +
   timestamps; the live journal keeps `broker_order_id` — join notes to
   journal fills on (exchange order number, trade date), falling back to
   (symbol, side, qty, trade time).

## Blocking input (owner)

One day's **XML contract-note export** (any small equity trading day) from
Console, so the parser is written against real tag names — the only part
public sources do not cover. A matching funds-statement CSV for the same
day would also pin the DP-charge row format.

## Sources

- Zerodha support: How to download contract notes
  (support.zerodha.com/.../where-can-i-get-the-contract-notes-for-the-trades-i-ve-taken)
- Zerodha support: How to understand the contract note
  (support.zerodha.com/.../how-to-interpret-the-contract-note)
- Zerodha support: What is an ECN (support.zerodha.com/.../what-is-ecn)
- SEBI press release Jul 2025: Common Contract Note with Single VWAP
  (sebi.gov.in/.../common-contract-note-with-single-volume-weighted-average-price-vwap...)
- Z-Connect: Tax reports at Zerodha (AGS / other credits and debits)
