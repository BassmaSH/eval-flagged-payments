"""Tests for src/vocabulary.py: which laundering terms a text names. No API call.

    python tests/test_vocabulary.py
    pytest tests/test_vocabulary.py

Plain asserts, like the other tests. Code written by Claude Code on Nov 15, 2026.
"""

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vocabulary import CASH_TERMS, PATTERNS, named  # noqa: E402


def test_every_spelling_of_a_pattern_counts_once():
    assert named("A Fan Out, then a fan-out and a fanout.", PATTERNS) == ["fan-out"]


def test_fan_in_and_fan_out_are_told_apart():
    assert named("money fans in: a fan-in", PATTERNS) == ["fan-in"]
    assert named("a fan-out only", PATTERNS) == ["fan-out"]


def test_the_two_compound_patterns_are_told_apart():
    assert named("scatter-gather", PATTERNS) == ["scatter-gather"]
    assert named("gather-scatter", PATTERNS) == ["gather-scatter"]


def test_all_eight_patterns_can_be_named():
    text = "fan-out, fan-in, cycle, scatter-gather, gather-scatter, stack, bipartite, random"
    assert named(text, PATTERNS) == list(PATTERNS) and len(PATTERNS) == 8


def test_cash_terms_and_network_patterns_are_counted_separately():
    text = "Placement, layering and integration; structuring is also called smurfing."
    assert named(text, CASH_TERMS) == list(CASH_TERMS)
    assert named(text, PATTERNS) == []


def test_a_text_that_names_nothing():
    assert named("The account pays the same bill every day.", PATTERNS) == []


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    print(f"testing vocabulary.py: {len(tests)} checks")
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
