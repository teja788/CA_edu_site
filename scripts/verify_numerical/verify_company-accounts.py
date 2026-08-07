"""Verifier for foundation/accounting/company-accounts.json (P1 Ch 11).

Every function recomputes its answer from the stem's own parameters — the share
capital ladder, the capital/premium split of each instalment, the pro-rata
waterfall, the forfeiture ledger, the reissue ledger, Table F interest and the
debenture issue entry — and only then maps the computed value on to an option
key through a dict holding all four option values.  Nothing is copied from the
answer key, so a wrong key in the bank shows up as a mismatch.

Conventions implemented below (each one is a judgment call flagged in the
review file, so a change of convention should break these functions loudly):

  * Ladder: paid-up = called-up − calls in arrears.  Calls in ADVANCE are never
    added to paid-up capital; they are a separate liability until the call is
    made.  Reserve capital is the slice of UNCALLED capital ring-fenced by
    special resolution for winding up.
  * Instalment split: every instalment is carried as (capital, premium) per
    share.  Sum of the capital elements must equal the face value and the sum
    of the premium elements the premium — `_check_schedule` asserts both, so a
    mis-stated stem cannot pass silently.
  * Pro-rata: rejected applications are refunded in full; the pro-rata group's
    surplus application money is never refunded — it is applied first to
    allotment and then, if the articles permit, to the calls.
  * Forfeiture: Share Capital is debited with the amount CALLED UP; premium
    already received is NOT reversed; premium called but unreceived IS debited
    back to Securities Premium.  The function asserts that the resulting
    Share Forfeiture credit equals the capital actually received — the two are
    arrived at by different routes, so the assert is a real cross-check.
  * Reissue: discount allowed may not exceed the amount forfeited on the shares
    being reissued (asserted); capital reserve = forfeited amount on the shares
    reissued − discount allowed on their reissue; a reissue above face value
    credits Securities Premium and does not enlarge the capital reserve.
  * Table F: 10% p.a. maximum on calls in arrears, 12% p.a. maximum on calls in
    advance, simple interest for the exact number of months.
  * Debentures: Debentures A/c is credited with the FACE value; loss on issue =
    discount on issue + premium payable on redemption; a premium received on
    issue goes to Securities Premium and is NOT netted against the loss;
    interest is the coupon rate on the face value.
"""

from __future__ import annotations


# ------------------------------------------------------------------ helpers

def _check_schedule(schedule, face, premium):
    """schedule = [(name, capital_per_share, premium_per_share), ...]."""
    assert abs(sum(c for _, c, _ in schedule) - face) < 1e-9, "capital elements must total the face value"
    assert abs(sum(p for _, _, p in schedule) - premium) < 1e-9, "premium elements must total the premium"


def paid_up(shares, called_up_per_share, calls_in_arrears=0.0, calls_in_advance=0.0):
    """Calls in advance are deliberately ignored: they are a liability, not capital."""
    return shares * called_up_per_share - calls_in_arrears


def reserve_capital(shares, face, called_up_per_share, reserved_per_share):
    uncalled = face - called_up_per_share
    assert 0 <= reserved_per_share <= uncalled, "reserve capital comes out of the uncalled part only"
    return shares * reserved_per_share


def prorata(applied_total, allotted_total, app_money, rejected_shares=0):
    """Returns the money map for an oversubscribed issue."""
    pro_rata_applications = applied_total - rejected_shares
    refund = rejected_shares * app_money
    received = applied_total * app_money
    retained = allotted_total * app_money
    excess = received - refund - retained
    return {
        "ratio": allotted_total / pro_rata_applications,
        "received": received,
        "refund": refund,
        "retained": retained,
        "excess": excess,
    }


def shares_applied_for(shares_allotted, applied_total, allotted_total):
    return shares_allotted * applied_total / allotted_total


def member_allotment_due(shares_applied, applied_total, allotted_total, app_money, allot_money):
    allotted = shares_applied * allotted_total / applied_total
    excess = (shares_applied - allotted) * app_money
    due = allotted * allot_money
    return {"allotted": allotted, "excess": excess, "due": due, "unpaid": due - excess}


def waterfall(excess, *dues):
    """Applies surplus application money to each subsequent instalment in turn.

    Returns the cash received on each instalment, in order.
    """
    cash = []
    left = excess
    for due in dues:
        applied = min(left, due)
        left -= applied
        cash.append(due - applied)
    return cash


