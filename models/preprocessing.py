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
            receivables,
            inventories,
            accounts_payable,
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
    Smoothing: possibly adjust the min_periods, since values at the beginning
    are currently being considered more. But on the other hand we would
    lose data
    """
    
    mean_series = series.rolling(12, min_periods=2).mean()
    return mean_series


def annual_lag(series: pd.Series) -> float:
    """
    Annual shift
    """
    
    return series.shift(4)

# =========================== Trailling Ratios ============================

nwc = df_prc['receivables'] + df_prc['inventories'] - df_prc['accounts_payable']
nwc_fallback = df_prc['current_assets'] - df_prc['current_liabilities']
df_prc['nwc'] = nwc.fillna(nwc_fallback)

df_prc['adj_ebit'] = df_prc['ebit_hist'] + df_prc['rd_expense'].fillna(0) - df_prc['rd_amortisation'].fillna(0)
df_prc['capex_adj'] = df_prc['capex'].abs() + df_prc['rd_expense'].fillna(0) # important that capex is absolute
df_prc['da_best'] = df_prc['da_cfs'].fillna(df_prc['da_act']).fillna(df_prc['da_is'])
df_prc['da_adj'] = df_prc['da_best'] + df_prc['rd_amortisation'].fillna(0)

df_prc['capex_rev'] = df_prc['capex_adj'] / df_prc['revenue_hist']
df_prc['da_rev'] = df_prc['da_adj'] / df_prc['revenue_hist']
df_prc['adj_ebit_margin'] = df_prc['adj_ebit'] / df_prc['revenue_hist']

df_prc['smooth_capex_ratio'] = df_prc.groupby('Instrument', sort=False)['capex_rev'].transform(smooth_mean)
df_prc['smooth_da_ratio'] = df_prc.groupby('Instrument', sort=False)['da_rev'].transform(smooth_mean)

df_prc['rd_rev'] = df_prc['rd_expense'].fillna(0) / df_prc['revenue_hist']
df_prc['rd_amort_rev'] = df_prc['rd_amortisation'].fillna(0) / df_prc['revenue_hist']

df_prc['smooth_rd_ratio'] = df_prc.groupby('Instrument', sort=False)['rd_rev'].transform(smooth_mean)
df_prc['smooth_rd_amort_ratio'] = df_prc.groupby('Instrument', sort=False)['rd_amort_rev'].transform(smooth_mean)

# Will most likely be changed later, quarters are populated with fully year numbers
df_prc['nwc_lag4'] = df_prc.groupby('Instrument', sort=False)['nwc'].transform(annual_lag)
df_prc['delta_nwc_rev'] = (df_prc['nwc'] - df_prc['nwc_lag4']) / df_prc['revenue_hist']

# Think about this; since some firms get lost because of one time big nwc chagnes; however we get less firms with this in DCF
df_prc['smooth_delta_nwc_ratio'] = df_prc.groupby('Instrument', sort=False)['delta_nwc_rev'].transform(smooth_mean)

df_prc['net_reinvestment_ratio'] = (
    df_prc['smooth_capex_ratio']
    - df_prc['smooth_da_ratio']
    + df_prc['smooth_delta_nwc_ratio']
)

df_prc['adj_ebit_margin'] = df_prc['adj_ebit_margin'].replace([np.inf, -np.inf], np.nan)
df_prc['adj_ebit_margin'] = df_prc['adj_ebit_margin'].clip(-0.5, 0.6) # apply limits on margins to reduce outliers

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
            smooth_rd_ratio,
            smooth_rd_amort_ratio,
            delta_nwc_rev,
            smooth_delta_nwc_ratio,
            net_reinvestment_ratio
        FROM df_prc
        """)
    rows = con.execute('SELECT COUNT(*) FROM preprocessing').fetchone()[0]
    print(f'Saved {rows} rows to preprocessing. Ready for the DCF')