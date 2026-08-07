"""Verifier for foundation/business-laws/sale-of-goods-act-1930.json.

Every function recomputes its answer from the parameters stated in the stem and
then maps the computed value onto an option key. No answer key is copied.

Three families of computable question live in this chapter, and in each of them
the arithmetic is trivial while the LEGAL step that selects the arithmetic is
the thing being examined:

1. Money owed on a delivery that does not match the contract (s. 37) and money
   owed where the risk has passed (ss. 20 and 26). The legal step is deciding
   WHICH quantity and WHICH rate the Act makes payable — the contract rate on
   the quantity accepted, or the whole contract price on goods the buyer now
   owns and has lost.

2. Resale by an unpaid seller (s. 54(2)). Arithmetically this is only
   resale price minus contract price, but the sign of that difference and the
   presence or absence of a NOTICE of the intention to resell decide who keeps
   the money:
     - notice given  -> the seller keeps a surplus and recovers a deficiency;
     - no notice     -> the buyer takes the profit and the seller recovers
                        nothing.
   The expenses of redelivery on a stoppage in transit are the seller's own
   (s. 52(2)) and are therefore excluded from the recoverable deficiency.

3. Sale-or-return timelines (s. 24). _add_days(d, n) counts a period expressed
   in DAYS from, and excluding, the trigger date, so day 1 is the day after
   delivery. Property passes on the EARLIEST of approval, an act adopting the
   transaction, expiry of a fixed return period, or expiry of a reasonable time
   where none is fixed.

Damages for non-delivery (s. 57) use the Contract Act s. 73 measure: the
difference between the market price on the date of breach and the contract
price, applied to the quantity not delivered.

Law as on 2026-02-28; applicable to the Sept 2026 and Jan 2027 attempts.
"""

from __future__ import annotations

from datetime import date, timedelta


def _add_days(d: date, n: int) -> date:
    """A period of n days counted from (and excluding) the trigger date."""
    return d + timedelta(days=n)


def _pick(options, value):
    """Map a computed value to its option key."""
    for key, v in options.items():
        if v == value:
            return key
    raise AssertionError(f"computed {value!r} matches no option in {options}")


# ---------------------------------------------------------------------------
# q-f2c3-016 — s. 37(1): buyer accepts a short delivery and pays at the
# CONTRACT rate for the quantity actually accepted.
# ---------------------------------------------------------------------------
def q_f2c3_016():
    contracted_kg = 800
    delivered_kg = 620
    contract_rate = 1450

    payable = delivered_kg * contract_rate          # 620 * 1450 = 8,99,000
    shortfall_value = (contracted_kg - delivered_kg) * contract_rate

    options = {
        "A": payable,
        "B": contracted_kg * contract_rate,         # pays for the full 800 kg
        "C": shortfall_value,                       # value of the shortfall
        "D": 0,                                     # pays nothing yet
    }
    return {"answer": _pick(options, payable), "computed": payable}


# ---------------------------------------------------------------------------
# q-f2c3-031 — s. 24(b): a fixed return period, buyer silent, so property
# passes on the expiry of that period counted from (and excluding) delivery.
# ---------------------------------------------------------------------------
def q_f2c3_031():
    delivery = date(2026, 3, 6)
    return_period_days = 20

    passes_on = _add_days(delivery, return_period_days)      # 26 March 2026

    options = {
        "A": date(2026, 3, 25),      # counts the delivery day as day one
        "B": delivery,               # property thought to pass on delivery
        "C": None,                   # "a reasonable time", not applicable here
        "D": date(2026, 3, 26),
    }
    return {"answer": _pick(options, passes_on), "computed": passes_on.isoformat()}


# ---------------------------------------------------------------------------
# q-f2c3-034 — ss. 20 and 26: specific goods in a deliverable state, property
# passed at the contract, so the buyer bears the accidental loss and owes the
# whole contract price.
# ---------------------------------------------------------------------------
def q_f2c3_034():
    bags = 150
    rate_per_bag = 2640

    price = bags * rate_per_bag                     # 150 * 2640 = 3,96,000

    options = {
        "A": 0,                                     # risk thought to stay with seller
        "B": price // 2,                            # loss thought to be shared
        "C": round(price * 0.9),                    # arbitrary 10% abatement
        "D": price,
    }
    return {"answer": _pick(options, price), "computed": price}


# ---------------------------------------------------------------------------
# q-f2c3-042 — s. 54(2): resale AFTER notice, so the seller keeps the surplus.
# ---------------------------------------------------------------------------
def q_f2c3_042():
    contract_price = 960000
    resale_price = 1035000
    notice_given = True

    difference = resale_price - contract_price      # +75,000 surplus
    surplus_kept_by_seller = difference if (notice_given and difference > 0) else 0

    options = {
        "A": surplus_kept_by_seller,
        "B": 0,                                     # surplus said to go to the buyer
        "C": difference // 2,                       # surplus said to be shared
        "D": resale_price,                          # whole resale price
    }
    return {
        "answer": _pick(options, surplus_kept_by_seller),
        "computed": surplus_kept_by_seller,
    }


# ---------------------------------------------------------------------------
# q-f2c3-043 — s. 54(2): resale WITHOUT notice of the intention to resell, the
# goods not being perishable, so the profit belongs to the original buyer.
# ---------------------------------------------------------------------------
def q_f2c3_043():
    contract_price = 540000
    resale_price = 594000
    notice_given = False
    perishable = False

    profit = resale_price - contract_price          # +54,000
    buyer_entitlement = profit if (not notice_given and not perishable
                                   and profit > 0) else 0

    options = {
        "A": 0,                                     # buyer said to get nothing
        "B": resale_price,                          # whole resale price
        "C": buyer_entitlement,
        "D": profit // 2,                           # profit said to be shared
    }
    return {"answer": _pick(options, buyer_entitlement),
            "computed": buyer_entitlement}


# ---------------------------------------------------------------------------
# cs-f2c3-02-c — s. 57 with Contract Act s. 73: damages for non-delivery are
# the excess of the market price on the date of breach over the contract price.
# ---------------------------------------------------------------------------
def cs_f2c3_02_c():
    quintals = 500
    contract_rate = 4100
    market_rate_on_breach = 4460                    # 28 February 2026

    damages = (market_rate_on_breach - contract_rate) * quintals   # 1,80,000

    options = {
        "A": quintals * contract_rate,              # contract value
        "B": quintals * market_rate_on_breach,      # market value
        "C": 0,                                     # nothing, blaming the fire
        "D": damages,
    }
    return {"answer": _pick(options, damages), "computed": damages}


# ---------------------------------------------------------------------------
# cs-f2c3-03-b — s. 54(2) with s. 52(2): resale after notice at a loss, so the
# seller recovers the deficiency; the redelivery expense of the stoppage is his
# own and is not added to it.
# ---------------------------------------------------------------------------
def cs_f2c3_03_b():
    contract_price = 750000
    resale_price = 690000
    redelivery_expense = 22000                      # borne by the seller, s. 52(2)
    notice_given = True

    deficiency = contract_price - resale_price      # 60,000
    recoverable = deficiency if (notice_given and deficiency > 0) else 0

    options = {
        "A": recoverable + redelivery_expense,      # wrongly adds s. 52(2) cost
        "B": recoverable,
        "C": 0,                                     # contract thought rescinded
        "D": resale_price,                          # the resale price itself
    }
    return {"answer": _pick(options, recoverable), "computed": recoverable}
