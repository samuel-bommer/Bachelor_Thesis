"""
Create a useable dataframe: query of duckdb
database.
"""

from pathlib import Path
import pandas as pd
import duckdb

DB_PATH = Path(__file__).with_name('thesis.duckdb')

def build_spine() -> pd.DataFrame:
    """
    Builds the practical database that we can use and
    load into memory.
    
    Returns a df for inspection.
    """
    
    
    with duckdb.connect(str(DB_PATH)) as con:
        con.execute("""
            CREATE OR REPLACE TABLE panel_clean AS

            WITH spine AS (
                SELECT DISTINCT
                    u.Instrument,
                    c.Date AS quarter_date
                FROM universe u
                CROSS JOIN (
                    SELECT DISTINCT Date FROM consensus_raw
                ) c
            ),

            -- point-in-time fundamentals: most recent announced before quarter-end
            fundamentals_pit AS (
                SELECT
                    s.Instrument,
                    s.quarter_date,
                    f.*
                FROM spine s
                ASOF JOIN fundamentals_raw f
                    ON s.Instrument = f.Instrument
                    AND f."Announcement Date" <= s.quarter_date
            )

            SELECT
                s.Instrument,
                s.quarter_date,
                -- consensus fields
                c."EPS Mean - Mean (FY1)"   AS eps_fy1,
                c."EPS Mean - Mean (FY2)"   AS eps_fy2,
                c."EPS Mean - Mean (FY3)"   AS eps_fy3,
                c."Revenue Mean (FY1)"      AS rev_fy1,
                c."Revenue Mean (FY2)"      AS rev_fy2,
                c."EBIT Mean (FY1)"         AS ebit_fy1,
                c."EBIT Mean (FY2)"         AS ebit_fy2,
                c."LTG Mean"                AS ltg_mean,
                -- market cap
                m."Company Market Cap"      AS market_cap,
                -- fundamentals
                fp."Revenue"                AS revenue_hist,
                fp."EBIT"                   AS ebit_hist,
                fp."Depreciation & Amort."  AS da,
                fp."Capital Expenditures"   AS capex,
                fp."Total Debt Outstanding" AS total_debt,
                fp."Cash & ST Investments"  AS cash,
                fp."Income Tax Rate"        AS tax_rate,
                fp."Total Equity"           AS book_equity,
                fp."R&D Expense"            AS rd_expense

            FROM spine s
            LEFT JOIN consensus_raw c
                ON s.Instrument = c.Instrument AND s.quarter_date = c.Date
            LEFT JOIN market_cap_raw m
                ON s.Instrument = m.Instrument AND s.quarter_date = m.Date
            LEFT JOIN fundamentals_pit fp
                ON s.Instrument = fp.Instrument AND s.quarter_date = fp.quarter_date
        """)
        
        df = con.execute('SELECT * FROM panel_clean').df()
    
    print(f"Panel built: {len(df)} firm-quarters")
    return df