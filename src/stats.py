"""
Statistical utility functions for conversion funnels and risk analysis.
Includes Wilson Score 95% Confidence Intervals and Two-Proportion Hypothesis Tests.
"""

from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
from scipy import stats


def wilson_score_interval(
    successes: int | float | np.ndarray | pd.Series,
    trials: int | float | np.ndarray | pd.Series,
    confidence: float = 0.95
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate the Wilson Score Interval for binomial proportions.
    Preferred over the normal approximation (Wald interval) because it handles
    extreme proportions (close to 0 or 1) and small sample sizes without exceeding [0, 1].

    Parameters
    ----------
    successes : Number of successes (k)
    trials : Total number of trials (n)
    confidence : Desired confidence level (default 0.95 for z ~ 1.95996)

    Returns
    -------
    (center, lower_bound, upper_bound) as numpy arrays or floats
    """
    k = np.asarray(successes, dtype=float)
    n = np.asarray(trials, dtype=float)

    # Avoid zero division
    zero_mask = n == 0
    n_safe = np.where(zero_mask, 1.0, n)
    p_hat = np.where(zero_mask, 0.0, k / n_safe)

    alpha = 1.0 - confidence
    z = stats.norm.ppf(1.0 - alpha / 2.0)
    z_sq = z ** 2

    denominator = 1.0 + z_sq / n_safe
    center_adjusted = (p_hat + z_sq / (2.0 * n_safe)) / denominator

    # Standard error term inside square root
    variance_term = (p_hat * (1.0 - p_hat) / n_safe) + (z_sq / (4.0 * (n_safe ** 2)))
    # Clip negative values resulting from floating-point inaccuracies
    variance_term = np.maximum(0.0, variance_term)
    margin = (z / denominator) * np.sqrt(variance_term)

    lower = np.maximum(0.0, center_adjusted - margin)
    upper = np.minimum(1.0, center_adjusted + margin)

    # When successes == 0, lower bound is analytically 0.0
    lower = np.where(k == 0, 0.0, lower)
    # When successes == trials, upper bound is analytically 1.0
    upper = np.where(k == n, 1.0, upper)

    # Zero trials should yield 0 for all
    p_hat = np.where(zero_mask, 0.0, p_hat)
    lower = np.where(zero_mask, 0.0, lower)
    upper = np.where(zero_mask, 0.0, upper)

    if np.ndim(successes) == 0:
        return float(p_hat), float(lower), float(upper)
    return p_hat, lower, upper


def two_proportion_z_test(
    count1: int,
    nobs1: int,
    count2: int,
    nobs2: int
) -> Dict[str, Any]:
    """
    Perform a two-sample pooled z-test for comparing two independent conversion proportions.
    
    H0: p1 = p2
    H1: p1 != p2 (two-tailed)

    Returns
    -------
    dict with p1, p2, diff, z_stat, p_value, is_significant (at alpha=0.05)
    """
    if nobs1 == 0 or nobs2 == 0:
        return {
            "p1": 0.0, "p2": 0.0, "diff": 0.0,
            "z_stat": 0.0, "p_value": 1.0, "is_significant": False
        }

    p1 = count1 / nobs1
    p2 = count2 / nobs2
    diff = p1 - p2

    p_pooled = (count1 + count2) / (nobs1 + nobs2)
    se_pooled = np.sqrt(p_pooled * (1.0 - p_pooled) * (1.0 / nobs1 + 1.0 / nobs2))

    if se_pooled == 0:
        z_stat = 0.0
        p_val = 1.0
    else:
        z_stat = diff / se_pooled
        p_val = 2.0 * (1.0 - stats.norm.cdf(abs(z_stat)))

    return {
        "p1": round(float(p1), 4),
        "p2": round(float(p2), 4),
        "diff": round(float(diff), 4),
        "z_stat": round(float(z_stat), 4),
        "p_value": float(p_val),
        "is_significant": bool(p_val < 0.05)
    }
