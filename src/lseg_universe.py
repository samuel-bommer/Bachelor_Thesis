"""
Retireving the data from LSEG
"""

import os
os.environ['LD_LIB_CONFIG_PATH'] = '/Users/sam/Code/bachelor_thesis/src'
import lseg.data as ld
import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "thesis.duckdb"



def get_lseg_universe() -> pd.DataFrame:
    """
    Function returns a DataFrame with the Data
    needed for the Analysis
    """
    
    ld.open_session()
    df_universe_active = ld.get_data(
        universe=['SCREEN(U(IN(Equity(active, public, primary))),'
                  'IN(TR.TRBCIndustryCode,"56201040"),'
                  'IN(TR.HQCountryCode,"US"))'],
        fields=['TR.RIC', 'TR.OrganizationID',
                'TR.CommonName','TR.IsDelistedQuote']
    )
    
    df_universe_inactive = ld.get_data(
        universe=['SCREEN(U(IN(Equity(inactive, public, primary))),'
                  'IN(TR.TRBCIndustryCode,"56201040"),'
                  'IN(TR.HQCountryCode,"US"))'],
        fields=['TR.RIC', 'TR.OrganizationID',
                'TR.CommonName', 'TR.IsDelistedQuote']
    )

    df_universe = pd.concat([df_universe_active, df_universe_inactive], ignore_index=True)
    return df_universe

def save_universe(df: pd.DataFrame) -> None:
    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE OR REPLACE TABLE universe AS SELECT * FROM df")
    con.close()
    