"""Verifier for foundation/business-laws/indian-partnership-act-1932.json.

Every function recomputes its answer from the parameters stated in the stem and
then maps the computed value onto an option key. No answer key is copied.

Four families of computable question live in this chapter, and in each of them
the arithmetic is easy while the LEGAL step that selects the arithmetic is the
thing being examined:

1. The six-month election window of a minor who has attained majority
   (s. 30(5)). The period runs from the LATER of (i) the date of majority and
   (ii) the date he obtained knowledge that he had been admitted to the benefits
   of partnership. `_add_months` adds six calendar months to that later date, so
   3 February 2026 -> 3 August 2026. The date of admission to the benefits is
   never a trigger, although it is the date from which liability runs if he
   becomes a partner (s. 30(7)(b)).

2. Interest at six per cent per annum on a payment or advance made beyond the
   capital a partner agreed to subscribe (s. 13(d)). This is a charge and is
   payable whether or not the firm made profits, which is what separates it from
   interest on capital under s. 13(c). Time-apportioned over the months for
   which the advance was outstanding.

3. The outgoing partner's option under s. 37: the share of profits since he
   ceased to be a partner attributable to the use of his share of the firm's
   property, OR interest at six per cent per annum on the amount of his share.
   The Act gives an option, so the recoverable figure is the HIGHER of the two,
   never their sum and never their difference.

4. The settlement of accounts on dissolution (s. 48(b)): assets are applied
   (i) to the debts of the firm to third parties, (ii) rateably to partners'
   advances as distinguished from capital, (iii) rateably to partners' capital,
   and (iv) the residue in the profit-sharing ratio. `_waterfall` performs those
   four steps explicitly, including the rateable abatement when what is left is
   not enough to repay capital in full.

One question is computable only because a legal bar removes a set-off: an
unregistered firm cannot claim a set-off (s. 69(3)), so the amount payable to
the plaintiff is the whole of his claim.

Law as on 2026-02-28; applicable to the Sept 2026 and Jan 2027 attempts.
"""

from __future__ import annotations

from datetime import date


def _add_months(d: date, n: int) -> date:
    """Add n calendar months, keeping the day of the month."""
    month = d.month - 1 + n
    year = d.year + month // 12
    month = month % 12 + 1
    return date(year, month, d.day)


def _pick(options, value):
    """Map a computed value to its option key."""
    for key, candidate in options.items():
        if candidate == value:
            return key
    raise AssertionError(f"computed {value!r} matches no option in {options!r}")


def _waterfall(assets, outside_debts, advances, capitals, ratio):
    """Section 48(b) settlement.

    advances and capitals are dicts partner -> amount; ratio is a dict
    partner -> profit-sharing weight. Returns a dict partner -> total received,
    plus the amount paid to each partner on account of capital.
    """
    left = assets - outside_debts
    assert left >= 0, "assets do not even cover the firm's debts"

    # (ii) partners' advances, rateably if short
    total_adv = sum(advances.values())
    if left >= total_adv:
        paid_adv = dict(advances)
        left -= total_adv
    else:
        paid_adv = {p: advances[p] * left / total_adv for p in advances}
        left = 0

    # (iii) partners' capital, rateably if short
    total_cap = sum(capitals.values())
    if left >= total_cap:
        paid_cap = dict(capitals)
        left -= total_cap
    else:
        paid_cap = {p: capitals[p] * left / total_cap for p in capitals}
        left = 0

    # (iv) residue in the profit-sharing ratio
    total_ratio = sum(ratio.values())
    residue = {p: left * ratio[p] / total_ratio for p in ratio}

    total = {}
    for p in set(list(advances) + list(capitals) + list(ratio)):
        total[p] = paid_adv.get(p, 0) + paid_cap.get(p, 0) + residue.get(p, 0)
    return total, paid_cap, residue


