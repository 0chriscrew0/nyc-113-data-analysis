# Project Plan

*An analysis of NYC 311 service requests using SQL, DuckDB, Python, and Tableau.*

**Core question:** Does the city resolve the same complaint faster in wealthier neighborhoods than in poorer ones?

> **Internal working title vs. public title.** Use the question above as the repo/dashboard/portfolio headline, since it's what makes someone click. "Response time equity analysis" is the description, not the hook.

---

## 1. Scope

### In scope
- **Dataset:** NYC 311 Service Requests from 2010 to Present (NYC Open Data, Socrata ID `erm2-nwe9`). Free, no login, API and bulk CSV.
- **Time window:** 2022-01-01 through 2025-12-31 (4 full years). Recent enough to be relevant, long enough to check whether any gap is stable or shrinking.
- **Geography:** All five boroughs, aggregated to ZIP code (`incident_zip`).
- **Complaint types:** Restricted to 5-8 high-volume, agency-consistent types so comparisons are apples-to-apples. Candidates:
  - Heat/Hot Water (HPD)
  - Noise - Residential (NYPD)
  - Illegal Parking (NYPD)
  - Street Condition / Pothole (DOT)
  - Rodent (DOHMH)
  - Water System (DEP)
- **Primary metric:** Resolution time = `closed_date` minus `created_date`, in hours.
- **Comparison variable:** Median household income by ZIP (ACS 5-Year Estimates, table B19013, ZCTA level).

### Out of scope (state this explicitly in the write-up)
- Causal claims. This is an observational association study, not a causal one.
- Complaint types with fewer than ~1,000 records in the window.
- Records missing `closed_date` (analyzed separately as a *non-closure rate*, not dropped silently; see Hypothesis 3).
- Any predictive modeling. This is an inference/measurement project, not an ML project.

### Single-dataset note
The 311 file is the only substantive dataset. Income enters as a small ZIP-to-median-income lookup (~180 rows). To keep this strictly one-source, borough or community board could substitute for income as the grouping variable; the analysis structure would stay identical, the framing would shift to "geographic equity" rather than "income equity," and it would lose some punch. Better to keep the ACS join and be transparent about it.

---

## 2. Hypotheses

Each is falsifiable and has a stated decision rule.

**H1, primary.** For a fixed complaint type, median resolution time is negatively correlated with ZIP-level median household income.
*Test:* Spearman rank correlation between ZIP median income and ZIP median resolution time, computed within each complaint type.
*Decision rule:* Reject the null if ρ is negative with p < 0.05 in a majority of complaint types studied.

**H2, the confound check.** Any raw citywide gap is substantially explained by *complaint mix*, not differential treatment. Poorer ZIPs generate more Heat/Hot Water complaints (slow, landlord-dependent); wealthier ZIPs generate more Illegal Parking (fast, ticket-and-done).
*Test:* Compare the raw citywide income-response gap against the gap after stratifying by complaint type.
*Why this matters:* If H2 holds and H1 fails, that's a genuinely interesting finding and a stronger portfolio piece than confirming a naive gap. Not a failed project.

**H3, non-closure.** The share of requests never closed (no `closed_date` after 12 months) is higher in lower-income ZIPs.
*Test:* Logistic regression of closure-within-365-days on log income, controlling for complaint type.
*Why:* Selection bias in the other direction. If slow tickets in poor ZIPs are disproportionately never closed at all, median resolution time among *closed* tickets will understate the gap.

**H4, the multivariate test. This is the headline result.**
H1 through H3 are all pairwise. Pairwise relationships aren't a conclusion, because income is correlated with borough, complaint mix, and reporting behavior simultaneously. The project's actual finding comes from one model:

```
log(resolution_hours) ~ log(median_income)
                      + complaint_type
                      + borough
                      + year
                      + reporting_channel
```

*Method:* OLS on log-transformed resolution hours (log because the distribution is heavily right-skewed; a GLM with a gamma family and log link is an acceptable alternative, pick one and justify it).
*Decision rule:* Report the income coefficient with its confidence interval, before and after adding controls.
*Why this is the point:* It lets me write one of these two sentences, and either is a real conclusion:
- *"After controlling for complaint type and borough, income was no longer a significant predictor of resolution time. The apparent gap is a complaint-mix effect."*
- *"Income remained significant after controls: a 10% increase in ZIP median income was associated with an X% decrease in resolution time."*

Simple correlations can't produce either sentence. Don't ship this project without this model.

**Reporting channel, a covariate, not a hypothesis.**
Whether `open_data_channel_type` (phone/app/online) varies by income is mildly interesting but not central, and a full standalone analysis of it would be scope creep. Include it as a covariate in H4's model and report whether it mattered. One paragraph, not a section.

