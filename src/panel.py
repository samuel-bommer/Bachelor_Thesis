"""
Create a useable dataframe: query of duckdb
database.
"""

from pathlib import Path
import pandas as pd
import duckdb


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


def build_data() -> pd.DataFrame:
    """
    Builds the practical database that we can use and
    load into memory.
    
    Returns a df for inspection.
    """
    
    
    with duckdb.connect(str(DB_PATH)) as con:
        con.execute("""
            CREATE OR REPLACE TABLE panel_clean AS

            WITH quarter_ends AS (
                SELECT (s + INTERVAL '1 MONTH' - INTERVAL '1 DAY')::DATE AS quarter_date
                FROM generate_series(DATE '2005-03-01', DATE '2025-12-01', INTERVAL '3 MONTHS') t(s)
            ),

            spine AS (
                SELECT u.Instrument, q.quarter_date
                FROM universe u
                CROSS JOIN quarter_ends q
            ),

            consensus_pit AS (
                SELECT
                    s.Instrument,
                    s.quarter_date,
                    c."Earnings Per Share - Mean"    AS eps_mean_fy1,
                    c."Earnings Per Share - Mean_1"  AS eps_mean_fy2,
                    c."Earnings Per Share - Mean_2"  AS eps_mean_fy3,
                    c."Revenue - Mean"               AS rev_mean_fy1,
                    c."Revenue - Mean_1"             AS rev_mean_fy2,
                    c."EBIT - Mean"                  AS ebit_mean_fy1,
                    c."EBIT - Mean_1"                AS ebit_mean_fy2,
                    c."EBITDA - Mean"                AS ebitda_mean_fy1,
                    c."EBITDA - Mean_1"              AS ebitda_mean_fy2,
                    c."Long Term Growth - Mean"      AS ltg_mean,
                    c."Number of Analysts"           AS n_analysts,
                    ROW_NUMBER() OVER (
                        PARTITION BY s.Instrument, s.quarter_date
                        ORDER BY c."Date" DESC
                    ) AS rn
                FROM spine s
                JOIN consensus_raw c
                    ON s.Instrument = c.Instrument
                    AND c."Date" <= s.quarter_date
            ),

            consensus_filtered AS (
                SELECT * FROM consensus_pit WHERE rn = 1
            ),

            fundamentals_pit AS (
                SELECT
                    s.Instrument,
                    s.quarter_date,
                    f."Revenue"                                    AS revenue_hist,
                    f."EBIT"                                       AS ebit_hist,
                    f."Net Income Incl Extra Before Distributions" AS net_income,
                    f."Depreciation And Amortization"              AS da_is,
                    f."Depreciation & Amortization - Actual"       AS da_act,
                    f."Depreciation Depletion & Amortization - Total" AS da_cfs,
                    f."Capital Expenditures, Cumulative"           AS capex,
                    f."Total Current Assets"                       AS current_assets,
                    f."Total Current Liabilities"                  AS current_liabilities,
                    f."Total Debt"                                 AS total_debt,
                    f."Cash and Short Term Investments"            AS cash,
                    f."Interest Expense"                           AS interest_expense,
                    f."Total Equity"                               AS book_equity,
                    f."Research And Development"                   AS rd_expense,
                    f."Research & Development Expense"             AS rd_cfs,
                    f."Income Taxes"                               AS income_tax,
                    f."WACC Tax Rate, (%)"                         AS wacc_tax_rate,
                    f."Tax Rate - Mean"                            AS tax_rate_mean,
                    f."Dividends Paid - Cash - Total - Cash Flow"  AS dividends_paid,
                    f."Weighted Average Cost of Capital, (%)"      AS wacc,

                    ROW_NUMBER() OVER (
                        PARTITION BY s.Instrument, s.quarter_date
                        ORDER BY f."Date" DESC
                    ) AS rn
                FROM spine s
                JOIN fundamentals_raw f
                    ON s.Instrument = f.Instrument
                    AND f."Date" <= s.quarter_date - INTERVAL '90 days'
            ),

            fundamentals_filtered AS (
                SELECT * FROM fundamentals_pit WHERE rn = 1
            ),
            
            market_pit AS (
                SELECT
                    s.Instrument,
                    s.quarter_date,
                    m."Company Market Cap"  AS market_cap,
                    m."Price Close"         AS price_close,
                    m."Outstanding Shares"  AS shares_outstanding,
                    ROW_NUMBER() OVER (
                        PARTITION BY s.Instrument, s.quarter_date
                        ORDER BY m."Date" DESC
                    ) AS rn
                FROM spine s
                JOIN market_cap_raw m
                    ON s.Instrument = m.Instrument
                    AND m."Date" <= s.quarter_date
            ),
            
            market_filtered AS (SELECT * FROM market_pit WHERE rn = 1),

            betas_deduped AS (
                SELECT
                    Instrument,
                    quarter_date,
                    beta,
                    ROW_NUMBER() OVER (
                        PARTITION BY Instrument, quarter_date
                        ORDER BY quarter_date DESC
                    ) AS rn
                FROM betas
            ),

            betas_filtered AS (SELECT * FROM betas_deduped WHERE rn = 1),

            rd_deduped AS (
                SELECT
                    Instrument,
                    quarter_date,
                    research_asset,
                    rd_amortisation,
                    ROW_NUMBER() OVER (
                        PARTITION BY Instrument, quarter_date
                        ORDER BY quarter_date DESC
                    ) AS rn
                FROM rd_capitalised
            ),

            rd_filtered AS (SELECT * FROM rd_deduped WHERE rn = 1)

            SELECT
                s.Instrument,
                s.quarter_date,

                -- consensus
                cf.eps_mean_fy1,
                cf.eps_mean_fy2,
                cf.eps_mean_fy3,
                cf.rev_mean_fy1,
                cf.rev_mean_fy2,
                cf.ebit_mean_fy1,
                cf.ebit_mean_fy2,
                cf.ebitda_mean_fy1,
                cf.ebitda_mean_fy2,
                cf.ltg_mean,
                cf.n_analysts,

                -- market
                mf.market_cap   AS market_cap,
                mf.price_close          AS price_close,
                mf.shares_outstanding   AS shares_outstanding,

                -- fundamentals (point-in-time)
                ff.revenue_hist,
                ff.ebit_hist,
                ff.net_income,
                ff.da_is,
                ff.da_act,
                ff.da_cfs,
                ff.capex,
                ff.current_assets,
                ff.current_liabilities,
                ff.total_debt,
                ff.cash,
                ff.interest_expense,
                ff.book_equity,
                ff.rd_expense,
                ff.rd_cfs,
                ff.income_tax,
                ff.wacc_tax_rate,
                ff.tax_rate_mean,
                ff.dividends_paid,
                ff.wacc,
                
                --beta
                b.beta,
                
                --rd asset
                rd.research_asset,
                rd.rd_amortisation

            FROM spine s
            LEFT JOIN consensus_filtered cf
                ON s.Instrument = cf.Instrument AND s.quarter_date = cf.quarter_date
            LEFT JOIN market_filtered mf
                ON s.Instrument = mf.Instrument AND s.quarter_date = mf.quarter_date
            LEFT JOIN fundamentals_filtered ff
                ON s.Instrument = ff.Instrument AND s.quarter_date = ff.quarter_date
            LEFT JOIN betas_filtered b
                ON s.Instrument = b.Instrument AND s.quarter_date = b.quarter_date
            LEFT JOIN rd_filtered rd
                ON s.Instrument = rd.Instrument AND s.quarter_date = rd.quarter_date
        """)
        
        df = con.execute('SELECT * FROM panel_clean').df()
    
    print(f"Panel built: {len(df)} firm-quarters")
    return df


if __name__ == '__main__':
    build_data()