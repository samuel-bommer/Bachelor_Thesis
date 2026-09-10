"""
Smoothen out CapEx and D&A
"""

import numpy as np
import pandas as pd
from pathlib import Path
import duckdb


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'

    
with duckdb.connect(str(DB_PATH)) as con:
    df_prc = con.execute("""
                              SELECT 
                                    Instrument,
                                    quarter_date,
                                    revenue_hist,
                                    capex,
                                    da_cfs, da_act, da_is,
                                    current_assets,
                                    current_liabilities,
                                    cash,
                                    ebit_hist,
                                    rd_expense,
                                    rd_amortisation
                                FROM 
                                    panel_clean
                              """).df()
    
df_prc.sort_values(['Instrument', 'quarter_date'], inplace=True)


def smooth_mean(series: pd.Series) -> float:
    """
    Smoothing
    """
    
    mean_series = series.rolling(12, min_periods=4).mean()
    return mean_series


def annual_lag(series: pd.Series) -> float:
    """
    Annual shift
    """
    
    return series.shift(4)

# =========================== Trailling Ratios ============================

df_prc['nwc'] = df_prc['current_assets'] - df_prc['current_liabilities']
df_prc['adj_ebit'] = df_prc['ebit_hist'] + df_prc['rd_expense'].fillna(0) - df_prc['rd_amortisation'].fillna(0)

df_prc['capex_rev'] = df_prc['capex'] / df_prc['revenue_hist']
df_prc['da_rev'] = df_prc['da_cfs'] / df_prc['revenue_hist']
df_prc['adj_ebit_margin'] = df_prc['adj_ebit'] / df_prc['revenue_hist']

df_prc['smooth_capex_ratio'] = df_prc.groupby('Instrument', sort=False)['capex_rev'].transform(smooth_mean)

df_prc['smooth_da_ratio'] = df_prc.groupby('Instrument', sort=False)['da_rev'].transform(smooth_mean)

# Will most likely be changed later, quarters are populated with fully year numbers
df_prc['nwc_lag4'] = df_prc.groupby('Instrument', sort=False)['nwc'].transform(annual_lag)
df_prc['delta_nwc_rev'] = (df_prc['nwc'] - df_prc['nwc_lag4']) / df_prc['revenue_hist']

df_prc['net_reinvestment_ratio'] = (
    df_prc['smooth_capex_ratio']
    - df_prc['smooth_da_ratio']
    + df_prc['delta_nwc_rev']
)

# =========================== Save to DB =================================

with duckdb.connect(DB_PATH) as con:
    con.execute('DROP TABLE IF EXISTS preprocessing')
    con.register('df_prc', df_prc)
    con.execute(
        """
        CREATE TABLE preprocessing AS
        SELECT
            Instrument,
            quarter_date,
            adj_ebit,
            adj_ebit_margin,
            smooth_capex_ratio,
            smooth_da_ratio,
            delta_nwc_rev,
            net_reinvestment_ratio
        FROM df_prc
        """)