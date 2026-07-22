# Do Wealthier NYC Neighborhoods Get Faster City Services?

An analysis of NYC 311 service requests (2022–2025) testing whether resolution
time for the same complaint type varies with ZIP-level median household income.

**Status:** scaffolding — acquisition and analysis not yet run.

## The question

Does the city resolve the same complaint faster in wealthier neighborhoods
than in poorer ones? See [`PLAN.md`](PLAN.md) for the full methodology,
hypotheses, and phase-by-phase TODO.

## Finding

_TBD — filled in once the H4 multivariate model is fit._

## Repo layout

```
data/
  raw/          # untouched downloads (gitignored)
  processed/    # cleaned/derived tables (gitignored)
  reference/    # small lookups committed to the repo (e.g. ZIP→income)
  README.md     # exact source URLs + download dates
sql/            # DuckDB SQL for aggregation
scripts/        # acquisition + cleaning scripts
notebooks/      # analysis narrative (Jupyter)
tableau/        # exported extracts for the dashboard build
```

## Tools

Python (pandas, numpy), DuckDB, SQL, scipy/statsmodels, Tableau Public, Jupyter.

## Reproduction

_TBD — filled in once acquisition scripts exist._

## Limitations

_TBD — see `PLAN.md` §Out of scope for the working list._
