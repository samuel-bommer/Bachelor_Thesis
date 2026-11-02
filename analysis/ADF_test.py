"""
ADF-test using statsmodels to 
look for a unit root
"""


import duckdb
from pathlib import Path
import statsmodels.api as sm
import pandas as pd


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


