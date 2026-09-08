"""
Smoothen out CapEx and D&A
"""

import numpy as np
import pandas as pd
from pathlib import Path
import duckdb


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'

    
with duckdb.connect(str(DB_PATH)) as con:
    df_capex_da = con.execute('SELECT Instrument, quarter_date, capex, da_cfs FROM panel_clean').df()
        
