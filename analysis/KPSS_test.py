"""
Do another test for stationarity.
"""

import warnings
warnings.filterwarnings("ignore")

import duckdb
from pathlib import Path
from statsmodels.tsa.stattools import kpss
import pandas as pd


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


with duckdb.connect(DB_PATH) as con:
    df_ve_full = con.execute("SELECT * FROM valuation_errors").df()
    df_macro_indicators = con.execute("SELECT * FROM macro_indicators").df()
    

def run_kpss(x: pd.Series, label: str) -> None:
    """
    Run adf-test with statsmodels
    """
    
    kpss_stat, p_value, n_lags, critical_values = kpss(x)
    
    print(f'=== KPSS-test {label} ===')
    print(f'KPSS statistic: {kpss_stat:.4f}')
    print(f'p-value: {p_value:.4f}')
    print(f'Lags used: {n_lags}')
    print(f'Critical values:')
    
    for level, val in critical_values.items():
        print(f' {level}: {val:.4f}')
    print(f'=> {"non-stationary" if p_value < 0.05 else "stationary"}\n')

if __name__ == '__main__':
    df_ve = df_ve_full[['Instrument', 'quarter_date', 'valuation_error_equity', 'valuation_error_firm']].copy()
    df_ve['quarter_date'] = pd.to_datetime(df_ve['quarter_date'])
    df_ve = df_ve.sort_values('quarter_date')
    
    df_ve_quarterly_firm = df_ve.groupby('quarter_date')['valuation_error_firm'].mean().reset_index()
    df_ve_quarterly_equity = df_ve.groupby('quarter_date')['valuation_error_equity'].mean().reset_index()
    
    run_kpss(df_ve_quarterly_firm['valuation_error_firm'], 'VE firm')
    run_kpss(df_ve_quarterly_equity['valuation_error_equity'], 'VE equity')
    run_kpss(df_macro_indicators['vix'], 'vix')