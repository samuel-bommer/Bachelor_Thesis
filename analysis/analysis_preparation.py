"""
This py file is for applying the insight of the tests to our data.
Specifically, we need to apply differencing to some series.
"""

import pandas as pd
from pathlib import Path
import numpy as np
import duckdb


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


with duckdb.connect(DB_PATH) as con:
    df_ve_full = con.execute("SELECT * FROM valuation_errors").df()
    df_macro_indicators = con.execute("SELECT * FROM macro_indicators").df()
    
# ================= Preparing the df_ve_full for the analysis =======================

df_ve = df_ve_full[['Instrument', 'quarter_date', 'valuation_error_equity', 'valuation_error_firm']].copy()
df_ve['quarter_date'] = pd.to_datetime(df_ve['quarter_date'])
df_ve = df_ve.sort_values('quarter_date')

df_ve_quarterly_firm = df_ve.groupby('quarter_date')['valuation_error_firm'].mean().reset_index()
df_ve_quarterly_equity = df_ve.groupby('quarter_date')['valuation_error_equity'].mean().reset_index()
df_ve_quarterly = df_ve_quarterly_firm.merge(df_ve_quarterly_equity, on='quarter_date', how='outer')

# ==================== Preparing macro indicators ============================
 
df_macro_indicators['quarter_date'] = pd.to_datetime(df_macro_indicators['quarter_date'])
df_macro_indicators['cpi_yoy'] = df_macro_indicators['cpi_yoy'].diff()
df_macro_indicators['term_spread'] = df_macro_indicators['term_spread'].diff()

# =================================== Merge ===================================

df_analysis = df_macro_indicators.merge(df_ve_quarterly, on='quarter_date', how='inner')
df_analysis = df_analysis.replace([np.inf, -np.inf], np.nan)


with duckdb.connect(str(DB_PATH)) as con:
    con.execute('DROP TABLE IF EXISTS analysis_table')
    con.register('df_analysis', df_analysis)
    con.execute('CREATE TABLE analysis_table AS SELECT * FROM df_analysis')
    rows = con.execute('SELECT COUNT(*) FROM analysis_table').fetchone()[0]
    print(f'Saved {rows} rows to analysis_table. Ready for the lead-lag analysis')

