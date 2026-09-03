"""
This file is stricly for inspecting the data that
we retrieved. (Essentially a helper file)

This is not used for anything other than looking
and checking the tables that we have in the DuckDB.

I run this file through a jupyter notebook and
interactively explore the data
"""

import duckdb


con = duckdb.connect('../data/thesis.duckdb')
df_universe = con.execute("SELECT * FROM universe LIMIT 100").df()
df_consensus = con.execute("SELECT * FROM consensus_raw LIMIT 1000").df()
df_fundamentals = con.execute("SELECT * FROM fundamentals_raw LIMIT 1000").df()
df_rd_hist = con.execute("SELECT * FROM rd_history_raw LIMIT 1000").df()
df_marketcap = con.execute("SELECT * FROM market_cap_raw LIMIT 1000").df()
df_price = con.execute("SELECT * FROM returns_raw LIMIT 1000").df()
df_panel_clean = con.execute("SELECT * FROM panel_clean").df()
df_betas = con.execute("SELECT * FROM betas").df()
df_rd_capitalised = con.execute("SELECT * FROM rd_capitalised").df()
df_riskfree = con.execute("SELECT * FROM riskfreerate").df()
df_wacc_computed = con.execute("SELECT * FROM wacc_computed").df()
con.execute("SHOW TABLES").df()
con.close()