def q_f2c4_019():
    """Minor's election deadline: admitted 10 Jun 2022, majority 12 Mar 2026,
    knowledge 20 Jul 2026. Six months from the LATER of majority and knowledge."""
    majority = date(2026, 3, 12)
    knowledge = date(2026, 7, 20)
    deadline = _add_months(max(majority, knowledge), 6)
    options = {
        "A": date(2027, 1, 20),
        "B": date(2026, 9, 12),
        "C": date(2022, 12, 10),
        "D": date(2027, 7, 20),
    }
    return {"answer": _pick(options, deadline), "computed": deadline.isoformat()}


def q_f2c4_021():
    """Section 13(d): 6% p.a. on an advance of Rs 3,00,000 beyond capital,
    outstanding 8 months. Payable although the firm made a loss; the agreed
    capital of Rs 5,00,000 carries nothing (s. 13(c))."""
    advance = 300000
    interest = advance * 6 / 100 * 8 / 12
    options = {"A": 18000, "B": 32000, "C": None, "D": 12000}
    return {"answer": _pick(options, interest), "computed": interest}


def q_f2c4_032():
    """Section 37 option: profits attributable to the use of his share
    (Rs 57,000) OR 6% p.a. on his share of Rs 8,00,000 for one year. The
    outgoing partner takes the higher of the two."""
    share = 800000
    profits = 57000
    interest = share * 6 / 100 * 12 / 12
    claim = max(profits, interest)
    options = {"A": 48000, "B": 57000, "C": 105000, "D": 9000}
    return {"answer": _pick(options, claim), "computed": claim}


def q_f2c4_041():
    """Section 48(b): total received by Deepa. Assets 47,00,000; outside
    creditors 18,00,000; Deepa's advance 5,00,000; capitals 9/6/3 lakh;
    profits 3:2:1."""
    total, _, _ = _waterfall(
        assets=4700000,
        outside_debts=1800000,
        advances={"Deepa": 500000},
        capitals={"Deepa": 900000, "Elango": 600000, "Farhan": 300000},
        ratio={"Deepa": 3, "Elango": 2, "Farhan": 1},
    )
    got = total["Deepa"]
    options = {"A": 1200000, "B": 1400000, "C": 1900000, "D": 1700000}
    return {"answer": _pick(options, got), "computed": got}


def q_f2c4_042():
    """Section 48(b)(iii): assets 27,00,000, creditors 15,00,000, P's advance
    3,00,000, capitals P 8,00,000 and Q 4,00,000. Only 9,00,000 is left for
    capital of 12,00,000, so capital abates rateably and Q receives 3,00,000."""
    _, paid_cap, _ = _waterfall(
        assets=2700000,
        outside_debts=1500000,
        advances={"P": 300000},
        capitals={"P": 800000, "Q": 400000},
        ratio={"P": 1, "Q": 1},
    )
    got = paid_cap["Q"]
    options = {"A": 400000, "B": 450000, "C": 300000, "D": 150000}
    return {"answer": _pick(options, got), "computed": got}


def cs_f2c4_02_a():
    """Minor's election deadline: majority 18 Nov 2025, knowledge 3 Feb 2026.
    Six months from the later of the two."""
    majority = date(2025, 11, 18)
    knowledge = date(2026, 2, 3)
    deadline = _add_months(max(majority, knowledge), 6)
    options = {
        "A": date(2026, 5, 18),
        "B": date(2026, 8, 3),
        "C": date(2022, 3, 5),
        "D": date(2027, 2, 3),
    }
    return {"answer": _pick(options, deadline), "computed": deadline.isoformat()}


def cs_f2c4_03_b():
    """Section 69(3): an unregistered firm cannot claim a set-off, so the
    landlord's claim of Rs 3,40,000 is payable in full and the firm's own
    claim of Rs 1,15,000 drops out of the suit."""
    claim = 340000
    set_off_available = 0  # barred by s. 69(3) while the firm is unregistered
    payable = claim - set_off_available
    options = {"A": 225000, "B": 0, "C": 340000, "D": 115000}
    return {"answer": _pick(options, payable), "computed": payable}
