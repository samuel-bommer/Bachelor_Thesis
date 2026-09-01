""""
Full DCF 
"""

import pandas as pd
import numpy as np
from pathlib import Path
import duckdb


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


def load_panel() -> pd.DataFrame:
    with duckdb.connect(str(DB_PATH)) as con:
        return con.execute("SELECT * FROM panel_clean").df()