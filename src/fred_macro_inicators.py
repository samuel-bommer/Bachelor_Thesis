"""
Getting the Macroeconomic variables
for the analysis from FRED.

Specifically we are interested in the following
variables:
- VIX
- Real GDP Growth
- Credit Spread (Baa-10Y)
- CPI YoY
"""

import duckdb 
from pathlib import Path
import pandas_datareader as web


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


if __name__ == '__main__':
    
    start_date = '2005-01-01'
    end_date = '2025-12-31'
    
    vix_df = web.DataReader('VIXCLS', 'fred', start=start_date, end=end_date)
    vix_df = vix_df.resample('QE').mean()
    vix_df.columns = ['vix']
    
    real_gdp = web.DataReader('A191RL1Q225SBEA', 'fred', start=start_date, end=end_date)
    real_gdp = real_gdp.resample('QE').last() # already quarterly but needs to be aligned with the other dates
    real_gdp.columns = ['real_gdp_growth']
    
    baa_df = web.DataReader('BAA10Y', 'fred', start=start_date, end=end_date)
    baa_df = baa_df.resample('QE').mean()
    baa_df.columns = ['credit_spread(10Y)']
    
    cpi_start_date = '2004-01-01'
    cpi_df = web.DataReader('CPIAUCSL', 'fred', start=cpi_start_date, end=end_date)
    cpi_df = cpi_df.pct_change(12) * 100    # YoY % change on monthly series
    cpi_df = cpi_df.resample('QE').last().dropna() # dropping 2004 values (NaN)
    cpi_df.columns = ['cpi_yoy']
    
    df_macro = vix_df.join([real_gdp, baa_df, cpi_df], how='outer')
    df_macro.index.name = 'quarter_date'
    df_macro = df_macro.reset_index()
    
    with duckdb.connect(str(DB_PATH)) as con:
        con.execute('DROP TABLE IF EXISTS macro_indicators')
        con.register('df_macro', df_macro)
        con.execute('CREATE TABLE macro_indicators AS SELECT * FROM df_macro')
        rows = con.execute('SELECT COUNT(*) FROM macro_indicators').fetchone()[0]
        print(f'Saved {rows} rows to macro_indicators')
    
    

    
    