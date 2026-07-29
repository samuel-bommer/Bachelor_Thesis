# Methodology Reference — Synthetic DCF & Valuation Error Pipeline

Reference file for the bachelor thesis *"Macroeconomic Shifts and Intrinsic Value Deviations
in Pharmaceutical Equities"*. Point Claude (or yourself) here to get up to speed.
Companion to `proposal.tex`.

---

## 1. Core idea

For each firm `i` and quarter-end `t` (2005Q1–2025Q4), build a DCF **using only information
available at `t`** (point-in-time discipline), then compute the valuation error:

```
VE_it = ln( MarketCap_it / IntrinsicValue_it )
```

The log ratio is preferred over `(P−V)/V`: symmetric, dampens outliers, standard in the
literature (Dong et al. 2006 use log misvaluation measures). VE > 0 = market premium over
intrinsic value. This panel of VE_it is the dependent variable regressed on macro factors.

---

## 2. Point-in-time data from LSEG — the critical part

### 2.1 Analyst forecasts (I/B/E/S consensus) — inherently point-in-time

The good news: **I/B/E/S consensus history in LSEG IS point-in-time by construction.**
When you request `TR.EPSMean` with a historical `SDate`, you get the consensus *as it stood
on that date*, not a restated figure. This is exactly what Lee/Myers/Swaminathan (1999) rely on.

Using the `lseg-data` Python library (`ld.get_data` / legacy `refinitiv-data`):

```python
ld.get_data(
    universe=["PFE.N", "MRK.N", ...],
    fields=[
        "TR.EPSMean(Period=FY1)", "TR.EPSMean(Period=FY2)", "TR.EPSMean(Period=FY3)",
        "TR.RevenueMean(Period=FY1)", "TR.RevenueMean(Period=FY2)",
        "TR.EBITMean(Period=FY1)", "TR.EBITMean(Period=FY2)",
        "TR.LTGMean",                       # long-term growth consensus
        "TR.NumberOfAnalysts(Period=FY1)",
        "TR.EPSMean(Period=FY1).date",      # always pull the date alongside
    ],
    parameters={"SDate": "2005-03-31", "EDate": "2025-12-31", "Frq": "FQ"},
)
```

Key points:
- `Frq=FQ` samples the consensus at each fiscal-quarter date; alternatively `Frq=CQ` or
  pull monthly (`FM`) and snap to calendar quarter-ends yourself (cleaner — see §5.4 on
  fiscal-year misalignment).
- `Period=FY1/FY2/FY3` are *forward* fiscal years **relative to the SDate row** — this is
  what makes it point-in-time.
- Pull `.date` for every field to verify alignment; never trust row order.
- Also pull `TR.EPSMeanEstDate` / estimate activity where available to detect **stale
  consensus** (no revision for >90 days → flag).

### 2.2 Fundamentals (historical, for the FCF bridge) — NOT automatically point-in-time

Standard `TR.` fundamentals (e.g., `TR.Revenue`, `TR.CapitalExpenditures`) return
**restated** figures. Two mitigations, use both:

1. **Reporting-lag rule:** at quarter-end `t`, only use fundamentals for fiscal periods whose
   report date precedes `t`. Pull `TR.OriginalAnnouncementDate` for each period and align on
   it. Simple fallback: lag all fundamentals by one quarter (the 10-Q/10-K filing lag is
   ~40–90 days).
2. Where restatement matters most (revenue, earnings), the I/B/E/S **actuals**
   (`TR.EPSActValue`, `TR.RevenueActValue`) are as-originally-reported and can serve as a
   point-in-time cross-check.

This is the Heinrichs et al. (2013) "data integrity" concern — document the choice in the
methodology chapter.

### 2.3 Market data

- `TR.CompanyMarketCap` at quarter-end (handles shares outstanding, splits, buybacks).
- `TR.PriceClose`, `TR.SharesOutstanding` as backup/sanity check.
- Sample market cap a few days *after* quarter-end if you want prices to reflect the same
  information set as the consensus snapshot — but quarter-end close is the standard choice.

### 2.4 Universe construction & survivorship bias

**Do not** build the universe from today's index constituents. Two options:

- **Preferred — sector screen incl. dead firms:** LSEG Screener with
  `IN(Equity(active, inactive))` filtered on TRBC industry *Pharmaceuticals* (TRBC code
  `5520201010`, optionally + Biotech `5520101010` — decide and document) and country = US.
  Dead/delisted instruments keep retrievable history under their dead RIC (e.g., `WYE.N^...`).
