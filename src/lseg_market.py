"""
Markets
"""

import lseg.data as ld
import lseg_consensus


FIELDS_MARKETCAP = [
    'TR.CompanyMarketCap.date',
    'TR.CompanyMarketCap',
    'TR.PriceClose',
    'TR.SharesOutstanding',
]

FIELDS_RETURNS = [
    'TR.TotalReturn.date',
    'TR.TotalReturn'
]

PARAMS_MARKETCAP = {'SDate': '2005-01-01', 'EDate': '2025-12-31', 'Frq': 'CQ', 'Curn': 'USD'}
PARAMS_RETURNS   = {'SDate': '2000-01-01', 'EDate': '2025-12-31', 'Frq': 'CM', 'Curn': 'USD'}


if __name__ == "__main__":
    ld.open_session()
    lseg_consensus.pull_and_save('market_cap_raw', FIELDS_MARKETCAP, PARAMS_MARKETCAP)
    lseg_consensus.pull_and_save('returns_raw',    FIELDS_RETURNS,   PARAMS_RETURNS)
    ld.close_session()