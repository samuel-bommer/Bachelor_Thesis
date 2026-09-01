"""
Caluclating the WACC for every
Instrument.

WACC = E /(D+E) * r_e + D /(D+E) * r_d * (1-tax)
"""


import pandas as pd
import numpy as np
import duckdb
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'

with duckdb.connect(str(DB_PATH)) as con:
    df_wacc = con.execute("""
        SELECT
            Instrument,
            quarter_date,
            DGS10,
            beta,
            ebit_hist,
            interest_expense,
            total_debt,
            market_cap
        FROM panel_clean
    """).df()

# ========================= Cost of Equity ==========================

EQUITY_RISK_PREMIUM = 0.05

def get_cost_equity(erp: float, riskfree: float) -> float:
    """
    The cost of equity: r_e = rf + beta * ERP
    where the ERP is kept constant
    """
    pass

# ========================== Cost of Debt ===========================

COVERAGE_SPREADS = [ #interest coverage low, high, spread
    (-100000, 0.1999,  0.1900),  # D2/D
    (0.20,    0.6499,  0.1600),  # C2/C
    (0.65,    0.7999,  0.1261),  # Ca2/CC
    (0.80,    1.2499,  0.0885),  # Caa/CCC
    (1.25,    1.4999,  0.0509),  # B3/B-
    (1.50,    1.7499,  0.0321),  # B2/B
    (1.75,    1.9999,  0.0275),  # B1/B+
    (2.00,    2.2499,  0.0184),  # Ba2/BB
    (2.25,    2.4999,  0.0138),  # Ba1/BB+
    (2.50,    2.9999,  0.0111),  # Baa2/BBB
    (3.00,    4.2499,  0.0089),  # A3/A-
    (4.25,    5.4999,  0.0078),  # A2/A
    (5.50,    6.4999,  0.0070),  # A1/A+
    (6.50,    8.4999,  0.0055),  # Aa2/AA
    (8.50,    100000,  0.0040),  # Aaa/AAA
]

def get_spread(interest_coverage: float) -> float:
    """
    Return the synthetic spread from the Damodaran table
    given the interest coverage ratio. 
    
    If no spread is found, we default to an industry 
    standard (Baaa2 / BBB)
    """
    
    for lower, upper, spread in COVERAGE_SPREADS:
        if lower <= interest_coverage <= upper:
            return spread
        return 0.0111


def get_cost_debt(spread: float, riskfree: float) -> float:
    """
    The cost of debt: r_d = rf + synthetic_rating
    the synthetic rating is calculated by Damodarans
    table;
    https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ratings.html
    """
    pass

# ============================= WACC =============================

def get_wacc() -> float:
    """
    Get the wacc
    """
    pass 



if __name__ == '__main__':
    pass