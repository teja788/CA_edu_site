"""Verifier for foundation/accounting/bank-reconciliation-statement.json.

Each function recomputes the answer from the stem's item list with explicit
signed arithmetic (favourable = plus, overdraft = minus) and maps the computed
value to the option key. Never copies the key from the bank.
"""


def q_f1c3_001():
    # CB favourable → PB: start 45,000
    pb = 45_000
    pb += 8_000    # cheques issued not presented (bank not yet paid)
    pb -= 12_000   # cheques deposited not credited (bank not yet received)
    key = {41_000: "A", 49_000: "C", 25_000: "D", 65_000: "B"}[pb]
    return {"answer": key, "computed": pb}


def q_f1c3_002():
    # CB favourable → PB: start 60,000
    pb = 60_000
    pb += 15_000   # unpresented cheques
    pb -= 9_500    # uncredited deposits
    pb -= 500      # bank charges (bank debit)
    pb += 1_200    # interest allowed (bank credit)
    key = {66_200: "B", 53_800: "D", 63_800: "C", 67_200: "A"}[pb]
    return {"answer": key, "computed": pb}


def q_f1c3_003():
    # CB favourable → PB with direct deposit and dishonour
    pb = 38_400
    pb += 7_600    # unpresented cheques
    pb -= 11_000   # uncredited deposits
    pb += 5_000    # direct deposit by customer (bank credit)
    pb -= 3_200    # dishonoured cheque (bank removed the credit)
    pb -= 200      # dishonour charges
    key = {40_000: "A", 36_800: "B", 36_600: "C", 26_600: "D"}[pb]
    return {"answer": key, "computed": pb}


def q_f1c3_004():
    # CB overdraft → PB: overdraft written as minus
    pb = -25_000
    pb += 10_000   # unpresented cheques
    pb -= 6_000    # uncredited deposits
    # pb = -21,000 → overdraft 21,000
    key = {-29_000: "A", -21_000: "D", 21_000: "C", 9_000: "B"}[pb]
    return {"answer": key, "computed": pb}


def q_f1c3_005():
    # CB overdraft → PB
    pb = -42_500
    pb += 13_000   # unpresented cheques
    pb -= 18_700   # uncredited deposits
    pb -= 1_900    # interest on overdraft charged (bank debit)
    pb += 8_000    # direct deposit (bank credit)
    key = {-42_100: "A", -42_900: "D", -38_300: "C", -58_100: "B"}[pb]
    return {"answer": key, "computed": pb}


def q_f1c3_006():
    # CB overdraft → PB, only outstanding slices count
    unpresented = 24_000 - 16_500   # 7,500
    uncredited = 20_000 - 12_000    # 8,000
    pb = -30_000
    pb += unpresented
    pb -= uncredited
    pb -= 350      # bank charges
    key = {-14_350: "D", -42_850: "A", -30_850: "B", -29_850: "C"}[pb]
    return {"answer": key, "computed": pb}


def q_f1c3_007():
    # PB favourable → CB: flip every sign
    cb = 52_000
    cb -= 9_000    # unpresented cheques (cash book already reduced)
    cb += 14_000   # uncredited deposits (already in cash book)
    key = {47_000: "D", 57_000: "C", 29_000: "B", 75_000: "A"}[cb]
    return {"answer": key, "computed": cb}


def q_f1c3_008():
    # PB favourable → CB
    cb = 67_500
    cb -= 12_400   # unpresented cheques
    cb += 8_900    # uncredited deposits
    cb += 600      # bank charges not yet in cash book (add back)
    cb -= 2_100    # interest allowed not yet in cash book (deduct)
    key = {72_500: "B", 61_300: "C", 66_700: "A", 62_500: "D"}[cb]
    return {"answer": key, "computed": cb}


def q_f1c3_009():
    # PB favourable → CB with standing instruction and direct deposit
    cb = 40_000
    cb -= 11_000   # unpresented cheques
    cb += 5_500    # uncredited deposits
    cb += 4_500    # SI premium (bank debit the cash book lacks: add back)
    cb -= 6_000    # direct deposit (bank credit the cash book lacks: deduct)
    key = {33_000: "A", 47_000: "B", 36_000: "C", 44_000: "D"}[cb]
    return {"answer": key, "computed": cb}


def q_f1c3_010():
    # PB overdraft (debit balance) → CB
    cb = -18_000
    cb -= 5_000    # unpresented cheques
    cb += 7_500    # uncredited deposits
    key = {-20_500: "D", -30_500: "A", -15_500: "B", 15_500: "C"}[cb]
    return {"answer": key, "computed": cb}


def q_f1c3_011():
    # PB overdraft → CB
    cb = -56_000
    cb -= 21_000   # unpresented cheques
    cb += 13_400   # uncredited deposits
    cb += 900      # bank charges (add back)
    cb += 2_700    # interest on overdraft (add back)
    key = {-52_000: "B", -60_000: "C", -67_200: "D", -44_800: "A"}[cb]
    return {"answer": key, "computed": cb}


def q_f1c3_012():
    # PB overdraft → CB with direct deposit, dividend, charges
    cb = -27_300
    cb -= 9_800    # unpresented cheques
    cb += 12_500   # uncredited deposits
    cb -= 7_000    # direct deposit (credit the cash book lacks)
    cb -= 1_500    # dividend collected (credit the cash book lacks)
    cb += 450      # bank charges (debit the cash book has not made)
    key = {-21_950: "C", -15_650: "A", -33_550: "B", -32_650: "D"}[cb]
    return {"answer": key, "computed": cb}


