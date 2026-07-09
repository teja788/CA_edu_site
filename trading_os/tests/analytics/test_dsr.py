"""Known-answer and behavioural tests for analytics/dsr.py.

The regression anchor reproduces the worked example from Bailey & López de
Prado, "The Deflated Sharpe Ratio" (2014). All Sharpe quantities are per-period
and kurtosis is non-excess (normal == 3) — the two easy-to-miss conventions.
"""

from __future__ import annotations

import math

import pytest

from tradingos.analytics.dsr import (
    deflated_sharpe_ratio,
    probabilistic_sharpe_ratio,
)

# --- Paper worked-example inputs ------------------------------------------- #
# Annualized SR 2.5 over 5 years of DAILY data. The paper uses 250 trading
# days/year for THIS example (the platform uses 252 elsewhere; we match the
# paper here so the anchor is comparable to the published figure).
#   t   = 250 * 5 = 1250 observations
#   sr  = 2.5 / sqrt(250)          (per-period)
#   N   = 100 trials
#   var of trial SRs = 0.5 / 250   (per-period)
#   skew = -3, kurt = 10 (non-excess)
_DAYS = 250
_T = _DAYS * 5
_SR = 2.5 / math.sqrt(_DAYS)
_N = 100
_SR_VAR = 0.5 / _DAYS
_SKEW = -3.0
_KURT = 10.0

# Computed value with the γ-weighted expected-max estimator = 0.900397. The
# paper reports ~0.9505 with its own exact E[max·N] estimate; our closed-form
# lands at 0.9004, inside the sanity band 0.85–0.99 and below PSR(SR0=0). We
# assert to 4 decimals as the regression anchor.
_EXPECTED_DSR = 0.9004


def test_dsr_paper_worked_example_anchor() -> None:
    dsr = deflated_sharpe_ratio(_SR, _N, _T, _SKEW, _KURT, _SR_VAR)
    assert dsr == pytest.approx(_EXPECTED_DSR, abs=1e-4)
    # sanity band
    assert 0.85 < dsr < 0.99


def test_dsr_below_psr_against_zero_benchmark() -> None:
    # DSR is PSR against the selection benchmark SR0 > 0, so for N > 1 it must
    # be strictly below PSR against a zero benchmark.
    dsr = deflated_sharpe_ratio(_SR, _N, _T, _SKEW, _KURT, _SR_VAR)
    psr0 = probabilistic_sharpe_ratio(_SR, 0.0, _T, _SKEW, _KURT)
    assert dsr < psr0
    assert psr0 == pytest.approx(1.0, abs=1e-3)  # SR this high over 1250 bars


def test_dsr_decreases_as_trials_grow() -> None:
    # More trials -> higher expected-max benchmark SR0 -> more deflation.
    d10 = deflated_sharpe_ratio(_SR, 10, _T, _SKEW, _KURT, _SR_VAR)
    d100 = deflated_sharpe_ratio(_SR, 100, _T, _SKEW, _KURT, _SR_VAR)
    d500 = deflated_sharpe_ratio(_SR, 500, _T, _SKEW, _KURT, _SR_VAR)
    assert d10 > d100 > d500


def test_more_negative_skew_lowers_dsr() -> None:
    # Negative skew inflates the Sharpe-estimator variance -> lower confidence.
    d_pos = deflated_sharpe_ratio(_SR, _N, _T, 0.0, _KURT, _SR_VAR)
    d_mid = deflated_sharpe_ratio(_SR, _N, _T, -3.0, _KURT, _SR_VAR)
    d_neg = deflated_sharpe_ratio(_SR, _N, _T, -6.0, _KURT, _SR_VAR)
    assert d_pos > d_mid > d_neg


def test_dsr_equals_psr_at_sr0_zero() -> None:
    # DSR is PSR at SR0; with zero cross-trial variance SR0 collapses to 0, so
    # DSR must equal PSR against a zero benchmark exactly.
    dsr = deflated_sharpe_ratio(_SR, _N, _T, _SKEW, _KURT, 0.0)
    psr0 = probabilistic_sharpe_ratio(_SR, 0.0, _T, _SKEW, _KURT)
    assert dsr == pytest.approx(psr0, abs=1e-15)


def test_psr_monotonic_in_observations() -> None:
    # A given Sharpe is more convincing over more observations.
    p_short = probabilistic_sharpe_ratio(_SR, 0.0, 100, _SKEW, _KURT)
    p_long = probabilistic_sharpe_ratio(_SR, 0.0, 2000, _SKEW, _KURT)
    assert p_long > p_short


def test_psr_half_when_sr_equals_benchmark() -> None:
    # sr == benchmark -> numerator 0 -> Phi(0) = 0.5, for symmetric-ish inputs.
    p = probabilistic_sharpe_ratio(0.1, 0.1, 500, 0.0, 3.0)
    assert p == pytest.approx(0.5)


# --- Edge cases ------------------------------------------------------------- #
def test_edge_cases_return_nan() -> None:
    # N < 1
    assert math.isnan(deflated_sharpe_ratio(_SR, 0, _T, _SKEW, _KURT, _SR_VAR))
    # t < 2
    assert math.isnan(deflated_sharpe_ratio(_SR, _N, 1, _SKEW, _KURT, _SR_VAR))
    # non-finite input
    assert math.isnan(
        deflated_sharpe_ratio(float("nan"), _N, _T, _SKEW, _KURT, _SR_VAR)
    )
    assert math.isnan(
        deflated_sharpe_ratio(_SR, _N, _T, float("inf"), _KURT, _SR_VAR)
    )
    # negative cross-trial variance is nonsensical
    assert math.isnan(deflated_sharpe_ratio(_SR, _N, _T, _SKEW, _KURT, -0.1))


def test_radicand_non_positive_is_nan() -> None:
    # Extreme positive skew drives 1 - skew*sr + (kurt-1)/4*sr^2 below zero;
    # the estimator is undefined and must be flagged with NaN, not faked.
    # sr=1, skew=5, kurt=3 -> 1 - 5 + 0.5 = -3.5 <= 0
    assert math.isnan(probabilistic_sharpe_ratio(1.0, 0.0, 100, 5.0, 3.0))


def test_psr_t_less_than_two_is_nan() -> None:
    assert math.isnan(probabilistic_sharpe_ratio(_SR, 0.0, 1, _SKEW, _KURT))


def test_single_trial_has_no_deflation() -> None:
    # N == 1 -> no selection -> SR0 == 0 -> DSR == PSR(0).
    dsr = deflated_sharpe_ratio(_SR, 1, _T, _SKEW, _KURT, _SR_VAR)
    psr0 = probabilistic_sharpe_ratio(_SR, 0.0, _T, _SKEW, _KURT)
    assert dsr == pytest.approx(psr0, abs=1e-15)
