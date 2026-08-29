"""
Captialising R&D according to Damodaran
using 10y worth of R&D spending with a linear
amortisation
"""

import numpy as np
import pandas as pd
from pathlib import Path
import duckdb
from dateutil.relativedelta import relativedelta


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


with duckdb.connect(str(DB_PATH)) as con:
    df_rd_hist = con.execute("SELECT * FROM rd_history_raw").df()
    df_fundamentals = con.execute("SELECT * FROM fundamentals_raw").df()
    
    
df_rd_fund = df_fundamentals[['Instrument', 'Research & Development Expense', 'Date']]
df_rd_fund.rename(columns={
    'Research & Development Expense': 'Research And Development'
    }, inplace=True)

df_rd_combined = pd.concat([df_rd_fund, df_rd_hist], ignore_index=True).sort_values(['Instrument', 'Date'])

