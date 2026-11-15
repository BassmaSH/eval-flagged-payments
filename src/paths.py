"""Where things are in the repo, in one place.

A case is named by its path inside benchmark/ ("cases/P01.md"), as golden.jsonl writes it.

Code written by Claude Code on Nov 15, 2026.
"""

from pathlib import Path

ROOT = Path(__file__).parent.parent
BENCHMARK = ROOT / "benchmark"  # golden.jsonl, cases/, keys/
GOLDEN = BENCHMARK / "golden.jsonl"
VARIANTS_DIR = ROOT / "src" / "variants"  # paragraphs added to the prompt
RESULTS = ROOT / "results"  # every saved answer
