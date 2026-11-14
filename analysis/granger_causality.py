"""
Granger causality test

In this setup with use a grangeer causality test to check
if past values of the explainging variable can better predict the
value of the explained values than its own lags
"""


import duckdb
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import grangercausalitytests
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


with duckdb.connect(DB_PATH) as con:
    df_analysis = con.execute("SELECT * FROM analysis_table").df()


def apply_granger(y: pd.Series, x: pd.DataFrame, maxlag: int = 4) -> dict:
    """
    Apply granger for a few columns
    """
    
    all_granger_results = {}
    for col in x.columns:
        data = pd.concat([y, x[col]], axis=1).dropna()
        all_granger_results[col] = grangercausalitytests(data, maxlag=maxlag)
        
    return all_granger_results


def apply_granger_reverse(y: pd.Series, x: pd.DataFrame, maxlag: int = 4) -> dict:
    """
    Reverse of the above
    """
    
    all_results = {}
    for col in x.columns:
        data = pd.concat([x[col], y], axis=1).dropna()
        all_results[col] = grangercausalitytests(data, maxlag=maxlag)
    return all_results


def print_granger_results(results: dict, reverse: bool = False) -> None:
    for col, res in results.items():
        arrow = f'VE → {col}' if reverse else f'{col} → VE'
        print(f'\n=== Granger: {arrow} ===')
        for lag, lag_res in res.items():
            f_stat = lag_res[0]['ssr_ftest'][0]
            p_val = lag_res[0]['ssr_ftest'][1]
            sig = '***' if p_val < 0.01 else '**' if p_val < 0.05 else '*' if p_val < 0.10 else ''
            print(f'Lag {lag}: F={f_stat:.3f}, p={p_val:.4f} {sig}')


if __name__ == '__main__':
    df_granger = df_analysis.copy().drop(columns=['quarter_date', 'valuation_error_firm', 'valuation_error_equity'])
    df_explained = df_analysis['valuation_error_firm'].copy()
    
    # ============================ Apply Granger =============================
    
    granger_results = apply_granger(df_explained, df_granger)
    print_granger_results(granger_results)
    
    # ======================== Apply Reverse Granger =========================
    
    rev_granger_results = apply_granger_reverse(df_explained, df_granger)
    print_granger_results(rev_granger_results, reverse=True)
    