- Alternative: point-in-time index constituents via `TR.IndexConstituentRIC` with historical
  `SDate` (S&P 500 Pharma index), joined over time.

Record for every firm: RIC (incl. dead RIC), delisting date and reason
(`TR.InstrumentDelistedDate`), so exits stay in the panel until exit (no survivorship bias)
and M&A exits can be flagged.

### 2.5 API practicalities

- Chunk requests: ~10–20 RICs × a few fields per call; LSEG throttles large requests and
  silently truncates some responses. **Verify row counts.**
- Cache every raw response immediately (parquet, one file per chunk) before any processing —
  the API is the slow/fragile part; never re-pull what you already have.
- Layered storage: `raw/` (untouched API output) → `clean/` (aligned panel) → `analysis/`
  (VE + macro). DuckDB over the parquet files works well at this size (~10k firm-quarters).

---

## 3. DCF construction at each (i, t)

Per Koller et al. (2020) / Damodaran (2012), enterprise-DCF with consensus inputs:

### 3.1 Explicit forecast years 1–3
From consensus: Revenue (FY1, FY2), EBIT (FY1, FY2), EPS (FY1–FY3). Where EBIT consensus is
missing, derive from EPS via historical interest/tax bridge or apply the firm's trailing
EBIT margin to revenue consensus.

### 3.2 FCFF bridge (consensus gives earnings, not cash flow)
```
FCFF = EBIT × (1 − tax rate)            ← effective tax rate, trailing 3y median, floored/capped [10%, 35%]
     + D&A                              ← trailing % of revenue, applied to forecast revenue
     − Capex                            ← trailing % of revenue
     − ΔNWC                             ← trailing ΔNWC/Δrevenue ratio × forecast revenue growth
```
Use 3-year trailing medians for the ratios (robust to one-off years; pharma M&A distorts
single years badly).

### 3.3 Fade years 4–10
Grow FCFF by fading growth linearly from the consensus LTG (`TR.LTGMean`, capped at e.g. 20%)
toward the terminal growth rate. If LTG is missing (common for smaller firms): fade from
implied FY2→FY3 EPS growth, or sector-median LTG at `t`.

### 3.4 Terminal value
Gordon growth: `TV = FCFF_10 × (1+g) / (WACC − g)` with `g` = long-run nominal GDP proxy
(~2–3%, fixed; or 10Y breakeven inflation + 1%). **Hard constraint: g ≤ WACC − 1.5pp**, else
floor the spread — TV explosion is the #1 numerical failure mode.

### 3.5 Discount rate (point-in-time WACC)
- Cost of equity: CAPM. `rf` = 10Y Treasury at `t` (FRED DGS10); ERP = fixed 5% **or**
  Damodaran's monthly implied ERP series (document the choice — it matters, since a
  time-varying ERP already absorbs macro variation you want to study! A *constant* ERP is
  arguably cleaner for this research design — the macro co-movement then shows up in VE
  rather than being baked into V).
- Beta: 5-year rolling monthly regression vs. S&P 500, winsorized to [0.4, 2.0]; or a single
  sector beta (more stable, less firm-specific noise — recommended baseline, firm beta as
  robustness).
- Cost of debt: `rf` + spread by leverage/coverage bucket (or Baa spread for all — simple,
  defensible).
- Weights: market cap vs. book debt at `t`. **Caveat — mild circularity:** market-cap weights
  make V depend on M (when M falls, the equity weight falls, WACC drifts toward the cheaper
  cost of debt, V rises → mechanical VE co-movement). Pharma leverage is low (~10–20%) so the
  effect is second-order, but the cleaner baseline is a *fixed sector-target capital structure*
  (e.g., long-run sector-median D/(D+E)), with firm-specific market weights as robustness.
  Same logic favors the *sector-constant beta* baseline already noted above: rolling firm betas
  spike in crises, injecting macro variation into V through the beta channel.

### 3.6 Equity value
```
EV = Σ PV(FCFF_1..10) + PV(TV)
Equity value V_it = EV − NetDebt_it      (NetDebt = total debt − cash, point-in-time per §2.2)
VE_it = ln(MarketCap_it / V_it)
```

