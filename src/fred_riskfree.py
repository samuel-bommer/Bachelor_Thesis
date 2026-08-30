"""
Retrieving the risk free rate
(US treasury yield) as a proxy.

DGS10 is the market yield on
US Treasury Yields at 10-y constant
maturity

The output is given in percentage, so
we need to divide by 100. The series is
Daily so we only keep the quarterpoints 
we need.
"""


import duckdb
from pathlib import Path
import pandas_datareader as web


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


if __name__ == '__main__':
    
    start_date = '2005-01-01'
    end_date = '2025-12-31'
    
    df_riskfree = web.DataReader('DGS10', 'fred', start=start_date, end=end_date)
    df_riskfree['DGS10'] = df_riskfree['DGS10'] / 100
    df_riskfree = df_riskfree.reset_index().rename(columns={'DATE': 'date'})
    df_riskfree = df_riskfree.resample('QE', on='date').last().reset_index()
    
    with duckdb.connect(str(DB_PATH)) as con:
        con.execute('DROP TABLE IF EXISTS riskfreerate')
        con.register('df_riskfree', df_riskfree)
        con.execute('CREATE TABLE riskfreerate AS SELECT * FROM df_riskfree')
        rows = con.execute('SELECT COUNT(*) FROM riskfreerate').fetchone()[0]
        print(f'Saved {rows} rows to riskfreerate')
    