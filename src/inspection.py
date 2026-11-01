"""
This file is stricly for inspecting the data that
we retrieved. (Essentially a helper file)

This is not used for anything other than looking
and checking the tables that we have in the DuckDB.

I run this file through a jupyter notebook and
interactively explore the data
"""


import duckdb
from pathlib import Path
import pandas as pd
import os


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


with duckdb.connect(DB_PATH) as con:
    df_universe = con.execute("SELECT * FROM universe LIMIT 100").df()
    df_consensus = con.execute("SELECT * FROM consensus_raw LIMIT 1000").df()
    df_fundamentals = con.execute("SELECT * FROM fundamentals_raw").df()
    df_rd_hist = con.execute("SELECT * FROM rd_history_raw LIMIT 1000").df()
    df_marketcap = con.execute("SELECT * FROM market_cap_raw LIMIT 1000").df()
    df_price = con.execute("SELECT * FROM returns_raw LIMIT 1000").df()
    df_panel_clean = con.execute("SELECT * FROM panel_clean").df()
    df_betas = con.execute("SELECT * FROM betas").df()
    df_rd_capitalised = con.execute("SELECT * FROM rd_capitalised").df()
    df_riskfree = con.execute("SELECT * FROM riskfreerate").df()
    df_wacc_computed = con.execute("SELECT * FROM wacc_computed").df()
    df_ve_clean = con.execute("SELECT * FROM valuation_errors").df()
    df_macro_indicators = con.execute("SELECT * FROM macro_indicators").df()

# ========================== Inspect in CSV =========================

def inspect_csv(df: pd.DataFrame, name: str='data.csv', sort=True) -> None:
    """
    Download csv file
    """
    
    path_download = '/Users/sam/Downloads'
    file_output = os.path.join(path_download, name)
    if sort:
        df.sort_values(['Instrument', 'quarter_date'], inplace=True)
    df.to_csv(file_output)
    

if __name__ == '__main__':
    
    #inspect_csv(df_panel_clean, 'panel_clean_data.csv')
    #inspect_csv(df_ve_clean, 'valuation_error.csv')
    #inspect_csv(df_fundamentals, 'fundamentals.csv', sort=False)
    #inspect_csv(df_consensus, 'consensus.csv', sort=False)
    inspect_csv(df_ve_clean, 've_clean.csv', sort=False)
    
