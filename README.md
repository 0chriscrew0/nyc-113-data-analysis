# Do Wealthier NYC Neighborhoods Get Faster City Services?

An analysis of NYC 311 service requests (2022-2025) testing whether resolution
time for the same complaint type varies with ZIP-level median household income.

**Status:** scaffolding. Acquisition and analysis haven't run yet.

## The question

Does the city resolve the same complaint faster in wealthier neighborhoods
than in poorer ones? See [`PLAN.md`](PLAN.md) for the full methodology,
hypotheses, and phase-by-phase TODO.

## Finding

_TBD. Will be filled in once the multivariate model (H4) is fit._

## Repo layout

```
data/
  raw/          # untouched downloads (gitignored)
  processed/    # cleaned/derived tables (gitignored)
  reference/    # small lookups committed to the repo (e.g. ZIP-to-income)
  README.md     # exact source URLs and download dates
sql/            # DuckDB SQL for aggregation
scripts/        # acquisition and cleaning scripts
notebooks/      # analysis narrative (Jupyter)
tableau/        # exported extracts for the dashboard build
```

## Tools

Python (pandas, numpy), DuckDB, SQL, scipy/statsmodels, Tableau Public, Jupyter.

## Reproduction

_TBD. Will be filled in once the acquisition scripts exist._

## Limitations

_TBD. See the "Out of scope" section of `PLAN.md` for the working list._