def q_f1c3_013():
    # Amended cash book: only bank-first items enter; timing items excluded
    acb = 48_000
    acb -= 400     # bank charges
    acb += 1_100   # interest allowed
    acb -= 3_000   # SI insurance premium
    acb += 9_000   # direct deposit
    # 6,000 unpresented and 10,000 uncredited stay BRS-only
    key = {54_700: "A", 50_700: "D", 36_700: "B", 60_700: "C"}[acb]
    return {"answer": key, "computed": acb}


def q_f1c3_014():
    # Amend first, then BRS with timing items only
    acb = 52_500
    acb -= 250     # bank charges
    acb -= 5_000   # SI loan instalment
    acb += 750     # interest allowed
    acb -= 6_500   # dishonoured cheque
    pb = acb
    pb += 9_000    # unpresented cheques
    pb -= 13_500   # uncredited deposits
    key = {41_500: "A", 37_000: "B", 46_000: "C", 43_500: "D"}[pb]
    return {"answer": key, "computed": pb}


def q_f1c3_015():
    # Balance sheet shows the ADJUSTED cash book balance
    acb = 29_800
    acb -= 300     # bank charges
    acb += 900     # interest allowed
    # timing items (4,000 / 6,500) never enter the cash book
    key = {29_800: "D", 27_900: "A", 30_400: "C", 31_000: "B"}[acb]
    return {"answer": key, "computed": acb}


def q_f1c3_016():
    # Amended cash book from an overdraft, incl. own-error correction
    acb = -15_600
    acb -= 840     # interest on overdraft
    acb += 12_000  # direct deposit
    acb -= 2_400   # SI insurance premium
    acb += 3_500   # omitted deposit now entered (own error corrected)
    key = {-6_840: "A", -3_340: "D", -27_340: "C", -1_660: "B"}[acb]
    return {"answer": key, "computed": acb}


def q_f1c3_017():
    # Wrong-side error: receipt 4,200 credited → balance 2 × 4,200 too LOW
    effect = -2 * 4_200   # negative = too low
    key = {-4_200: "C", -8_400: "A", 4_200: "B", 8_400: "D"}[effect]
    return {"answer": key, "computed": effect}


def q_f1c3_018():
    # Wrong-amount error: cheque 5,630 recorded 6,530 → CB 900 too low → add 900
    adjustment = 6_530 - 5_630   # positive = add when walking CB → PB
    key = {900: "B", -900: "A", 1_800: "D", -1_800: "C"}[adjustment]
    return {"answer": key, "computed": adjustment}


def q_f1c3_019():
    # Wrong-column error: payment 2,750 missing from bank column → CB too high → less 2,750
    adjustment = -2_750
    key = {2_750: "A", -2_750: "C", -5_500: "B", 0: "D"}[adjustment]
    return {"answer": key, "computed": adjustment}


def q_f1c3_020():
    # Overcast debit side by 1,000 → CB too high → less 1,000
    adjustment = -1_000
    key = {-1_000: "D", 1_000: "C", -2_000: "A", 2_000: "B"}[adjustment]
    return {"answer": key, "computed": adjustment}


def q_f1c3_021():
    # Bank's wrong debit 3,600 → pass book stands lower
    pb = 50_000
    pb -= 3_600    # bank's own wrong debit, single-sized
    key = {53_600: "D", 50_000: "B", 42_800: "C", 46_400: "A"}[pb]
    return {"answer": key, "computed": pb}


def q_f1c3_022():
    # Combined errors then standard walk (CB favourable → PB)
    pb = 33_000
    pb += 2 * 2_900        # wrong side: cash book 2 × 2,900 too low
    pb += 4_810 - 4_180    # over-recorded payment: cash book 630 too low
    pb += 7_000            # unpresented cheques
    pb -= 9_400            # uncredited deposits
    key = {34_130: "D", 37_030: "B", 35_770: "C", 41_830: "A"}[pb]
    return {"answer": key, "computed": pb}


def q_f1c3_023():
    # PB favourable → CB with bank charges
    cb = 75_000
    cb -= 10_000   # unpresented cheques
    cb += 6_000    # uncredited deposits
    cb += 500      # bank charges (add back on the reverse walk)
    key = {78_500: "B", 71_500: "C", 70_500: "A", 59_500: "D"}[cb]
    return {"answer": key, "computed": cb}


def q_f1c3_024():
    # CB favourable → PB, bank-first items only
    pb = 22_000
    pb -= 150      # bank charges
    pb += 600      # interest allowed
    pb -= 2_000    # SI rent paid
    key = {23_550: "A", 19_250: "B", 20_450: "D", 24_450: "C"}[pb]
    return {"answer": key, "computed": pb}


def q_f1c3_025():
    # PB overdraft → CB with dishonour + charges
    cb = -12_400
    cb += 5_000    # dishonoured cheque (bank debit the cash book lacks: add back)
    cb += 100      # dishonour charges (same direction)
    cb -= 3_800    # unpresented cheques
    key = {-13_700: "D", -11_200: "C", 11_100: "B", -11_100: "A"}[cb]
    return {"answer": key, "computed": cb}


def q_f1c3_042():
    # BRS item = issued − presented (outstanding slice only)
    unpresented = 40_000 - 31_000
    key = {40_000: "A", 31_000: "C", 9_000: "B", 71_000: "D"}[unpresented]
    return {"answer": key, "computed": unpresented}
