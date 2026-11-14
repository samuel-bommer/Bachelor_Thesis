"""
Vector Autoregression Analysis

"""


import duckdb
import pandas as pd
from pathlib import Path
from statsmodels.tsa.api import VAR


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


with duckdb.connect(DB_PATH) as con:
    df_analysis = con.execute("SELECT * FROM analysis_table").df()
    
    
if __name__ == '__main__':
    var_cols = ['valuation_error_firm', 'real_gdp_growth', 'cpi_yoy', 'ind_prod_growth'] # We use these columns based on the granger results
    df_var = df_analysis[var_cols].copy()
    df_var.index = pd.DatetimeIndex(df_analysis['quarter_date'])
    
    # ============================== VAR model ==============================
    
    model_var = VAR(df_var)
    lag_order = model_var.select_order(maxlags=8)
    print(lag_order.summary())
    
    optimal_lag_aic = lag_order.aic
    result_var_aic = model_var.fit(optimal_lag_aic)
    print(result_var_aic.summary())
    
    optimal_lag_bic = lag_order.bic
    result_var_bic = model_var.fit(optimal_lag_bic)
    print(result_var_bic.summary())
    
    optimal_lag_hqic = lag_order.hqic
    result_var_hqic = model_var.fit(optimal_lag_hqic)
    print(result_var_hqic.summary())
    