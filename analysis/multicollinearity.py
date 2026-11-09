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


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame | None:
    """
    Build a correlation analysis matrix
    """
    
    corr_matrix = df.corr()
    
    plt.figure(figsize=(10,6))
    sns.heatmap(corr_matrix, annot=True, fmt=".2f")
    
    plt.title(f'Correlation Heatmap Analysis')
    plt.show()
    
    return corr_matrix


if __name__ == '__main__':
    corr_matrix_analysis = correlation_matrix(df_analysis)


"""
In the correlation heatmap we see that our variables are generally not 
highly correlated; except for VIX, credit spread, and industrial production.
"""