**Optional stretch: survival analysis.**
H3 (non-closure) and H1 (resolution time) are really the same problem: never-closed tickets are *right-censored observations*, and dropping them biases the median downward unevenly across ZIPs. A Cox proportional hazards model handles both at once and is the statistically correct treatment. This is above the bar for a data analyst portfolio, so treat it as a bonus: if it happens, it's a genuinely strong differentiator and a good interview topic. If time is tight, H3 plus H4 as specified is sufficient, but mention the censoring issue in the limitations section either way, since noticing it is most of the credit.

---

## 3. Tools

| Tool | Role in this project |
|---|---|
| **Python (pandas, numpy)** | Cleaning, feature engineering, statistical tests |
| **DuckDB** | Query the full multi-GB CSV without loading into memory. Reads CSV/Parquet directly with SQL. The right call at 30M+ rows. |
| **SQL** | All aggregation logic, written in SQL rather than pandas groupbys, since it reads more clearly in a portfolio. |
| **scipy / statsmodels** | Spearman correlation, logistic regression, confidence intervals |
| **Tableau Public** | The primary deliverable. Choropleth map of NYC ZIPs colored by median response time, with complaint-type filter; scatter of income vs. response time; small-multiples trend by year. Published publicly and linked from the portfolio site. |
| **Jupyter** | Analysis narrative and methodology transparency |
| **Git / GitHub** | Repo with README, notebook, SQL scripts, and a link to the Tableau dashboard |

**Note on Tableau:** Tableau Public can't handle 30M rows well. All heavy aggregation happens in DuckDB, exported as a pre-aggregated extract (roughly ZIP by complaint type by year by metrics, a few thousand rows). Worth a paragraph in the README, since "aggregated upstream so the BI layer stayed fast" is a real engineering judgment call.

---

## 4. Step-by-step TODO

### Phase 1: Acquisition
- [x] Download the 311 dataset. Two options: (a) NYC Open Data export UI, (b) Socrata API with `$where=created_date between '2022-01-01' and '2025-12-31'` and pagination. API is cleaner and reproducible, so script it. Done via `scripts/download_311.py`, 13,506,490 rows.
- [x] Verify row count and date coverage against the portal's stated totals. Matches the API's `count(*)` exactly.
- [x] Convert CSV to Parquet immediately (`duckdb` one-liner). Cuts file size ~5x and speeds every subsequent query. 2.3 GB CSV to 480 MB Parquet.
- [x] Download ACS B19013 median household income by ZCTA from data.census.gov or the Census API. Done via `scripts/download_acs_income.py`, 192 NYC ZCTAs in `data/reference/nyc_zcta_median_income.csv`.
- [x] Commit a `data/README.md` documenting exact source URLs and download date. Do not commit the raw data.

### Phase 2: Cleaning
- [ ] Profile nulls across all columns; document which fields are unreliable.
- [ ] Parse `created_date` and `closed_date` as datetimes; confirm timezone handling.
- [ ] **Flag and quarantine bad rows:** `closed_date` earlier than `created_date` (data entry errors), resolution times under 1 minute (auto-closures), resolution times over 365 days (stale tickets). Record how many of each. Don't delete silently.
- [ ] Normalize `incident_zip` (strip ZIP+4, drop non-NYC ZIPs, handle whitespace/casing).
- [ ] Standardize `complaint_type`. There are near-duplicate labels across years (e.g. "Noise - Residential" vs older variants). Build an explicit mapping table.
- [ ] Create `resolution_hours` and a boolean `closed_within_365d`.
- [ ] Write the cleaning decisions into a numbered list in the notebook. This is the section that separates a portfolio project from a tutorial.

### Phase 3: Exploratory analysis
- [ ] Volume by complaint type by year, to confirm the chosen types are stable over the window.
- [ ] Distribution of `resolution_hours` per complaint type. Expect heavy right skew, so use median, not mean, and state why.
- [ ] Complaint volume per capita by ZIP (sanity check on reporting-rate differences).
- [ ] Map complaint mix by income quintile. This directly sets up H2.
- [ ] Missingness of `closed_date` by ZIP and by year.

### Phase 4: Core analysis
- [ ] Join income to ZIP; assign income quintiles.
- [ ] **Raw gap:** median resolution time by income quintile, all complaints pooled. Record this number.
- [ ] **Stratified gap:** same, computed *within* each complaint type. Compare to the raw gap to answer H2.
- [ ] Spearman ρ (income vs. median resolution time) per complaint type, with p-values and bootstrap CIs, to answer H1.
- [ ] Logistic regression on non-closure, to answer H3.
- [ ] **Build the multivariate model to answer H4.** Fit in three nested steps and report all three, so the coefficient's movement is visible:
  1. `log(hours) ~ log(income)` alone
  2. `+ complaint_type`
  3. `+ borough + year + reporting_channel`
