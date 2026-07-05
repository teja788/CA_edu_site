"""Composite scoring: weighted mean over six 0-10 dimensions."""

DIMENSIONS = ["long_term_value", "ease", "monetization", "personal_fit", "defensibility", "impact"]

DEFAULT_WEIGHTS = {
    "long_term_value": 0.25,
    "ease": 0.10,
    "monetization": 0.20,
    "personal_fit": 0.15,
    "defensibility": 0.10,
    "impact": 0.20,
}


def composite(scores: dict, weights: dict) -> float:
    """Weighted mean over the dimensions that have been scored (0-10 scale)."""
    scored = [d for d in DIMENSIONS if scores.get(d) is not None]
    total_weight = sum(weights.get(d, 0) for d in scored)
    if not scored or total_weight <= 0:
        return 0.0
    return round(sum(scores[d] * weights.get(d, 0) for d in scored) / total_weight, 2)