def forfeiture(n, face, called_up_per_share, schedule, instalments_paid):
    """Full forfeiture entry, built from the instalment schedule.

    `instalments_paid` is how many of the leading instalments the member paid.
    """
    paid, unpaid = schedule[:instalments_paid], schedule[instalments_paid:]
    capital_received = n * sum(c for _, c, _ in paid)
    premium_received = n * sum(p for _, _, p in paid)
    premium_unreceived = n * sum(p for _, _, p in unpaid)
    unpaid_credits = {name: n * (c + p) for name, c, p in unpaid}
    share_capital_dr = n * called_up_per_share
    total_dr = share_capital_dr + premium_unreceived
    forfeiture_cr = total_dr - sum(unpaid_credits.values())
    # Cross-check: what is confiscated must be exactly the capital he did pay.
    assert abs(forfeiture_cr - capital_received) < 1e-6, "forfeiture credit must equal capital received"
    return {
        "share_capital_dr": share_capital_dr,
        "securities_premium_dr": premium_unreceived,
        "premium_received_untouched": premium_received,
        "unpaid_credits": unpaid_credits,
        "forfeiture_cr": forfeiture_cr,
    }


def reissue(n_forfeited, forfeited_total, n_reissued, face, reissue_price,
            paid_up_credited=None):
    paid_up_credited = face if paid_up_credited is None else paid_up_credited
    per_share = forfeited_total / n_forfeited
    forfeited_on_reissued = per_share * n_reissued
    discount = max(0.0, paid_up_credited - reissue_price) * n_reissued
    assert discount <= forfeited_on_reissued + 1e-9, "discount on reissue cannot exceed the amount forfeited"
    return {
        "discount": discount,
        "securities_premium": max(0.0, reissue_price - paid_up_credited) * n_reissued,
        "capital_reserve": forfeited_on_reissued - discount,
        "balance_left": forfeited_total - forfeited_on_reissued,
        "min_reissue_price": paid_up_credited - per_share,
    }


def simple_interest(amount, rate_pct, months):
    return amount * rate_pct / 100 * months / 12


TABLE_F_ARREARS = 10.0   # maximum, per Table F
TABLE_F_ADVANCE = 12.0   # maximum, per Table F


def debenture_issue(n, face, issue_price, redemption_price):
    discount = max(0.0, face - issue_price) * n
    issue_premium = max(0.0, issue_price - face) * n
    redemption_premium = max(0.0, redemption_price - face) * n
    return {
        "cash": n * issue_price,
        "debentures_cr": n * face,               # always the face value
        "discount_on_issue": discount,
        "securities_premium": issue_premium,     # never netted against the loss
        "premium_on_redemption": redemption_premium,
        "loss_on_issue": discount + redemption_premium,
    }


# ------------------------------------------------------- Unit 1: the ladder

