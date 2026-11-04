"""
Test the assumptions of the regression.

----
We specifically need to see if the residual has homoskedastic 
properties (as per assumption) or it violates the assumption,
ergo heteroskedastic, we use a Breusch-Pagan-Test. 

For the Breusch-Pagan-Test we need the fitted OLS residual.

----
It needs to be cecked if a given series exhibits
autocorrelation. 
"""


from statsmodels.stats.diagnostic import het_breuschpagan, acorr_breusch_godfrey

    
def run_bg_bp_diagnostics(result, label: str) -> None:
    """
    Runs the Breusch-Pagan-Test to check for heteroskedasticity
    and runs the Breusch-Godfrey-Test to check for autocorrelation
    """
    
    bg_stat, bg_pval, _, _ = acorr_breusch_godfrey(result, nlags=4)
    bp_stat, bp_pval, _, _ = het_breuschpagan(result.resid, result.model.exog)

    print(f'=== Diagnostics: {label} ===')
    print(f'Breusch-Godfrey (serial correlation): stat={bg_stat:.4f}, p={bg_pval:.4f} → {"FAIL: autocorrelation present, use HAC" if bg_pval < 0.05 else "PASS: no serial correlation"}')
    print(f'Breusch-Pagan   (heteroskedasticity): stat={bp_stat:.4f}, p={bp_pval:.4f} → {"FAIL: heteroskedasticity present, use robust SE" if bp_pval < 0.05 else "PASS: homoskedastic"}\n')
    
    
