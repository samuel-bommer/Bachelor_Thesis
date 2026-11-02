"""
Do the valuations make sense? Check DCF bias diagnostics.
Reads directly from the valuation_errors table and describes the distributions
of important variables.
"""

import duckdb
import numpy as np
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


if __name__ == '__main__':
    with duckdb.connect(str(DB_PATH)) as con:
        df = con.execute("SELECT * FROM valuation_errors").df()

    print("=" * 60)
    print("WACC distribution")
    print("=" * 60)
    print(df['wacc_used'].describe(percentiles=[.1, .25, .5, .75, .9]).round(4))

    print("\n" + "=" * 60)
    print("LTG used (capped)")
    print("=" * 60)
    print(df['ltg_used'].describe(percentiles=[.1, .25, .5, .75, .9]).round(4))

    print("\n" + "=" * 60)
    print("TV share of firm value")
    print("=" * 60)
    print(df['tv_share'].describe(percentiles=[.1, .25, .5, .75, .9]).round(3))

    print("\n" + "=" * 60)
    print("VE firm")
    print("=" * 60)
    ve = df['valuation_error_firm'].replace([np.inf, -np.inf], np.nan)
    print(ve.describe(percentiles=[.1, .25, .5, .75, .9]).round(3))

    print("\n" + "=" * 60)
    print("Median TV share by year")
    print("=" * 60)
    df['year'] = df['quarter_date'].astype('datetime64[ns]').dt.year
    print(df.groupby('year')['tv_share'].median().round(3).to_string())
