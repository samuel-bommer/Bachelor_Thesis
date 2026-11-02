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
PHARMA_SECTOR_BETA = 0.98 # Damodaran numbers

def get_cost_equity(riskfree: pd.Series, beta: pd.Series ) -> pd.Series:
    """
    The cost of equity: r_e = rf + beta * ERP
    where the ERP is kept constant. 
    
    If no beta is in the list, we use the Pharma
    sector beta from Damodaran
    https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/Betas.html
    """
    
    beta_filled = beta.fillna(PHARMA_SECTOR_BETA)
    cost_of_equity = riskfree + beta_filled * EQUITY_RISK_PREMIUM
    return cost_of_equity

# ========================== Cost of Debt ===========================

COVERAGE_SPREADS = [ # interest coverage low, high, spread
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

PHARMA_SECTOR_SPREAD = 0.011

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
    return PHARMA_SECTOR_SPREAD


def get_cost_debt(ebit: pd.Series, interest: pd.Series, riskfree: pd.Series) -> pd.Series:
    """
    The cost of debt: r_d = rf + synthetic_rating
    the synthetic rating is calculated by Damodarans
    table;
    https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ratings.html
    """
    coverage_ratio = (ebit / interest).replace([np.inf, -np.inf], np.nan)
    
    spreads = []
    for cov in coverage_ratio:
        if pd.isna(cov):
            spreads.append(PHARMA_SECTOR_SPREAD)
        else:
            spreads.append(get_spread(cov))
            
    spread_series = pd.Series(spreads, index=ebit.index)
    cost_of_debt = spread_series + riskfree
    return cost_of_debt

# ============================= WACC =============================

PHARMA_DEBT_WEIGHT = 0.14

def get_wacc(quarter_date: pd.Series,
             riskfree: pd.Series, 
             ebit: pd.Series,
             interest: pd.Series,
             beta: pd.Series,
             market_cap: pd.Series,
             debt: pd.Series
             ) -> pd.Series:
    """
    Get the wacc.
    Using US marginal tax rates of 0.35 before 2018 and 
    0.21 starting 2018
    
    Using Damodaran debt to firm_value ratio as a fallback
    https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/dbtfund.html
    """
    
    tax = pd.Series(np.where(quarter_date < '2018-01-01', 0.35, 0.21), index=ebit.index)
    cost_of_equity = get_cost_equity(riskfree, beta)
    cost_of_debt = get_cost_debt(ebit, interest, riskfree)
    
    firm_value = market_cap + debt

    equity_portion = cost_of_equity * (market_cap / firm_value).fillna(1 - PHARMA_DEBT_WEIGHT)
    debt_portion = cost_of_debt * (debt / firm_value).fillna(PHARMA_DEBT_WEIGHT) * (1-tax)
    wacc = equity_portion + debt_portion
    
    # apply a floor to bad data and outliers 
    WACC_FLOOR = riskfree + 0.01
    wacc = wacc.where(wacc >= WACC_FLOOR, np.nan)
    
    return wacc


if __name__ == '__main__':
    wacc = get_wacc(
        df_wacc['quarter_date'],
        df_wacc['DGS10'],
        df_wacc['ebit_hist'],
        df_wacc['interest_expense'],
        df_wacc['beta'],
        df_wacc['market_cap'],
        df_wacc['total_debt']
        )
    
    df_wacc_out = pd.DataFrame({
        'Instrument': df_wacc['Instrument'],
        'quarter_date': df_wacc['quarter_date'],
        'wacc': wacc
    })
    
    with duckdb.connect(str(DB_PATH)) as con:
        con.execute('DROP TABLE IF EXISTS wacc_computed')
        con.register('df_wacc_out', df_wacc_out[['Instrument', 'quarter_date', 'wacc']])
        con.execute('CREATE TABLE wacc_computed AS SELECT * FROM df_wacc_out')