"""Deflated & Probabilistic Sharpe Ratios (Bailey & López de Prado, 2014).

Reference: D. H. Bailey and M. López de Prado, "The Deflated Sharpe Ratio:
Correcting for Selection Bias, Backtest Overfitting and Non-Normality",
Journal of Portfolio Management, 2014.

The DSR answers: given that a strategy was *selected* as the best of ``N``
trials, and given the non-normal shape of its returns, what is the probability
its TRUE Sharpe ratio exceeds an expected-maximum benchmark ``SR0`` produced by
that very selection process? A DSR near 1 is strong evidence of skill; a DSR
near 0.5 says the result is consistent with luck under multiple testing.

UNITS — read carefully, these are the two easiest things to get wrong:

* **All Sharpe quantities are PER-PERIOD (non-annualized).** If you have an
  annualized Sharpe of 2.5 on daily data, pass ``sr = 2.5 / sqrt(252)`` (or
  whatever bars/year applies), NOT 2.5. Likewise ``sr_var_across_trials`` is the
  variance of PER-PERIOD trial Sharpes.
* **``kurt`` is NON-EXCESS kurtosis** — a normal distribution has ``kurt == 3``
  (not 0). Pass the raw fourth-moment kurtosis, not Fisher/excess kurtosis.

Edge handling (documented, not faked): non-finite inputs, ``n_trials < 1`` or
``t < 2`` return NaN. When the non-normality adjustment radicand
``1 - skew*sr + (kurt-1)/4 * sr^2`` is <= 0 (an extreme skew/kurtosis regime
where the PSR variance estimator breaks down) the result is NaN — the caller is
flagged rather than handed a fabricated probability.
"""

from __future__ import annotations

import math

from scipy.stats import norm

# Euler-Mascheroni constant, used in the expected-maximum-Sharpe estimator.
_EULER_MASCHERONI = 0.5772156649015329


def probabilistic_sharpe_ratio(
    sr: float, sr_benchmark: float, t: int, skew: float, kurt: float
) -> float:
    """Probabilistic Sharpe Ratio: P(true SR > ``sr_benchmark``).

    Parameters
    ----------
    sr
        Observed PER-PERIOD Sharpe ratio.
    sr_benchmark
        PER-PERIOD Sharpe threshold to beat (0 for "better than nothing").
    t
        Number of return observations (bars) the Sharpe was estimated over.
    skew
        Skewness of the returns.
    kurt
        NON-EXCESS kurtosis of the returns (normal == 3).

    Returns
    -------
    float
        Probability in ``[0, 1]``; NaN on degenerate/undefined inputs.
    """
    if not all(math.isfinite(x) for x in (sr, sr_benchmark, skew, kurt)):
        return math.nan
    if t < 2:
        return math.nan

    # Variance of the Sharpe estimator under non-normal returns (Mertens/Lo):
    # 1 - skew*SR + (kurt-1)/4 * SR^2. Negative-skew/fat-tail returns inflate it.
    radicand = 1.0 - skew * sr + ((kurt - 1.0) / 4.0) * sr * sr
    if radicand <= 0.0:
        # Extreme higher-moment regime: the estimator is not defined; flag it.
        return math.nan

    z = (sr - sr_benchmark) * math.sqrt(t - 1) / math.sqrt(radicand)
    return float(norm.cdf(z))


def _expected_max_sharpe_z(n_trials: int) -> float:
    """Estimated E[max of N iid standard-normal Sharpes], in std units.

    Bailey-LdP closed form: ``(1 - γ)·Φ⁻¹(1 - 1/N) + γ·Φ⁻¹(1 - 1/(N·e))`` with
    γ the Euler-Mascheroni constant. For ``N == 1`` there is no selection, so
    the expected maximum of a single draw is 0 (the formula's ``Φ⁻¹(0)`` limit
    is handled explicitly).
    """
    if n_trials == 1:
        return 0.0
    gamma = _EULER_MASCHERONI
    z1 = norm.ppf(1.0 - 1.0 / n_trials)
    z2 = norm.ppf(1.0 - 1.0 / (n_trials * math.e))
    return float((1.0 - gamma) * z1 + gamma * z2)


def deflated_sharpe_ratio(
    sr: float,
    n_trials: int,
    t: int,
    skew: float,
    kurt: float,
    sr_var_across_trials: float,
) -> float:
    """Deflated Sharpe Ratio — PSR against a selection-adjusted benchmark ``SR0``.

    ``SR0 = sqrt(sr_var_across_trials) · E[max of N standard-normal Sharpes]``,
    the Sharpe you'd expect the *best* of ``N`` random trials to show by luck
    alone. DSR is then ``PSR(sr, SR0)``. As ``N`` grows, ``SR0`` grows and the
    DSR falls — the deflation for multiple testing.

    Parameters
    ----------
    sr
        Observed PER-PERIOD Sharpe of the selected strategy.
    n_trials
        Number of independent configurations tried (``N``). ``N < 1`` -> NaN.
    t
        Number of return observations. ``t < 2`` -> NaN.
    skew, kurt
        Returns skewness and NON-EXCESS kurtosis (normal == 3).
    sr_var_across_trials
        Variance of the PER-PERIOD Sharpe ratios across the ``N`` trials.

    Returns
    -------
    float
        Probability in ``[0, 1]``; NaN on degenerate/undefined inputs.
    """
    inputs_finite = all(
        math.isfinite(x) for x in (sr, t, skew, kurt, sr_var_across_trials)
    )
    if not inputs_finite:
        return math.nan
    if n_trials < 1 or t < 2:
        return math.nan
    if sr_var_across_trials < 0:
        return math.nan

    sr0 = math.sqrt(sr_var_across_trials) * _expected_max_sharpe_z(n_trials)
    return probabilistic_sharpe_ratio(sr, sr0, t, skew, kurt)