### 3.7 Robustness alternative: Residual Income Model
LMS (1999) actually use RIM, not DCF — it needs only EPS forecasts + book value + cost of
equity (no FCF bridge, no capital-structure assumptions). **Strongly recommended as the
robustness valuation**: if VE from DCF and VE from RIM co-move with macro the same way, the
result doesn't hinge on the FCF bridge assumptions.

---

## 4. Variable list

### 4.1 Firm-level (LSEG)
| Variable | Field | Use |
|---|---|---|
| Market cap | `TR.CompanyMarketCap` | VE numerator |
| EPS consensus FY1–FY3 | `TR.EPSMean(Period=FYn)` | forecasts |
| Revenue consensus FY1–FY2 | `TR.RevenueMean(Period=FYn)` | forecasts |
| EBIT consensus FY1–FY2 | `TR.EBITMean(Period=FYn)` | forecasts |
| Long-term growth | `TR.LTGMean` | fade anchor |
| # analysts | `TR.NumberOfAnalysts` | coverage filter, control |
| Revenue, EBIT, net income | `TR.Revenue`, `TR.EBIT`, ... | margins, bridge |
| D&A, Capex, ΔNWC | `TR.DepreciationAmort`, `TR.CapitalExpenditures`, WC items | FCF bridge |
| Total debt, cash | `TR.TotalDebtOutstanding`, `TR.CashAndSTInvestments` | net debt, WACC weights |
| Interest expense, tax | `TR.InterestExpense`, `TR.IncomeTaxRate` | cost of debt, tax rate |
| Book equity | `TR.TotalEquity` | RIM, controls |
| Report dates | `TR.OriginalAnnouncementDate` | point-in-time alignment |
| Delisting date/reason | `TR.InstrumentDelistedDate` | exit handling |
| TRBC code, country | `TR.TRBCIndustryGroupCode`, `TR.HQCountryCode` | universe |
| Monthly total returns | `TR.TotalReturn` | beta estimation, momentum control |
| R&D expense | `TR.ResearchAndDevelopment` | R&D intensity (pipeline/duration proxy) |
| Dividends paid | `TR.DividendsPaid` or `TR.DividendYield` | payout (short-duration proxy) |

Controls for the panel regression (standard in Dong et al. 2006): size (ln market cap),
leverage, book-to-market, analyst coverage, firm age. Add: **momentum** (trailing 12m return —
price-vs-anchor gaps mechanically follow returns while consensus lags), **R&D/revenue**, and
**TV share of V** (fraction of V from the terminal value, computed from your own DCF — a
direct cash-flow-duration proxy). The last two matter most as *interaction* variables, see §7.3.

### 4.2 Macro candidates (FRED tickers) — input to PCA, select 3–5
| Dimension | Series | FRED ID |
|---|---|---|
| Rates level | 10Y Treasury | `DGS10` |
| Rates level | Fed funds | `FEDFUNDS` |
| Real rates | 10Y TIPS yield | `DFII10` (starts 2003 ✓) |
| Yield curve | 10Y–2Y slope | `T10Y2Y` |
| Yield curve | 10Y–3M slope | `T10Y3M` |
| Credit | Baa – 10Y spread | `BAA10Y` |
| Credit | HY OAS | `BAMLH0A0HYM2` |
| Risk appetite | VIX (quarterly avg, not point) | `VIXCLS` |
| Inflation | 10Y breakeven | `T10YIE` |
| Inflation | CPI YoY | `CPIAUCSL` (transform) |
| Activity | Industrial production YoY | `INDPRO` (transform) |
| Activity | Unemployment | `UNRATE` |
| Financial conditions | Chicago Fed NFCI | `NFCI` |
| Policy uncertainty | EPU index | `USEPUINDXD` |
| Policy uncertainty | **Healthcare-category EPU** | policyuncertainty.com (not on FRED) |
| Rates (ZLB fix) | Wu-Xia shadow fed funds rate | Atlanta Fed (not on FRED) |
| Inflation exp. | 5y5y forward inflation | `T5YIFR` |
| USD | Broad dollar index | `DTWEXBGS` (starts 2006 — gap!) |

Notes: TED spread (`TEDRATE`) **discontinued Jan 2022** — avoid or splice. `FEDFUNDS` is flat
at zero 2009–2015 and 2020–2022 (~40% of the sample) — near-zero variance in the ZLB years
distorts PCA loadings; use the Wu-Xia shadow rate instead of (or spliced with) `FEDFUNDS`.
The **healthcare EPU sub-index** (Baker-Bloom-Davis categorical series) is the one genuinely
sector-specific candidate — ACA 2010, the 2015–16 drug-pricing debate, IRA 2022 are pharma
shocks invisible to broad macro series; strong differentiator for this thesis. Take quarterly
averages of daily series (less noisy than quarter-end point values). Transform levels to
changes/YoY where non-stationary *before* PCA; standardize all inputs.

