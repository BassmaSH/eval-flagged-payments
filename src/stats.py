"""The three calculations behind "is this score reliable?", with the standard library only.

    exact_interval(14, 16)      ->  (0.617, 0.984)   the range for one score
    paired_p_value(14, 0)       ->  0.00012          two systems on the same cases
    cases_needed(margin=0.10)   ->  97               how many cases for a score within 10 points

Methods: the Clopper-Pearson interval, the exact McNemar test, and the usual sample-size formula
for a proportion. Code written by Claude Code on Nov 15, 2026, for the author.
"""

from math import ceil, comb
from statistics import NormalDist


def binomial_cdf(k: int, n: int, rate: float) -> float:
    """Returns the probability of k passes or fewer in n cases, when each passes with this rate."""
    return sum(comb(n, i) * rate**i * (1 - rate) ** (n - i) for i in range(k + 1))


def exact_interval(passed: int, total: int, level: float = 0.95) -> tuple[float, float]:
    """Returns the Clopper-Pearson interval for a pass rate: the rates that could plausibly give it.

    The low end is the rate at which this many passes or more would happen only (1 - level) / 2 of
    the time; the high end, the rate at which this many or fewer would. It never claims more
    certainty than the data gives, which is why it is the one to report on small samples.

    Args:
        passed: the number of cases passed.
        total: the number of cases.
        level: the confidence level, 0.95 by default.
    """
    tail = (1 - level) / 2

    def crossing(too_low: "callable") -> float:
        low, high = 0.0, 1.0
        for _ in range(60):  # halves the gap 60 times: far below any rounding shown
            middle = (low + high) / 2
            low, high = (middle, high) if too_low(middle) else (low, middle)
        return low

    lower = (
        0.0 if passed == 0 else crossing(lambda r: 1 - binomial_cdf(passed - 1, total, r) < tail)
    )
    upper = 1.0 if passed == total else crossing(lambda r: binomial_cdf(passed, total, r) > tail)
    return lower, upper


def paired_p_value(only_first: int, only_second: int) -> float:
    """Returns the exact McNemar p-value for two systems scored on the same cases.

    Cases both pass or both fail say nothing about which is better, so only the cases where they
    disagree count. If the two were equally good, each disagreement would go either way like a coin
    toss; the p-value is how often a split at least this uneven would then happen.

    Args:
        only_first: cases the first system passed and the second failed.
        only_second: cases the second system passed and the first failed.
    """
    disagreements = only_first + only_second
    if disagreements == 0:
        return 1.0
    return min(1.0, 2 * binomial_cdf(min(only_first, only_second), disagreements, 0.5))


def cases_needed(margin: float, rate: float = 0.5, level: float = 0.95) -> int:
    """Returns how many cases put a score within plus or minus margin (the planning formula).

    n = z² × rate × (1 − rate) ÷ margin². The default rate of 0.5 is the worst case, so the answer
    is safe whatever the true score turns out to be. It is a normal approximation, good for
    planning; report the exact interval once the cases are run.

    Args:
        margin: the half-width wanted, as a fraction (0.10 for 10 points).
        rate: the pass rate expected; 0.5 when unknown.
        level: the confidence level, 0.95 by default.
    """
    z = NormalDist().inv_cdf(1 - (1 - level) / 2)
    return ceil(z**2 * rate * (1 - rate) / margin**2)
