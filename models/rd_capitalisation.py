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
df_rd_combined = df_rd_combined.dropna(subset=['Date', 'Research And Development'])
df_rd_combined = df_rd_combined.drop_duplicates(subset=['Instrument', 'Date'])

# ====================== R&D Captialisation =========================

weights = np.array([weight for weight in np.arange(1, 0, -0.1)])

def capitalised_research_calc(series: pd.Series) -> float:
    """
    Summing up and linearly weighing R&D expense
    """
    n_weights = len(series)
    weight = weights[:n_weights][::-1]
    weighted_sum = np.dot(series, weight)
    
    return weighted_sum

research_asset = (
    df_rd_combined
    .groupby('Instrument')['Research And Development']
    .rolling(window=10, min_periods=1)
    .apply(capitalised_research_calc, raw=False)
    .reset_index(level=0, drop=True)
)

df_rd_combined['Research Asset'] = research_asset
df_rd_combined['RD Amortisation'] = df_rd_combined['Research Asset'] / 10

# ====================== Saving output in DB =========================

with duckdb.connect(str(DB_PATH)) as con:
    con.execute('DROP TABLE IF EXISTS rd_capitalised')
    con.register('df_rd_combined', df_rd_combined)
    con.execute("""
        CREATE TABLE rd_capitalised AS
        SELECT
            Instrument,
            Date::DATE AS quarter_date,
            "Research Asset" AS research_asset,
            "RD Amortisation" AS rd_amortisation
        FROM df_rd_combined
        WHERE Date >= '2005-01-01'
    """)
