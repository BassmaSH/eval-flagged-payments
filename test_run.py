"""Tests for run.py: reading the command line and the VARIANTS table. No API call.

    python test_run.py
    pytest test_run.py

Plain asserts, like test_aml_graders.py. Code written by Claude Code on Nov 15, 2026.
"""

import inspect
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import run  # noqa: E402


def exits(argv: list[str]) -> bool:
    """True when read_arguments refuses this command line."""
    try:
        run.read_arguments(argv)
    except SystemExit:
        return True
    return False


def test_model_alone_is_the_plain_run():
    assert run.read_arguments(["mistral-large-4"]) == ("mistral-large-4", "", "")


def test_variant_and_repeat_are_read_in_either_combination():
    assert run.read_arguments(["m", "method"]) == ("m", "method", "")
    assert run.read_arguments(["m", "repeat2"]) == ("m", "", "repeat2")
    assert run.read_arguments(["m", "method", "repeat3"]) == ("m", "method", "repeat3")


def test_a_mistyped_variant_is_refused_before_any_call():
    assert exits(["m", "methd"])
    assert exits(["m", "method", "extra-word"])
    assert exits([])


def test_every_paragraph_named_in_the_table_exists():
    for name, row in run.VARIANTS.items():
        if "extra" in row:
            assert (HERE / "variants" / f"{row['extra']}.txt").is_file(), name


def test_every_file_in_variants_is_used_by_the_table():
    used = {row["extra"] for row in run.VARIANTS.values() if "extra" in row}
    assert {p.stem for p in (HERE / "variants").glob("*.txt")} == used


def test_every_saved_run_is_a_variant_in_the_table():
    """A results file whose variant is not in the table could not be run again."""
    for path in (HERE / "results").glob("*.json"):
        if (
            path.name.count(".") > 1 or path.stem == "rule"
        ):  # .meta.json and .thinking.json; the rule
            continue
        parts = path.stem.split("+")[1:]
        variant = "+".join(p for p in parts if not p.startswith("repeat"))
        assert variant in run.VARIANTS, path.name


def test_variant_settings_reads_the_paragraph_and_keeps_the_rest():
    settings = run.variant_settings("method-neutral")
    assert settings["extra"] == (HERE / "variants" / "method.txt").read_text().strip()
    assert settings["neutral"] is True
    assert run.variant_settings("") == {}
    assert run.variant_settings("schema-temp1") == {"schema": True, "temperature": 1}


def test_variant_settings_does_not_change_the_table():
    before = {name: dict(row) for name, row in run.VARIANTS.items()}
    run.variant_settings("method")
    assert before == run.VARIANTS


def test_the_table_only_uses_settings_the_system_accepts():
    accepted = {
        "extra",
        "schema",
        "temperature",
        "neutral",
    }  # ModelSystem's arguments, besides the model
    for name, row in run.VARIANTS.items():
        assert set(row) <= accepted, name
    try:
        from system import ModelSystem  # needs mistralai: checked only where it is installed
    except ImportError:
        return
    assert accepted == set(inspect.signature(ModelSystem.__init__).parameters) - {"self", "model"}


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    print(f"testing run.py: {len(tests)} checks")
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
