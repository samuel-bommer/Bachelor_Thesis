"""
Calculating firm betas according to the 
CAPM with Damodaran's example.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import duckdb

DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'

with duckdb.connect(str(DB_PATH)) as con:
    df_returns = con.execute("""
        SELECT
            r.Instrument,
            r.Date::DATE AS date,
            CAST(r."Total Return" AS DOUBLE) / 100.0 AS firm_return,
            s.return AS market_return
        FROM returns_raw r
        JOIN sp500_monthly s ON r.Date::DATE = s.date
        ORDER BY r.Instrument, r.Date
    """).df()

    quarters = con.execute("""
        SELECT DISTINCT Instrument, quarter_date
        FROM panel_clean
        ORDER BY Instrument, quarter_date
    """).df()

