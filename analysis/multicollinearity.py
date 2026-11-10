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

df_analysis_exp = df_analysis[['vix', 'real_gdp_growth',
                               'credit_spread(10Y)',
                               'cpi_yoy', 'term_spread',
                               'ind_prod_growth']].copy()


def correlation_matrix(df: pd.DataFrame, graph: bool = True) -> pd.DataFrame:
    """
    Build a correlation analysis matrix
    """
    
    corr_matrix = df.corr()
    
    if graph:
        plt.figure(figsize=(10,6))
        sns.heatmap(corr_matrix, annot=True, fmt=".2f")
        
        plt.title(f'Correlation Heatmap Analysis')
        plt.show()
    
    return corr_matrix


def principal_component_analysis(df: pd.DataFrame, graph: bool = True) -> pd.DataFrame:
    """
    Run the PCA using statsmodels
    """
    
    pca_model = PCA(df, standardize=True)
    
    explained = pca_model.eigenvals / pca_model.eigenvals.sum()
    cumulative = np.cumsum(explained)

    if graph:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(range(1, len(explained) + 1), explained, label='Individual')
        ax.plot(range(1, len(explained) + 1), cumulative, marker='o', color='red', label='Cumulative')
        ax.axhline(0.9, linestyle='--', color='grey', linewidth=0.8)
        ax.set_xlabel('Principal Component')
        ax.set_ylabel('Variance Explained')
        ax.set_title('PCA Plot')
        ax.legend()
        plt.tight_layout()
        plt.show()

    print(pca_model.loadings.round(3))
        
    return pca_model


if __name__ == '__main__':
    corr_matrix_analysis = correlation_matrix(df_analysis_exp)
    principal_components = principal_component_analysis(df_analysis_exp)


"""
In the correlation heatmap we see that our variables are generally not 
highly correlated; except for VIX, credit spread, and industrial production.

In the PCA, the first factor "only" explain about 40% of the data, which 
means that our factors are largely orthogonal.
"""
