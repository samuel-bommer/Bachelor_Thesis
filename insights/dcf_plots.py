"""
This specific file is for plots to check the dcf
"""

import duckdb
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


with duckdb.connect(DB_PATH) as con:
    df_ve_clean = con.execute("SELECT * FROM valuation_errors").df()
    df_analysis = con.execute("SELECT * FROM analysis_table").df()
    
    
plt.plot(df_analysis['quarter_date'], df_analysis['valuation_error_firm'])
plt.show()