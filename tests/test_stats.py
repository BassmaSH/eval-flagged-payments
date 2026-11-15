"""Tests for stats.py: the interval, the paired test and the sample size. No API call.

    python tests/test_stats.py
    pytest tests/test_stats.py

Plain asserts, like the other tests. Code written by Claude Code on Nov 15, 2026.
"""

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from stats import binomial_cdf, cases_needed, exact_interval, paired_p_value  # noqa: E402


def close(a: float, b: float, tolerance: float = 1e-6) -> bool:
    return abs(a - b) < tolerance


def test_no_pass_and_all_pass_match_their_closed_forms():
    """With 0 of n the upper end is 1 - 0.025^(1/n); with n of n the lower end is 0.025^(1/n)."""
    for n in (4, 16, 100):
        assert exact_interval(0, n)[0] == 0.0 and close(
            exact_interval(0, n)[1], 1 - 0.025 ** (1 / n)
        )
        assert exact_interval(n, n)[1] == 1.0 and close(exact_interval(n, n)[0], 0.025 ** (1 / n))


def test_each_end_leaves_exactly_the_tail_it_should():
    low, high = exact_interval(14, 16)
    assert close(1 - binomial_cdf(13, 16, low), 0.025), (
        "14 or more happens 2.5% of the time at the low end"
    )
    assert close(binomial_cdf(14, 16, high), 0.025), (
        "14 or fewer happens 2.5% of the time at the high end"
    )


def test_interval_is_symmetric_between_passes_and_failures():
    low, high = exact_interval(3, 10)
    mirror_low, mirror_high = exact_interval(7, 10)
    assert close(low, 1 - mirror_high) and close(high, 1 - mirror_low)


def test_interval_contains_the_score_and_narrows_with_more_cases():
    for passed, total in [(14, 16), (1, 16), (8, 16), (70, 80)]:
        low, high = exact_interval(passed, total)
        assert low < passed / total < high
    small, large = exact_interval(14, 16), exact_interval(140, 160)
    assert large[1] - large[0] < small[1] - small[0]


def test_the_ranges_quoted_in_the_readme():
    assert [round(100 * x) for x in exact_interval(14, 16)] == [62, 98]
    assert [round(100 * x) for x in exact_interval(0, 16)] == [0, 21]
    assert [round(100 * x) for x in exact_interval(8, 16)] == [25, 75]


def test_paired_p_value():
    assert paired_p_value(0, 0) == 1.0, "no disagreement says nothing"
    assert paired_p_value(5, 5) == 1.0, "an even split is what equal systems give"
    assert close(paired_p_value(14, 0), 2 * 0.5**14), "14 to 0: both tails of 14 coin tosses"
    assert paired_p_value(14, 0) == paired_p_value(0, 14)
    assert paired_p_value(2, 0) == 0.5, "2 to 0 is far too few to conclude"


def test_cases_needed():
    assert cases_needed(0.10) == 97
    assert cases_needed(0.05) == 385
    assert cases_needed(0.10, rate=0.9) < cases_needed(0.10), (
        "a score near 0 or 1 needs fewer cases"
    )
    assert cases_needed(0.05) > 3 * cases_needed(0.10), "half the margin costs four times the cases"


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    print(f"testing stats.py: {len(tests)} checks")
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  [ok ] {name}")
        except Exception:
            failed += 1
            print(f"  [FAIL] {name}")
            traceback.print_exc()
    print("\nALL PASS" if not failed else f"\n{failed} FAILED")
    raise SystemExit(1 if failed else 0)
