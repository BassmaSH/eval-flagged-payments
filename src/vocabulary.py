"""Which laundering terms a text names: the dataset's eight network patterns, or the cash terms.

    named("a fan out, then layering", PATTERNS)  ->  ["fan-out"]

Each term is listed with the spellings counted for it. The lists were fixed on Nov 15, 2026, before
the knowledge probe was run (probe.py). Code written by Claude Code for the author.
"""

# The eight patterns planted in IBM's data (Altman et al., 2023), with the spellings counted.
# "stack" and "random" are also ordinary words: read the answer before trusting those two.
PATTERNS = {
    "fan-out": ["fan-out", "fan out", "fanout"],
    "fan-in": ["fan-in", "fan in", "fanin"],
    "cycle": ["cycle", "cyclic", "circular"],
    "scatter-gather": ["scatter-gather", "scatter gather", "scatter and gather"],
    "gather-scatter": ["gather-scatter", "gather scatter", "gather and scatter"],
    "stack": ["stack"],
    "bipartite": ["bipartite"],
    "random": ["random"],
}
# The classic three stages of laundering cash, and splitting deposits under a reporting limit.
CASH_TERMS = {
    "placement": ["placement"],
    "layering": ["layering"],
    "integration": ["integration"],
    "structuring": ["structuring"],
    "smurfing": ["smurfing", "smurf"],
}


def named(text: str, terms: dict[str, list[str]]) -> list[str]:
    """Returns the terms the text contains, in any of their spellings, in the order of the list."""
    lowered = text.lower()
    return [term for term, spellings in terms.items() if any(s in lowered for s in spellings)]
