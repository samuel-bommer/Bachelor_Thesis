"""
Fundamentals.

Get the fundamentals from LSEG. Whilst most are actively 
used in the DCF, others are essentially a sanity check (e.g. TR.WACC)
for the  DCF calculation.
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
    'TR.TotalEquity', 
    'TR.ResearchAndDevelopment',
    'TR.OriginalAnnouncementDate',
    'TR.WACCTaxRate',
    'TR.TaxRateMean',
    'TR.F.DivPaidCashTotCF',
    'TR.WACCERP',
    'TR.WACC'
]

PARAMETERS = {'SDate': '2005-01-01', 'EDate': '2025-12-31', 'Frq': 'FQ', 'Curn' : 'USD'}


if __name__ == "__main__":
    ld.open_session()
    lseg_consensus.pull_and_save('fundamentals_raw', FIELDS, PARAMETERS)
    ld.close_session()


