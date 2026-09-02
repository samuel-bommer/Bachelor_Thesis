"""
Calculating firm betas according to the 
CAPM with Damodaran's example.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import duckdb
from dateutil.relativedelta import relativedelta


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


with duckdb.connect(str(DB_PATH)) as con:
    df_returns = con.execute("""
        SELECT
            r.Instrument,
            r.Date::DATE AS date,
            CAST(r."Total Return" AS DOUBLE) / 100.0 AS firm_return,
            s.mkt_return AS market_return
        FROM returns_raw r
        JOIN sp500_monthly s ON DATE_TRUNC('month', r.Date::DATE) = DATE_TRUNC('month', s.date)
        ORDER BY r.Instrument, r.Date
    """).df()

# ========================= Beta calculation ===========================    

def OLS_beta(firm_return:float, market_return: float) -> float:
    """
    Calculate beta using OLS.
    
    Beta = COV(X,Y) / VAR(Y)
    """
    
    covariance = np.cov(firm_return, market_return)
    variance_market = np.var(market_return)
    beta = covariance[0,1] / variance_market
    return beta


quarter_points_bool = df_returns['date'].dt.month.isin([3, 6, 9, 12])
quarter_points = df_returns[quarter_points_bool][['Instrument', 'date']]
quarter_points = quarter_points.drop_duplicates(subset=['Instrument', 'date'])

betas = []

for _, row in quarter_points.iterrows():
    
    window_start = row['date'] - relativedelta(months=60)
    
    window = df_returns[
        (df_returns['Instrument'] == row['Instrument']) &
        (df_returns['date'] > window_start) &
        (df_returns['date'] <= row['date'])
    ]
    
    if len(window) < 12:
        beta = np.nan
        
    else:
        beta = OLS_beta(window['firm_return'], window['market_return'])
    
    betas.append({
        'Instrument': row['Instrument'],
        'quarter_date': row['date'],
        'beta': beta
    })


if __name__ == '__main__':
    
    df_betas = pd.DataFrame(betas)

    with duckdb.connect(str(DB_PATH)) as con:
        con.execute('DROP TABLE IF EXISTS betas')
        con.register('df_betas', df_betas)
        con.execute('CREATE TABLE betas AS SELECT * FROM df_betas')
