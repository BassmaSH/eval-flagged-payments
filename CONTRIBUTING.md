# Contributing

Fourteen guidelines for the code in this repo, and how each one is checked. They follow Google's
Python Style Guide, "Good Enough Practices in Scientific Computing" (Wilson et al., 2017), the Good
Research Code Handbook and the ML Code Completeness Checklist.

## Before you push

```bash
pip install ruff==0.17.5 pytest
ruff format .      # rewrites the files in the agreed style
ruff check .       # reports what breaks a rule
pytest -q          # 48 checks, no API call
python report.py   # the README's tables, rebuilt from results/
```

The same five steps run on every push (`.github/workflows/check.yml`). The settings are in
`pyproject.toml`.

## The guidelines

| # | guideline | checked by |
|---|---|---|
| 1 | One job per function, about 40 lines at most | ruff: 40 statements, 10 branches, 6 arguments |
| 2 | A choice between named things is a table, not an `if` chain (`GRADERS`, `VARIANTS`, `COMMANDS`) | review |
| 3 | Nothing runs at import: every script has a `main()` | review |
| 4 | Each piece of logic lives in one place | review |
| 5 | A file opens with what it does, how to run it, and who wrote it | ruff: a docstring is required |
| 6 | Comments say why, never what | review |
| 7 | Every rule behind a published number has a test | review; the tests run on every push |
| 8 | A formatter and a linter decide style | ruff, 100 characters |
| 9 | Computing is kept apart from reading and writing files | review |
| 10 | No state shared between functions behind their backs | ruff flags `global`; review |
| 11 | Numbers, columns and paths have names | review |
| 12 | Every table in the README has the command that rebuilds it; dependencies are written down | `report.py` runs on every push |
| 13 | Type hints on every function; a docstring with `Args:` and `Returns:` where the names do not say it | ruff |
| 14 | One folder per role, one level deep; only the commands a reader runs sit in the root | review |

"Review" means a person reads the change against the guideline: no tool checks it.

## Where a file goes

| folder | role | goes here |
|---|---|---|
| root | what a reader runs | `run.py`, `report.py`, and the files that describe the repo |
| `src/` | what the commands are made of | the systems, the graders, the statistics, the prompt variants |
| `benchmark/` | the test itself | the cases, the keys, `golden.jsonl` |
| `results/` | what came out | one file of answers per run, never edited |
| `prep/` | how the test was built | the scripts that make `benchmark/` from the source data |
| `tests/` | how the code is checked | one file per module tested |
| `docs/` | the record | the notebook and longer write-ups |

`run.py`, `report.py` and the files in `src/` take these folders from `src/paths.py`.

## Changing something that produces a number

The scores in the README depend on `src/aml_graders.py`, everything in `benchmark/`, and the prompt
in `src/system.py`. A change to any of them must show that the published
numbers still follow:

- `python report.py` grades every saved answer again. Its tables must match the README.
- `python prep/make_golden.py` must write the same `benchmark/golden.jsonl`.
- `python run.py rule` must give the same table.
- A change to `prep/make_case.py` must rebuild the 36 files in `benchmark/cases/` and
  `benchmark/keys/` unchanged (the data: `prep/README.md`).

Saved answers in `results/` are never replaced, and a run is written to disk line by line: one
that stops is resumed by the same command. A new run gets its own name (`repeat2`, or a new
row in `VARIANTS`), and its prediction is written in `docs/NOTEBOOK.md` before it is run.

## Not covered

`src/evals_kit/` is a copy of [evals-kit](https://github.com/BassmaSH/evals-kit) and is excluded from
the linter here. Changes to it belong in that repo.
