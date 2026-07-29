Here's the method stack, in the order you'll use it, each pinned to your existing literature list and calibrated to bachelor depth. The rule I applied throughout: the *basic* version of each method is correct and defensible — rigor at your level means applying simple methods cleanly and documenting choices, not using fancier ones.

## Tier 1 — the core, non-negotiable methods

**1. Enterprise DCF (FCFF + WACC + Gordon terminal value)** — *Koller et al., Damodaran*
The valuation engine. What you need to command: FCFF definition and why it's pre-financing (EBIT×(1−t) + D&A − Capex − ΔNWC), CAPM cost of equity, WACC as the blend, present-value mechanics, and the Gordon growth terminal value `TV = FCF×(1+g)/(WACC−g)` — including *why* it explodes when g approaches WACC. Koller chapters on the core DCF and terminal value are enough; Damodaran fills in tax rates, betas, and growth-fade logic. Bachelor depth: you do **not** need APV, mid-year conventions, or option-value adjustments for pipelines — say explicitly that the DCF is a deliberately mechanical, uniform anchor applied identically to every firm-quarter, and that its simplicity is a feature (comparability), not a bug.

**2. Residual Income Model (robustness valuation)** — *Lee/Myers/Swaminathan 1999, Heinrichs et al. 2013*
`V = Book equity + Σ PV(ROE_t − r) × B_{t−1}`, i.e., book value plus discounted "abnormal earnings." You need: the clean-surplus relation (book value grows by earnings minus dividends), why RIM only needs EPS forecasts + book value + cost of equity, and why it's less terminal-value-dependent than DCF (book value anchors the level today). LMS 1999 is your template — they do exactly your exercise, with RIM, on the Dow. Bachelor depth: implement the simple three-period version LMS use; skip the Heinrichs extensions except as citations for data-integrity choices.

**3. The valuation-error measure ln(M/V) and the panel design** — *Dong et al. 2006*
This paper is your design template: log misvaluation measure, firm-level panel, fixed effects, standard controls (size, book-to-market, leverage, coverage). Read it for *how they structure and defend the measure*, not their takeover application.

**4. Panel regression with fixed effects** — *Asteriou & Hall, panel chapters; Dong et al. for the application*
The workhorse: `VE_it = α_i + β·Macro_t + γ·Controls_it + ε_it`. What you must genuinely understand: what firm fixed effects absorb (all time-invariant firm differences — including the level biases in your DCF like expensed R&D, which is exactly why FE saves you), and why standard errors need correcting when all firms share the same macro shock. For the correction, use Driscoll-Kraay and cite it as the standard remedy for cross-sectional dependence — one added reference (Hoechle 2007, *Stata Journal*, very readable) covers it. Bachelor depth: you don't need to derive DK; you need to explain *why* naive SEs are wrong (residuals correlated across firms within a quarter) and that DK fixes it.

**5. Stationarity and unit-root testing** — *Asteriou & Hall*
Before any regression: ADF tests on the macro series (transform levels to changes/YoY where non-stationary), and a panel unit-root test (IPS or Fisher-ADF) on VE. The concept to master is **spurious regression** — two trending series correlate meaninglessly — because it dictates your biggest modeling decision: VE in levels vs. changes. Asteriou & Hall covers ADF, spurious regression, and panel unit roots at exactly the right depth. Bachelor-level resolution: if VE is persistent, run the regressions in changes (ΔVE on ΔMacro) as the headline and levels as descriptive — full error-correction models are the "build it out later" option, not required.

**6. PCA for the macro factors** — *gap in your current list*
Standardize inputs, extract components, read the loadings, keep 3–5 by scree/variance-explained, name them economically ("level," "credit/risk," "activity"). This is the one method none of your six references covers properly. Fix: add one citation — either Jolliffe & Cadima (2016, a short open-access review) or the PCA chapter of James et al., *Introduction to Statistical Learning* (free PDF). Bachelor depth: full-sample PCA for a descriptive/co-movement study is fine (your §5.12 already notes the caveat); report the loadings table and check they look stable in two half-samples. Nothing more.

## Tier 2 — the lead-lag layer (keep deliberately simple)

**7. Granger causality + Newey-West SEs** — *Asteriou & Hall*
Run this on the **aggregate quarterly VE index** (cross-firm median), not the panel: with ~84 quarters, a bivariate Granger test with 1–2 lags per macro factor is honest and interpretable. Newey-West handles the autocorrelation. Asteriou & Hall covers both. Understand what Granger causality does and doesn't claim — "X helps predict Y" — and say so; that phrasing itself signals rigor. Skip Dumitrescu-Hurlin panel Granger entirely unless a grader asks.

**8. Rolling-window regressions** — no new theory needed
Re-estimate the aggregate regression on a moving 20-quarter window and plot the coefficient path. Present it as **descriptive** (does the relationship look stable across regimes?), never as tested — with 84 quarters the windows are too short for formal inference, and admitting that is the rigorous move.

## What to consciously leave out (and say so)

Error-correction/cointegration models, local projections, Fama-MacBeth, panel Granger, vintage (ALFRED) macro data, and time-varying-parameter models. One paragraph in the methodology chapter — "these extensions exist, here's why the design doesn't require them" — is worth more at bachelor level than a half-understood implementation. The spec grid from §7.2 (rerunning VE under three discount-rate rules) needs **no new methods at all** — it's the same DCF three times — which is exactly why it's your best rigor-per-effort investment.

## Literature coverage summary

| Method | Covered by |
|---|---|
| DCF, WACC, terminal value | Koller; Damodaran |
| RIM, consensus-based V | LMS 1999; Heinrichs 2013 |
| VE measure, panel design, controls | Dong et al. 2006 |
| Panel FE, ADF/unit roots, Granger, Newey-West | Asteriou & Hall |
| Driscoll-Kraay SEs | **add** Hoechle 2007 |
| PCA | **add** Jolliffe & Cadima 2016 or ISLR ch. 12 |

So the reading list needs exactly two small additions, both free and readable. Suggested learning order: Koller/Damodaran DCF chapters first (that's the supervisor conversation), then LMS 1999 cover to cover (it's your thesis in miniature), then Asteriou & Hall panels + unit roots, then Dong et al. for design details, PCA last — it's a two-day topic.