A practical note that helps the design: nearly all preferred candidates (rates, slopes,
spreads, VIX, breakevens) are **financial-market series — observed in real time, never
revised**. Lean the final 3–5 factors toward these; it dissolves the release-lag/vintage
problem (§5.10) for the core specification, leaving ALFRED only for CPI/INDPRO-type inputs.

---

## 5. Edge cases & known failure modes

1. **Negative EPS/FCF forecasts — the big one for pharma.** Small pharma/biotech firms often
   have negative consensus EPS for all forecast years → DCF yields negative or meaningless V,
   and ln(M/V) is undefined. Decide the rule up front:
   - Restrict universe to firms with positive FY2 consensus EPS in ≥ X% of quarters
     (pushes sample toward large/mid-cap pharma — fine, and worth stating as a scope choice), and/or
   - Drop firm-quarters with non-positive V (document attrition), never floor/fudge V.
   This interacts with the Pharma-vs-Biotech TRBC choice in §2.4 — pure biotech is mostly
   pre-revenue and will be largely unusable; the 80–120 firm target realistically means
   *Pharmaceuticals* TRBC + profitable large biotechs.
2. **Insufficient coverage.** Require ≥ 3 analysts on FY1 EPS for inclusion in a given
   quarter. FY3/LTG missing is normal → fallback rules in §3.3, but FY1+FY2 missing → drop
   the firm-quarter.
