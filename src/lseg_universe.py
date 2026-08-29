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
    
    df_universe_active = ld.get_data(
        universe=['SCREEN(U(IN(Equity(active, public, primary))),'
                  'IN(TR.TRBCIndustryCode,"56201040"),'
                  'IN(TR.HQCountryCode,"US"))'],
        fields=['TR.RIC', 'TR.OrganizationID',
                'TR.CommonName', 'TR.IsDelistedQuote',
                'TR.InstrumentDelistedDate', 'TR.TRBCIndustryCode', 'TR.HQCountryCode']
    )

    df_universe_inactive = ld.get_data(
        universe=['SCREEN(U(IN(Equity(inactive, public, primary))),'
                  'IN(TR.TRBCIndustryCode,"56201040"),'
                  'IN(TR.HQCountryCode,"US"))'],
        fields=['TR.RIC', 'TR.OrganizationID',
                'TR.CommonName', 'TR.IsDelistedQuote',
                'TR.InstrumentDelistedDate', 'TR.TRBCIndustryCode', 'TR.HQCountryCode']
    )
    
    df_universe = pd.concat([df_universe_active, df_universe_inactive], ignore_index=True)
    return df_universe

def save_universe(df: pd.DataFrame) -> None:
    """
    Save the current universe to the DB
    """
    
    with duckdb.connect(str(DB_PATH)) as con:
        con.register('universe_df', df)
        con.execute("CREATE OR REPLACE TABLE universe AS SELECT * FROM universe_df")
        print(f'Retrieve done.')
        
def IpoDate_retrieve() -> None:
    """
    IPO date has to be retrieved seperately and thn
    append it to the current table
    """
    
    with duckdb.connect(str(DB_PATH)) as con:
        rics = con.execute("SELECT Instrument FROM universe").df()["Instrument"].tolist()
    
    df_ipo = ld.get_data(
        universe=rics,
        fields=['TR.IPODate']
    )
    
    with duckdb.connect(str(DB_PATH)) as con:
        con.register('ipo_df', df_ipo)
        con.execute("ALTER TABLE universe ADD COLUMN IF NOT EXISTS IPODate DATE")
        con.execute("""
            UPDATE universe
            SET IPODate = ipo_df."IPO Date"
            FROM ipo_df
            WHERE universe.Instrument = ipo_df.Instrument
        """)


if __name__ == "__main__":
    ld.open_session()
    df = get_lseg_universe()
    save_universe(df)
    IpoDate_retrieve()
    ld.close_session()