def q_f1c11_005():
    subscribed_shares = 2_80_000
    value = paid_up(subscribed_shares, 8, calls_in_arrears=5_000 * 3)
    key = {
        28_00_000: "A",   # subscribed capital at face value
        22_40_000: "B",   # called-up, arrears ignored
        22_25_000: "C",
        22_55_000: "D",   # arrears added instead of deducted
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_006():
    value = reserve_capital(shares=60_000, face=10, called_up_per_share=7, reserved_per_share=2)
    key = {
        1_20_000: "A",
        1_80_000: "B",   # whole uncalled capital
        60_000: "C",     # the ₹1 still ordinarily callable
        4_20_000: "D",   # called-up capital
    }[round(value)]
    return {"answer": key, "computed": value}


# ------------------------------------- Unit 2: issue, premium, pro-rata, calls

def q_f1c11_013():
    n, face, issue_price = 80_000, 10, 13
    schedule = [("application", 4, 1), ("allotment", 3, 2), ("call", 3, 0)]
    _check_schedule(schedule, face, issue_price - face)
    value = n * (issue_price - face)
    key = {
        2_40_000: "A",
        80_000: "B",      # application instalment of the premium only
        1_60_000: "C",    # allotment instalment of the premium only
        10_40_000: "D",   # total money received
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_014():
    n, face, premium = 40_000, 10, 5
    schedule = [("application", 3, 1), ("allotment", 3, 4), ("call", 4, 0)]
    _check_schedule(schedule, face, premium)
    capital_element = dict((name, c) for name, c, _ in schedule)["allotment"]
    value = n * capital_element
    key = {
        2_80_000: "A",   # whole allotment instalment
        1_60_000: "B",   # the premium element
        1_20_000: "C",
        4_00_000: "D",   # entire face value of the issue
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_020():
    raised = 20_000 * (120 - 100)
    value = raised - 1_20_000 - 80_000   # both are s.52 permitted applications
    key = {
        4_00_000: "A",   # nothing written off
        2_80_000: "B",   # only preliminary expenses
        3_20_000: "C",   # only issue expenses
        2_00_000: "D",
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_021():
    m = prorata(applied_total=1_50_000, allotted_total=1_00_000, app_money=2)
    value = m["excess"]
    key = {
        1_00_000: "A",
        2_00_000: "B",   # application money retained on allotted shares
        3_00_000: "C",   # total application money received
        50_000: "D",     # excess shares costed at ₹1 instead of ₹2
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_022():
    value = shares_applied_for(shares_allotted=600, applied_total=60_000, allotted_total=40_000)
    key = {
        400: "A",     # ratio inverted
        1_800: "B",   # multiplied by 3 instead of 3/2
        900: "C",
        1_200: "D",   # allotment simply doubled
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_023():
    m = member_allotment_due(shares_applied=1_500, applied_total=75_000, allotted_total=50_000,
                             app_money=3, allot_money=4)
    value = m["unpaid"]
    key = {
        6_000: "A",   # allotment charged on shares applied for
        4_500: "B",   # 6,000 less the excess
        4_000: "C",   # allotment due, excess ignored
        2_500: "D",
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_024():
    n, face, issue_price = 80_000, 10, 12
    schedule = [("application", 4, 0), ("allotment", 3, 2), ("call", 3, 0)]
    _check_schedule(schedule, face, issue_price - face)
    m = prorata(applied_total=1_20_000, allotted_total=n, app_money=4)
    allotment_due = n * 5            # ₹5 instalment, capital ₹3 + premium ₹2
    value = allotment_due - m["excess"]
    key = {
        4_00_000: "A",   # allotment due, excess not adjusted
        2_40_000: "B",
        2_00_000: "C",   # excess computed at ₹5 application money
        5_60_000: "D",   # excess added instead of adjusted
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_025():
    m = prorata(applied_total=1_00_000, allotted_total=60_000, app_money=5, rejected_shares=10_000)
    value = m["refund"]
    key = {
        50_000: "A",
        2_00_000: "B",   # every unallotted share refunded
        1_50_000: "C",   # the pro-rata group's surplus, which is not refunded
        5_00_000: "D",   # total application money
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_026():
    n = 30_000
    m = prorata(applied_total=60_000, allotted_total=n, app_money=4)
    allotment_cash, call_cash = waterfall(m["excess"], n * 3, n * 3)
    assert allotment_cash == 0, "the surplus more than covers allotment in this stem"
    value = call_cash
    key = {
        90_000: "A",     # call due, carried surplus ignored
        1_20_000: "B",   # the whole excess application money
        60_000: "C",
        30_000: "D",     # the surplus left after allotment
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_027():
    value = simple_interest(4_000 * 4, TABLE_F_ARREARS, months=3)
    key = {
        1_600: "A",   # a full year
        400: "B",
        480: "C",     # the 12% advance rate used
        200: "D",     # half the period, or 5%
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_028():
    value = simple_interest(90_000, TABLE_F_ADVANCE, months=6)
    key = {
        4_500: "A",    # the 10% arrears rate used
        10_800: "B",   # a full year
        2_700: "C",    # three months
        5_400: "D",
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_030():
    value = paid_up(1_00_000, 8, calls_in_arrears=24_000, calls_in_advance=50_000)
    key = {
        7_76_000: "A",
        8_26_000: "B",   # calls in advance added to capital
        8_00_000: "C",   # arrears ignored
        8_50_000: "D",   # arrears ignored and advance added
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_031():
    consideration, face, premium_pct = 9_60_000, 100, 20
    issue_price = face * (1 + premium_pct / 100)
    value = consideration / issue_price
    key = {
        9_600: "A",    # divided by face value
        11_520: "B",   # consideration inflated by 20%, then divided by face
        12_000: "C",   # divided by ₹80, i.e. a 20% discount
        8_000: "D",
    }[round(value)]
    return {"answer": key, "computed": value}


# --------------------------------------------- Unit 2: forfeiture and reissue

def q_f1c11_033():
    schedule = [("application", 3, 0), ("allotment", 2, 0), ("first call", 3, 0)]
    e = forfeiture(n=1_000, face=10, called_up_per_share=8, schedule=schedule, instalments_paid=2)
    value = e["forfeiture_cr"]
    key = {
        8_000: "A",    # amount called up (the Share Capital debit)
        10_000: "B",   # face value
        5_000: "C",
        3_000: "D",    # the unpaid first call
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_034():
    face, issue_price = 10, 14
    schedule = [("application", 2, 4), ("allotment", 5, 0), ("first and final call", 3, 0)]
    _check_schedule(schedule, face, issue_price - face)
    e = forfeiture(n=800, face=face, called_up_per_share=face, schedule=schedule, instalments_paid=1)
    assert e["securities_premium_dr"] == 0, "the whole premium was received on application"
    value = e["forfeiture_cr"]
    key = {
        1_600: "A",
        4_800: "B",   # whole application money, premium included
        8_000: "C",   # amount called up
        3_200: "D",   # the premium already received
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_035():
    face, issue_price = 10, 13
    schedule = [("application", 3, 2), ("allotment", 4, 1), ("first and final call", 3, 0)]
    _check_schedule(schedule, face, issue_price - face)
    e = forfeiture(n=600, face=face, called_up_per_share=face, schedule=schedule, instalments_paid=1)
    value = e["securities_premium_dr"]
    key = {
        1_200: "A",   # the premium already received
        1_800: "B",   # the whole premium on the shares
        0: "C",       # "nil — premium is never reversed"
        600: "D",
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_037():
    schedule = [("application", 25, 0), ("allotment", 25, 0), ("first call", 25, 0)]
    e = forfeiture(n=500, face=100, called_up_per_share=75, schedule=schedule, instalments_paid=2)
    value = e["share_capital_dr"]
    key = {
        37_500: "A",
        50_000: "B",   # face value
        25_000: "C",   # amount received
        12_500: "D",   # amount unpaid
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_038():
    r = reissue(n_forfeited=2_000, forfeited_total=2_000 * 6, n_reissued=2_000,
                face=10, reissue_price=8)
    value = r["capital_reserve"]
    key = {
        12_000: "A",   # whole forfeited amount
        4_000: "B",    # the discount allowed
        8_000: "C",
        16_000: "D",   # discount added instead of deducted
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_039():
    r = reissue(n_forfeited=3_000, forfeited_total=3_000 * 5, n_reissued=1_800,
                face=10, reissue_price=9)
    assert round(r["balance_left"]) == 6_000
    value = r["capital_reserve"]
    key = {
        9_000: "A",    # forfeited amount on the reissued shares, discount not deducted
        7_200: "B",
        13_200: "C",   # whole ₹15,000 less the discount
        6_000: "D",    # the balance left for the unissued shares
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_040():
    r = reissue(n_forfeited=1_500, forfeited_total=4_500, n_reissued=1_500,
                face=10, reissue_price=7)
    value = r["min_reissue_price"]
    key = {
        3: "A",    # the forfeited amount per share
        10: "B",   # no discount allowed at all
        6: "C",    # a ₹4 discount, beyond the ₹3 forfeited
        7: "D",
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_041():
    r = reissue(n_forfeited=1_000, forfeited_total=7_000, n_reissued=1_000,
                face=10, reissue_price=12)
    assert r["discount"] == 0 and r["securities_premium"] == 2_000
    value = r["capital_reserve"]
    key = {
        5_000: "A",   # reissue premium wrongly deducted
        9_000: "B",   # reissue premium wrongly added
        7_000: "C",
        2_000: "D",   # the reissue premium itself
    }[round(value)]
    return {"answer": key, "computed": value}


# ------------------------------------------------------- Unit 3: debentures

def q_f1c11_044():
    d = debenture_issue(n=5_000, face=100, issue_price=94, redemption_price=100)
    value = d["debentures_cr"]
    key = {
        4_70_000: "A",   # money received
        5_00_000: "B",
        5_30_000: "C",   # discount added to the liability
        30_000: "D",     # the discount itself
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_045():
    d = debenture_issue(n=3_000, face=100, issue_price=95, redemption_price=110)
    value = d["loss_on_issue"]
    key = {
        15_000: "A",   # discount only
        30_000: "B",   # redemption premium only
        45_000: "C",
        60_000: "D",   # redemption premium overstated at ₹15
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_046():
    d = debenture_issue(n=2_500, face=100, issue_price=102, redemption_price=105)
    assert d["securities_premium"] == 5_000 and d["discount_on_issue"] == 0
    value = d["loss_on_issue"]
    key = {
        12_500: "A",
        7_500: "B",    # issue premium netted against the loss
        17_500: "C",   # issue premium added to the loss
        5_000: "D",    # the issue premium itself
    }[round(value)]
    return {"answer": key, "computed": value}


def q_f1c11_047():
    d = debenture_issue(n=6_000, face=100, issue_price=96, redemption_price=102)
    value = 9 / 100 * d["debentures_cr"]          # coupon on the FACE value
    key = {
        51_840: "A",   # 9% of the money received
        54_000: "B",
        55_080: "C",   # 9% of the redemption value
        27_000: "D",   # half a year
    }[round(value)]
    return {"answer": key, "computed": value}
