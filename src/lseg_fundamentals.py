"""
Fundamentals
"""

import lseg_consensus
import lseg.data as ld

FIELDS = [
    'TR.Revenue.date',
    'TR.Revenue',
    'TR.EBIT',
    'TR.DepreciationAmort',
    'TR.CapitalExpenditures',
    'TR.TotalCurrentAssets', 
    'TR.TotalCurrentLiabilities',
    'TR.TotalDebtOutstanding', 
    'TR.CashAndSTInvestments',
    'TR.InterestExpense',
    'TR.IncomeTaxRate',
    'TR.TotalEquity', 
    'TR.ResearchAndDevelopment',
    'TR.DividendsPaid',
    'TR.OriginalAnnouncementDate',
]

PARAMETERS = {'SDate': '2005-01-01', 'EDate': '2025-12-31', 'Frq': 'FQ', 'Curn' : 'USD'}


if __name__ == "__main__":
    ld.open_session()
    lseg_consensus.pull_and_save('fundamentals_raw', FIELDS, PARAMETERS)
    ld.close_session()