- [ ] Check model diagnostics: residual plots, VIF for multicollinearity (income and borough will be correlated, say so), and note that ZIP-clustered errors are more appropriate than naive OLS standard errors.
- [ ] Translate the income coefficient into plain English with units: "A 10% increase in median income is associated with a Y% change in resolution time," not a bare coefficient table.
- [ ] Year-over-year: is any gap widening, stable, or closing?
- [ ] Sensitivity check: rerun the headline result using mean instead of median, and with the quarantined rows re-included. If the conclusion flips, say so.

### Phase 5: Tableau build
- [ ] Export aggregated extract from DuckDB (ZIP by complaint_type by year, with median hours, count, non-closure rate, median income).
- [ ] Get NYC ZIP boundary shapefile (NYC Open Data, ZIP Code Tabulation Areas) and confirm it joins cleanly to the ZIP field.
- [ ] **Sheet 1:** Choropleth, median response time by ZIP, complaint-type filter, diverging color scale centered on citywide median.
- [ ] **Sheet 2:** Scatter, ZIP median income (x) vs. median response hours (y), sized by volume, colored by borough, trend line shown.
- [ ] **Sheet 3:** Small multiples, response time by income quintile per year, one panel per complaint type.
- [ ] Assemble into a dashboard with a clear title stating the finding, not "NYC 311 Dashboard" but something like "Heat complaints take X% longer to close in the lowest-income quintile."
- [ ] Publish to Tableau Public; test the link in an incognito window.

### Phase 6: Write-up and delivery
- [ ] README with: the question, the answer in two sentences, methodology summary, key visual, limitations, reproduction instructions.
- [ ] **Limitations section** covering at minimum: closure timestamp isn't the same as actual problem resolution; agencies differ in closing practice; reporting-rate differences mean the data measures *reported* problems, not problems; ZCTA isn't the same as ZIP, it's an approximation; observational, not causal.
- [ ] **Write an "Unexpected Findings" section.** Keep a running note file from Phase 3 onward of anything that's surprising: a complaint type that runs backwards to the trend, a discontinuity at a specific date, a borough that behaves unlike the rest. Three bullets is enough. This is the most quotable part of a portfolio project and it costs nothing if the notes are kept as I go. Don't try to write it retroactively at the end; I'll have forgotten.
- [ ] Clean the notebook top-to-bottom so it runs from a fresh kernel.
- [ ] Push repo; link both repo and Tableau dashboard from the portfolio site.
- [ ] **Prep answers** to: Why median over mean? Why Spearman over Pearson? Why log-transform? Why DuckDB over pandas? What would change the conclusion? These will be asked, and the project is only as good as the ability to defend the decisions in it.

---

## 5. Positioning

**Portfolio headline:** "Do Wealthier NYC Neighborhoods Get Faster City Services?"

**Resume bullet (fill in the bracketed parts only once the numbers exist):**
> Analyzed [N]M+ NYC 311 service requests (2022-2025) using DuckDB, SQL, Python, and Tableau to test whether city response times vary by neighborhood income; built a multivariate regression controlling for complaint type, borough, and year, finding [specific result], and published an interactive dashboard.

Two rules for this bullet:

1. **Count the rows before claiming a number.** Don't state a record count that hasn't been computed. Four years of 311 data is somewhere in the multi-million range, but the exact figure depends on the date filter and how many rows survive cleaning. An interviewer who knows the dataset will ask, and "I'm not sure, I saw that number somewhere" is a bad moment. Run the count, use the real number.
2. **Name the actual finding.** "Identified factors influencing resolution times" says nothing. "Found the apparent income gap was explained by complaint mix" or "found a 22% gap persisting after controls" is what makes someone want to ask about it.

---

## 6. Definition of done

The project is complete when a stranger can, in under five minutes: read the headline finding, see the evidence in one chart, understand what would invalidate it, and click through to reproducible code.

## 7. Risks

| Risk | Mitigation |
|---|---|
| File size overwhelms local machine | Parquet + DuckDB; never load full data into pandas |
| H1 isn't supported | Fine. H2/H3 findings become the story instead. The H4 model produces a publishable conclusion either way. Plan the write-up to accommodate a null result. |
| Multivariate model added late, breaks the timeline | Fit a rough version of the H4 model early (right after Phase 4's first join) even on messy data, just to confirm the approach works. Polish later. |
| ZIP/ZCTA mismatch | Document the approximation; consider community district as a robustness check |
| Tableau Public row limits | Pre-aggregate upstream (already in plan) |
| Scope creep into 20 complaint types | Hard cap at 8; freeze the list before Phase 4 |
