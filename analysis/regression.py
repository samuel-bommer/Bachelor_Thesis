"""
Starting with the inital time series analysis. 

We first run a linear regression with only one variable. 
Then, we check if the time series has a unit root with the 
Augmented Dicky Fuller test. For most of the statistical analysis
we use statsmodels. 
"""


import numpy as np
import duckdb
from pathlib import Path
import statsmodels.api as sm
import pandas as pd


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


with duckdb.connect(DB_PATH) as con:
    df_ve_full = con.execute("SELECT * FROM valuation_errors").df()
    df_macro_indicators = con.execute("SELECT * FROM macro_indicators").df()
    

def lin_reg_statsmodels(y: pd.DataFrame, x: pd.DataFrame) -> dict:
    """
    Uses lin reg implementation for statsmodels
    """
    
    x_const = sm.add_constant(x) # adds an intercept
    lin_reg = sm.OLS(y, x_const)
    result = lin_reg.fit(cov_type='HC3') # cov type for heteroskedasticity-robust standard errors (might change this later)
    
    print(result.summary())
    
    return result


if __name__ == '__main__':
    df_ve = df_ve_full[['Instrument', 'quarter_date', 'valuation_error_equity', 'valuation_error_firm']].copy()
    df_ve['quarter_date'] = pd.to_datetime(df_ve['quarter_date'])
    df_ve = df_ve.sort_values('quarter_date')
    
    df_ve_quarterly_firm = df_ve.groupby('quarter_date')['valuation_error_firm'].mean().reset_index()
    df_ve_quarterly_equity = df_ve.groupby('quarter_date')['valuation_error_equity'].mean().reset_index()
    df_ve_quarterly = df_ve_quarterly_firm.merge(df_ve_quarterly_equity, on='quarter_date', how='outer')
    # Think about adding this to the db directly, since it will be reused a couple of times
    # Check DCF again, why are all values negative (overstated)
    
    df_macro_indicators['quarter_date'] = pd.to_datetime(df_macro_indicators['quarter_date'])
    
    df_analysis = df_macro_indicators.merge(df_ve_quarterly, on='quarter_date', how='inner')
    df_analysis = df_analysis.replace([np.inf, -np.inf], np.nan).dropna()
    
    # =================== Statsmodels Linear Regression =====================
    
    vix_result = lin_reg_statsmodels(df_analysis['valuation_error_firm'], df_analysis['vix'])
    real_gdp_result = lin_reg_statsmodels(df_analysis['valuation_error_firm'], df_analysis['real_gdp_growth'])
    
    