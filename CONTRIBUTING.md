# Contributing

Thirteen guidelines for the code in this repo, and how each one is checked. They follow Google's
Python Style Guide, "Good Enough Practices in Scientific Computing" (Wilson et al., 2017), the Good
Research Code Handbook and the ML Code Completeness Checklist.

## Before you push

```bash
pip install ruff==0.17.5 pytest
ruff format .      # rewrites the files in the agreed style
ruff check .       # reports what breaks a rule
pytest -q          # 37 checks, no API call
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

"Review" means a person reads the change against the guideline: no tool checks it.

## Changing something that produces a number

The scores in the README depend on `aml_graders.py`, `golden.jsonl`, the files in `cases/` and
`keys/`, and the prompt in `system.py`. A change to any of them must show that the published
numbers still follow:

- `python report.py` grades every saved answer again. Its tables must match the README.
- `python prep/make_golden.py` must write the same `golden.jsonl`.
- `python run.py rule` must give the same table.
- A change to `prep/make_case.py` must rebuild the 36 files in `cases/` and `keys/` unchanged (the data:
  `prep/README.md`).

Saved answers in `results/` are never replaced. A new run gets its own name (`repeat2`, or a new
row in `VARIANTS`), and its prediction is written in `docs/NOTEBOOK.md` before it is run.

## Not covered

`evals_kit/` is a copy of [evals-kit](https://github.com/BassmaSH/evals-kit) and is excluded from
the linter here. Changes to it belong in that repo.
