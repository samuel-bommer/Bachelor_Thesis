"""
Consensus
"""

import os
os.environ['LD_LIB_CONFIG_PATH'] = '/Users/sam/Code/bachelor_thesis/src'
import lseg.data as ld
import duckdb
import pandas as pd
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'
CHUNK_SIZE = 15
SLEEP = 1.0

def get_rics() -> list:
    """
    Get the list of RICS from the lseg_universe retrieve
    from the db Database
    """
    
    with duckdb.connect(str(DB_PATH)) as con:
        return con.execute('SELECT Instrument FROM universe').df()['Instrument'].tolist()
    
    
def pull_and_save(table_name: str, fields: list, parameters: dict) -> None:
    """
    Download the numbers
    """
    
    rics = get_rics()
    chunks = [rics[i:i+CHUNK_SIZE] for i in range(0, len(rics), CHUNK_SIZE)]

    with duckdb.connect(str(DB_PATH)) as con:
        con.execute(f'DROP TABLE IF EXISTS {table_name}')
        
        for i, chunk in enumerate(chunks):
            df = ld.get_data(universe=chunk, fields=fields, parameters=parameters)
            con.register('chunk_df', df)
            if i == 0:
                con.execute(f'CREATE TABLE {table_name} AS SELECT * FROM chunk_df')
            else:
                con.execute(f'INSERT INTO {table_name} SELECT * FROM chunk_df')
            print(f'Chunk {i+1}/{len(chunks)} done')
            time.sleep(SLEEP)
            

FIELDS = [
    'TR.EPSMean(Period=FY1)', 'TR.EPSMean(Period=FY2)', 'TR.EPSMean(Period=FY3)',
    'TR.RevenueMean(Period=FY1)', 'TR.RevenueMean(Period=FY2)',
    'TR.EBITMean(Period=FY1)', 'TR.EBITMean(Period=FY2)',
    'TR.LTGMean', 'TR.NumberOfAnalysts(Period=FY1)',
]

PARAMETERS = {'SDate': '2005-01-01', 'EDate': '2025-12-31', 'Frq': 'CQ'}

ld.open_session()
pull_and_save('consensus_raw', FIELDS, PARAMETERS)
ld.close_session()