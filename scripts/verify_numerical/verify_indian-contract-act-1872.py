"""Verifier for foundation/business-laws/indian-contract-act-1872.json.

Every function recomputes its answer from the stem's parameters and then maps
the computed value onto an option key. Nothing is copied from the answer key.

Three families of computable question live in this chapter, and each raises a
LEGAL choice before it raises an arithmetic one:

1. Postal-rule timelines (ss. 4, 5, 6(2)).
   _add_days(d, n)  a period expressed in DAYS runs from, and excludes, the
                    trigger date — day 1 is the next day. 21 days from 11 May
                    -> 1 June. Used for s. 6(2) lapse.
   The two s. 5 deadlines are dates already given in the stem, not periods:
     - the OFFEROR may revoke until the acceptance is POSTED, and his
       revocation binds the offeree only when it REACHES him (s. 4). So the
       contract date is the acceptance-posting date whenever the revocation
       arrives after it.
     - the ACCEPTOR may revoke until the acceptance letter REACHES the
       offeror, so his deadline is the delivery date of that letter.

2. Appropriation of payments (ss. 59 to 61) — plain running arithmetic over
   the debts in the order the applicable section fixes. The section chosen is
   the legal step: s. 60 (creditor's discretion, time-barred debt allowed)
   versus s. 61 (oldest first).

3. Money measures — joint-promisor contribution (s. 43), the effect of a
   release (s. 44), the s. 74 ceiling, and the s. 73 damages measure with the
   Explanation's duty to mitigate. Each is written as an explicit expression
   so a reviewer can see the rule, not just the number.

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


# ── ss. 4, 5, 6(2) · postal timelines ────────────────────────────────────

def q_f2c2_009():
    # Offer letter dated 11 May 2026, open "twenty-one days from the date of
    # this letter". s. 6(2): the proposal is revoked by the lapse of the time
    # prescribed. Days run from, and exclude, the date of the letter.
    letter = date(2026, 5, 11)
    last_day = _add_days(letter, 21)
    key = _pick(
        {
            "A": _add_days(letter, 20),        # counts the letter's own date as day 1
            "B": date(2026, 6, 11),            # reads 21 days as one calendar month
            "C": _add_days(letter, 22),        # off-by-one the other way
            "D": last_day,
        },
        last_day,
    )
    return {"answer": key, "computed": last_day.isoformat()}


def q_f2c2_010():
    # Proposal posted 2 Feb, received 6 Feb. Acceptance posted 10 Feb, received
    # 14 Feb. Revocation of the proposal posted 8 Feb, reaching the acceptor
    # 12 Feb.
    #   s. 4  — acceptance complete against the PROPOSER when posted.
    #   s. 4  — revocation complete against the ACCEPTOR when it reaches him.
    #   s. 5  — the proposal may be revoked only before the acceptance is posted.
    proposal_received = date(2026, 2, 6)
    acceptance_posted = date(2026, 2, 10)
    acceptance_received = date(2026, 2, 14)
    revocation_reached = date(2026, 2, 12)

    revocation_effective = revocation_reached <= acceptance_posted
    contract_date = None if revocation_effective else acceptance_posted
    assert contract_date is not None, "on these dates the revocation is out of time"

    key = _pick(
        {
            "A": proposal_received,
            "B": acceptance_posted,
            "C": revocation_reached,
            "D": acceptance_received,
        },
        contract_date,
    )
    return {"answer": key, "computed": contract_date.isoformat()}


def q_f2c2_011():
    # Same facts. s. 5, second limb: an acceptance may be revoked at any time
    # before the communication of the acceptance is complete as against the
    # ACCEPTOR — that is, before it reaches the proposer. The acceptance was
    # posted on 10 Feb and spent four days in the post.
    acceptance_posted = date(2026, 2, 10)
    transit_days = 4
    deadline = _add_days(acceptance_posted, transit_days)
    key = _pick(
        {
            "A": acceptance_posted,                    # the offeror's deadline, not the acceptor's
            "B": _add_days(acceptance_posted, 2),      # the date the offeror's revocation arrived
            "C": deadline,
            "D": _add_days(acceptance_posted, 3),      # off-by-one
        },
        deadline,
    )
    return {"answer": key, "computed": deadline.isoformat()}


# ── ss. 43, 44 · joint promisors ─────────────────────────────────────────

def q_f2c2_037():
    # Three joint promisors owe 6,00,000. The promisee releases one of them.
    # s. 44 — the release does not discharge the others; s. 43 — the promisee
    # may compel any one of them to perform the WHOLE promise.
    debt = 600000
    n = 3
    equal_share = debt // n
    recoverable_from_one = debt          # s. 43, unaffected by the s. 44 release
    key = _pick(
        {
            "A": recoverable_from_one,
            "B": debt - equal_share,     # treats the release as a partial discharge
            "C": equal_share,            # English several liability
            "D": 0,                      # release of one discharges all
        },
        recoverable_from_one,
    )
    return {"answer": key, "computed": recoverable_from_one}


def q_f2c2_040():
    # Three joint promisors owe 9,00,000; one pays the whole; one of the other
    # two is insolvent. s. 43 — equal contribution, and the loss from a
    # co-promisor's default is borne by the rest in EQUAL shares.
    debt = 900000
    promisors = 3
    equal_share = debt // promisors                   # 3,00,000 each
    defaulter_share = equal_share                     # the insolvent promisor's share
    solvent_others = 2                                # the payer and the one other
    recoverable_from_manoj = equal_share + defaulter_share // solvent_others
    key = _pick(
        {
            "A": equal_share,                         # stops at the bare one-third
            "B": debt,                                # joint and several towards a co-promisor
            "C": equal_share + defaulter_share,       # whole default thrown on one promisor
            "D": recoverable_from_manoj,
        },
        recoverable_from_manoj,
    )
    return {"answer": key, "computed": recoverable_from_manoj}


# ── ss. 60, 61 · appropriation of payments ───────────────────────────────

def q_f2c2_038():
    # Neither party appropriates -> s. 61: discharge in ORDER OF TIME.
    debts = [                      # (date incurred, amount)
        (date(2025, 1, 12), 18000),
        (date(2025, 3, 4), 25000),
        (date(2025, 6, 20), 15000),
    ]
    payment = 30000

    def apply_in_order(order, amount):
        balances = {d: amt for d, amt in debts}
        for d in order:
            paid = min(amount, balances[d])
            balances[d] -= paid
            amount -= paid
        return balances

    oldest_first = [d for d, _ in sorted(debts)]
    newest_first = list(reversed(oldest_first))
    target = date(2025, 3, 4)                       # the 25,000 debt

    outstanding = apply_in_order(oldest_first, payment)[target]

    total = sum(a for _, a in debts)
    proportionate = round(25000 - payment * 25000 / total)   # s. 61 equal-standing rule misapplied

    key = _pick(
        {
            "A": proportionate,
            "B": apply_in_order(newest_first, payment)[target],
            "C": outstanding,
            "D": 25000,                                       # payment held in suspense
        },
        outstanding,
    )
    return {"answer": key, "computed": outstanding}


def q_f2c2_039():
    # Debtor gives no intimation -> s. 60: the creditor may apply the payment to
    # any lawful debt actually due, INCLUDING a time-barred one. He applies it
    # to the time-barred debt, which was never recoverable by suit anyway.
    time_barred = 40000
    current = 60000
    payment = 40000

    applied_to_time_barred = min(payment, time_barred)
    remaining_payment = payment - applied_to_time_barred
    suable = current - remaining_payment              # 60,000 - 0

    key = _pick(
        {
            "A": current - payment,                   # forces the payment onto the current loan
            "B": suable,
            "C": time_barred + current,               # payment ignored entirely
            "D": 0,                                   # treats the whole balance as barred
        },
        suable,
    )
    return {"answer": key, "computed": suable}


# ── ss. 73, 74 · damages ─────────────────────────────────────────────────

def q_f2c2_043():
    # s. 74 — reasonable compensation NOT EXCEEDING the sum named. The proved
    # loss exceeds the ceiling, so the ceiling governs.
    named_sum = 800000
    proved_loss = 1150000
    award = min(proved_loss, named_sum)
    key = _pick(
        {
            "A": proved_loss,                    # ignores the ceiling
            "B": named_sum + proved_loss,        # treats the named sum as an add-on
            "C": proved_loss - named_sum,        # awards only the excess
            "D": award,
        },
        award,
    )
    return {"answer": key, "computed": award}


# Case set 4 — the s. 73 measure with the Explanation's duty to mitigate.
_QTY = 800
_CONTRACT_RATE = 450
_BREACH_RATE = 520          # market rate on 5 July 2026, the date of breach
_SUBSTITUTE_RATE = 575      # rate on 20 August 2026, when the buyer finally bought
_EXPORT_RATE = 800          # undisclosed resale value


def cs_f2c2_04_a():
    # First limb of s. 73: the loss naturally arising is the market/contract
    # differential ON THE DATE OF BREACH.
    ordinary = _QTY * (_BREACH_RATE - _CONTRACT_RATE)
    key = _pick(
        {
            "A": ordinary,
            "B": _QTY * (_SUBSTITUTE_RATE - _CONTRACT_RATE),   # measured at the late purchase
            "C": _QTY * (_EXPORT_RATE - _BREACH_RATE),         # the undisclosed export margin
            "D": _QTY * (_SUBSTITUTE_RATE - _BREACH_RATE),     # the avoidable extra cost
        },
        ordinary,
    )
    return {"answer": key, "computed": ordinary}


def cs_f2c2_04_b():
    # Explanation to s. 73: the avoidable part of the loss — the extra cost the
    # buyer incurred by waiting six weeks before buying a substitute.
    avoidable = _QTY * (_SUBSTITUTE_RATE - _BREACH_RATE)
    key = _pick(
        {
            "A": 0,                                            # no duty to mitigate
            "B": _QTY * (_SUBSTITUTE_RATE - _CONTRACT_RATE),   # whole differential
            "C": avoidable,
            "D": _QTY * (_BREACH_RATE - _CONTRACT_RATE),       # the recoverable part
        },
        avoidable,
    )
    return {"answer": key, "computed": avoidable}