3. **Terminal value blow-up.** WACC close to g → V explodes. Enforce the spread floor (§3.4)
   and winsorize VE at 1%/99% — but **winsorize cross-sectionally (within each quarter), not
   pooled across the panel**: pooled winsorization truncates exactly the crisis quarters that
   are the signal (in 2008Q4 *every* firm's VE may sit beyond the pooled 1% tail). Per-quarter
   winsorization kills firm-level outliers while preserving the aggregate time-series swing.
4. **Fiscal year misalignment.** FY1 means different calendar horizons for different firms
   (most pharma is Dec FYE, but not all). Either restrict to Dec-FYE firms or interpolate
   FY1/FY2 to a constant 12-month-forward horizon (LMS do a weighting). At minimum, control
   for days-to-fiscal-year-end.
5. **M&A and spinoffs.** Acquisition announcements move the target's price far from any DCF
   value (this is *information*, not error — Dong et al. 2006 is literally about this).
   Flag firm-quarters between deal announcement and delisting; run robustness excluding them.
   Spinoffs (e.g., AbbVie 2013, Organon 2021, Viatris 2020) create short histories and
   ratio breaks — trailing ratios in §3.2 need a minimum-history rule (≥ 8 quarters, else
   sector medians).
6. **Dead RICs and identifier changes.** Tickers get reused; RICs change on exchange moves.
   Build the panel keyed on PermID (`TR.OrganizationID`) or ISIN, not RIC. Resolve once,
   store the mapping.
7. **Stale consensus.** Thinly covered firms can carry an unrevised estimate for quarters.
   Flag if newest revision underlying the mean is > 90 days old; robustness excluding flagged.
8. **Currency (if European firms added).** Use local rf for cost of equity, value in local
   currency, compare to local-currency market cap — VE is a ratio so no FX conversion needed
   for VE itself, but *do not* mix a USD rf with EUR cash flows. (Simplest scope decision:
   US-only first; Europe only if time permits.)
9. **Crisis quarters (2008–09, 2020).** Extreme VE values here are the *signal*, not noise —
   winsorize but never drop these periods. Expect heteroskedasticity; use Driscoll-Kraay or
   clustered standard errors.
10. **Macro release lags / look-ahead in macro data.** CPI, INDPRO etc. for quarter `t` are
    published weeks later, and FRED stores revised values. For a co-movement/lead-lag study
    this is partially acceptable, but for any "predictive" claim use lagged macro
    (`t−1` explains VE at `t`) — which the lead-lag design does anyway. Mention ALFRED
    (vintage FRED data) as the fix if a referee-grade answer is needed.
11. **Stationarity.** VE is likely persistent (near unit-root within firm). Test (panel unit
    root: IPS/Fisher); if persistent, model ΔVE or use error-correction form rather than
    levels-on-levels. This drives the "final model selection" caveat in the proposal.
12. **PCA leakage.** Fit PCA on the full sample only for the descriptive analysis; for
    anything framed as predictive, fit PCA on expanding windows.

---

## 6. Pipeline order of operations

1. Universe: TRBC screen incl. inactive, US pharma, 2005–2025 → RIC/PermID list + delisting dates.
2. Pull & cache raw: I/B/E/S consensus (quarterly snapshots), fundamentals + report dates,
   market data, monthly returns.
3. Clean panel: align everything to calendar quarter-ends with point-in-time rules (§2).
4. Coverage filters (§5.1–5.2) → final estimation sample; report the attrition table.
5. Per (i,t): WACC → DCF → V_it → VE_it. Also RIM-based VE for robustness.
6. Macro: pull FRED, transform, standardize, PCA → 3–5 factors.
7. Panel regressions (firm FE, Driscoll-Kraay SE), lead-lag specs, Granger, rolling windows.

**Sanity checks before trusting VE:** median VE should be near 0 in calm periods (or stable
at a small premium); VE should spike in 2008–09 and Mar 2020; cross-check a couple of
firm-quarters by hand against a manual DCF (put one worked example in the thesis appendix —
supervisors love it). Also report the **distribution of the TV share of V** (expect 60–80%;
"how much of your value is terminal?" is a guaranteed supervisor question), and as an external
validity check, sort firms into V/P quintiles each quarter and tabulate forward 12-month
returns — if VE means anything, low-VE (cheap) firms should outperform, à la LMS (1999).

---

## 7. Identification & interpretation — stress-test layer

The methodology above builds VE correctly; this section is about what a coefficient on a
macro factor *means* and how to defend it. This is where a valuation-savvy supervisor will
push hardest.

### 7.1 What VE actually measures — the three-channel decomposition

V_it is anchored on (a) analyst consensus cash-flow expectations and (b) a mechanical
discount-rate rule. So VE = ln(M) − ln(V) can co-move with macro through three channels:

1. **Discount-rate channel (mechanical):** rf_t enters WACC directly. A DCF with a 10y fade
   + Gordon TV has an effective duration of 20+ years — when rf falls from 5% (2007) to 0.6%
   (2020), V multiplies *by construction*. Any VE–rates co-movement partly reflects the gap
   between the model's duration and the market's effective discounting, not mispricing.
2. **Expectations channel (sluggish analysts):** consensus revises with a lag of weeks to
   quarters, while prices reprice in minutes. In a shock quarter M moves and V stands still →
   VE swings, then mean-reverts as analysts catch up. This predicts the *lead-lag* structure:
   VE reacts contemporaneously with financial-market variables and its reversal follows
   consensus revisions (cf. sticky-expectations / analyst underreaction literature —
   Bouchaud et al. 2019, Coibion & Gorodnichenko 2015).
3. **Mispricing / risk-premium channel:** the residual — time-varying required returns or
   genuine sentiment (the Dong et al. 2006 reading).

**Never claim channel 3 alone.** Frame the thesis as: "the wedge between market prices and a
disciplined, fixed-assumption fundamental anchor co-moves with macro conditions" — and use
§7.2 to separate channel 1 from 2+3 empirically. This framing is honest *and* stronger.

### 7.2 The discount-rate specification grid (key robustness design)

Re-run the whole VE panel under three discount-rate regimes; everything else identical:

| Spec | rf | ERP | What VE captures |
|---|---|---|---|
| A (baseline) | 10Y at `t` | fixed 5% | cash-flow news + duration mismatch |
| B | **fixed** (sample-mean 10Y) | fixed 5% | pure cash-flow-expectations wedge — rates enter VE only through M and consensus |
| C | 10Y at `t` | Damodaran implied ERP_t | wedge net of market-implied risk premium |

The *differences* in macro coefficients across A/B/C are themselves the finding: if the rates
coefficient is large in A and near zero in B, the co-movement is the mechanical
discount-rate channel; if it survives in B, the market is repricing pharma cash flows in ways
consensus doesn't capture. This turns the biggest weakness ("your V is mechanically
rate-sensitive") into the core identification device. Implement via a valuation config file
(§8) so the grid is a loop, not new code.

### 7.3 The common-regressor problem — and where the panel earns its keep

Macro factors do not vary across firms. For the macro coefficient itself, the panel's 6–10k
firm-quarters provide **no** extra identification: the effective sample is ~84 quarterly
observations of the cross-sectional mean of VE, and Driscoll-Kraay SEs implicitly acknowledge
this. Two consequences:

- Report an **aggregate specification** honestly: build a quarterly VE index (equal-weighted
  median across firms; value-weighted as alternative) and run time-series regressions /
  Granger on it with Newey-West SEs. This is the cleanest home for the lead-lag analysis
  (panel Granger alternative: Dumitrescu-Hurlin, but 84 obs of a common factor argues for the
  aggregate version).
- The panel's real power is **cross-sectional heterogeneity in macro sensitivity**:
  interactions macro_t × firm characteristic — TV share of V (duration proxy), R&D/revenue,
  size, payout. Hypothesis: long-duration, high-R&D, low-payout firms' VE responds more to
  rate and risk-appetite shocks. Firm FE + these interactions is a well-identified design
  (the level effect of macro is absorbed; the *differential* effect is estimated from
  thousands of firm-quarters) and the economically most interesting result for a
  practitioner audience.

### 7.4 Ex-ante hypothesis sign table

Commit to signs before running anything (guards against data-mining and is exactly what a
practitioner supervisor will ask for). Under spec A:

| Shock | Expected VE response | Channel |
|---|---|---|
| Credit spreads ↑ / VIX ↑ | VE ↓ (prices fall fast, consensus anchor sticky) | expectations |
| 10Y ↓ | VE ↓ (V rises mechanically more than M) | discount-rate |
| 10Y ↓ under spec B | ambiguous — rate cuts proxy bad news → M falls, V sticky → VE ↓ | expectations |
| Healthcare EPU ↑ | VE ↓, stronger for high-R&D firms | sector policy discount |
| Curve steepening (recovery) | VE ↑ with a lag, as M recovers before consensus | expectations |

Lead-lag prediction from the sluggish-consensus mechanism: financial-market shocks →
contemporaneous VE move → consensus revisions over the next 1–3 quarters → VE mean-reversion.
"VE leads consensus revisions" is testable directly (revision data is in the I/B/E/S pull)
and is a sharper claim than generic Granger causality.

### 7.5 Ready answers for predictable supervisor questions

- *"Why not just use multiples (EV/EBITDA) as the anchor?"* Multiples are priced off the same
  market — the anchor must be independent of M or VE is circular. DCF/RIM on consensus is the
  standard independent anchor (LMS 1999; Dong et al. 2006).
- *"What share of V is terminal value?"* Report the number (§6 sanity checks). Answer: high TV
  share is inherent to enterprise DCF; RIM robustness (§3.7) has far lower "terminal" weight
  because book value anchors the level — if results agree, TV dominance is defused.
- *"Isn't a significant rates coefficient just your model's duration being wrong?"* Yes,
  partially — that's spec grid §7.2, channel separation is the design.
- *"84 quarters, 3–5 factors, plus lags — degrees of freedom?"* Aggregate regressions stay
  parsimonious (≤ 3 regressors + 1–2 lags); richness lives in the panel interactions where
  N is real. Rolling-window results are presented as descriptive, not tested.
- *"Monthly instead of quarterly?"* I/B/E/S consensus and market cap support monthly
  snapshots; fundamentals don't change intra-quarter but don't need to. If time-series power
  becomes binding, monthly VE (~252 obs) is a feasible extension — note it as an option,
  don't commit.

---

## 8. Code architecture (for February 2027)

- `src/` modules: `universe.py`, `pull_ibes.py`, `pull_fundamentals.py`, `pull_macro.py`,
  `panel.py` (point-in-time alignment), `dcf.py`, `rim.py`, `regressions.py`.
- **All valuation assumptions in one `config/valuation.yaml`** (ERP, g, caps/floors, fade
  length, beta rule, weight rule). The §7.2 spec grid and every robustness table is then a
  loop over configs — never a code fork.
- Raw API responses cached to parquet before any processing (§2.5); DuckDB views over
  `raw/` → `clean/` → `analysis/`.
- One golden unit test: a fully hand-computed DCF for one firm-quarter (e.g., PFE 2015Q4)
  asserted against `dcf.py` output; doubles as the thesis-appendix worked example.
- `linearmodels` (PanelOLS, Driscoll-Kraay via kernel covariance), `statsmodels`
  (Newey-West, Granger, unit-root tests), `scikit-learn` (PCA).
