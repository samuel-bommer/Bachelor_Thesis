"""
This file is for testing multicollinearity in our model variables.

For this a simple correlation matrix is used and later followed up
by a Principal Component Analysis.
"""

import duckdb
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.multivariate.pca import PCA


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


with duckdb.connect(DB_PATH) as con:
    df_analysis = con.execute("SELECT * FROM analysis_table").df()

