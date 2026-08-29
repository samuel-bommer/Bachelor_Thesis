"""
In order to calculate the monthly betas,
we need the monthly  return of the S&P500
as a reference index to run our regression
according to CAPM.
"""

import yfinance as yf
import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'

if __name__ == '__main__':

    ticker_sp = '^GSPC'
    SP_df = yf.download(ticker_sp, start='2000-01-01', end='2025-12-31', interval='1mo', auto_adjust=True)
    SP_df = SP_df[('Close', '^GSPC')].reset_index()
    SP_df.columns = ['date', 'close']
    SP_df['mkt_return'] = SP_df['close'].pct_change()
    SP_df.dropna(subset=['mkt_return'], inplace=True)
    
    with duckdb.connect(str(DB_PATH)) as con:
        con.execute('DROP TABLE IF EXISTS sp500_monthly')
        con.register('sp500_df', SP_df)
        con.execute('CREATE TABLE sp500_monthly AS SELECT * FROM sp500_df')
        rows = con.execute('SELECT COUNT(*) FROM sp500_monthly').fetchone()[0]
        print(f'Saved {rows} rows to sp500_monthly')
    
    