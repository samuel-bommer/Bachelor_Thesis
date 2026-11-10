"""
Starting with the inital time series analysis. 

We first run a linear regression with only one variable. 
Then, we check if the time series has a unit root with the 
Augmented Dicky Fuller test. For most of the statistical analysis
we use statsmodels. 
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import duckdb
from pathlib import Path
import statsmodels.api as sm
import pandas as pd
from BP_BG_diagnostics import run_bg_bp_diagnostics


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


with duckdb.connect(DB_PATH) as con:
    df_analysis = con.execute("SELECT * FROM analysis_table").df()


def lin_reg_statsmodels(y: pd.DataFrame, x: pd.DataFrame, cov_type: str = 'HC3', max_lags: int = 4) -> sm.regression.linear_model.RegressionResultsWrapper:
    """
    Uses lin reg implementation for statsmodels
    """
    
    x_const = sm.add_constant(x) # adds an intercept
    lin_reg = sm.OLS(y, x_const)
    if cov_type == 'HC3':
        result = lin_reg.fit(cov_type=cov_type) # cov type for heteroskedasticity-robust standard errors (might change this later)
    else:
        cov_kwds = {'maxlags' : max_lags}
        result = lin_reg.fit(cov_type=cov_type, cov_kwds=cov_kwds)

    print(result.summary())
    return result


if __name__ == '__main__':
    
    # =================== Statsmodels Linear Regression =====================
    
    vix_result = lin_reg_statsmodels(df_analysis['valuation_error_firm'], df_analysis['vix'], 'HAC')
    real_gdp_result = lin_reg_statsmodels(df_analysis['valuation_error_firm'], df_analysis['real_gdp_growth'], 'HAC')
    credit_spread_result = lin_reg_statsmodels(df_analysis['valuation_error_firm'], df_analysis['credit_spread(10Y)'], 'HAC')
    cpi_result = lin_reg_statsmodels(df_analysis['valuation_error_firm'], df_analysis['cpi_yoy'], 'HAC')
    term_spread_result = lin_reg_statsmodels(df_analysis['valuation_error_firm'], df_analysis['term_spread'], 'HAC')
    ind_prod_result = lin_reg_statsmodels(df_analysis['valuation_error_firm'], df_analysis['ind_prod_growth'], 'HAC')
    # We use HAC because autocorrelation and heteroskedasticity are present, it ensures that p-values and confidence intervals are correct

    # ========================== Run Diagnostics ============================

    run_bg_bp_diagnostics(vix_result, 'vix')
    run_bg_bp_diagnostics(real_gdp_result, 'real gdp growth')
    run_bg_bp_diagnostics(credit_spread_result, 'credit spread')
    run_bg_bp_diagnostics(cpi_result, 'cpi yoy')
    run_bg_bp_diagnostics(term_spread_result, 'term spread')
    run_bg_bp_diagnostics(ind_prod_result, 'ind prod growth')
    
    # ================== Multivariate Linear Regression =====================
    
    macro_cols = ['vix', 'real_gdp_growth',
                  'credit_spread(10Y)', 'cpi_yoy',
                  'term_spread', 'ind_prod_growth']
    
    multivariate_result = lin_reg_statsmodels(
        df_analysis['valuation_error_firm'],
        df_analysis[macro_cols],
        'HAC'
    )
    
    # ==================== Multivariate Diagonostics ========================
    
    run_bg_bp_diagnostics(multivariate_result, 'multivariate')
    
    