"""
Extended R&D history pull (1995–2004).

Damodaran R&D capitalisation requires ~10 years of R&D history prior to the
study period. This pulls only TR.ResearchAndDevelopment going back to 1995
and stores it in rd_history_raw. The main fundamentals_raw table covers
2005–2025, so together they give the full history needed to build the
research asset at every quarter-end in the panel.
"""

import os
os.environ['LD_LIB_CONFIG_PATH'] = '/Users/sam/Code/bachelor_thesis/src'
import lseg.data as ld
import lseg_consensus

FIELDS = [
    'TR.ResearchAndDevelopment',
    'TR.F.RnD'
]

PARAMETERS = {'SDate': '1995-01-01', 'EDate': '2004-12-31', 'Frq': 'FQ', 'Curn': 'USD'}

if __name__ == '__main__':
    ld.open_session()
    lseg_consensus.pull_and_save('rd_history_raw', FIELDS, PARAMETERS, chunk_size=8)
    ld.close_session()
