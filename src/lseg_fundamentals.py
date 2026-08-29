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
    'TR.NetIncome',
    'TR.DepreciationAmort',
    'TR.DepreciationAmortizationActValue',
    'TR.F.DeprDeplAmortTot',
    'TR.CapitalExpenditures',
    'TR.TotalCurrentAssets',
    'TR.TotalCurrentLiabilities',
    'TR.TotalDebtOutstanding',
    'TR.CashAndSTInvestments',
    'TR.InterestExpense',
    'TR.F.IncTax',
    'TR.TotalEquity',
    'TR.ResearchAndDevelopment',
    'TR.F.RnD',
    'TR.OriginalAnnouncementDate',
    'TR.WACCTaxRate',
    'TR.TaxRateMean',
    'TR.F.DivPaidCashTotCF',
    'TR.WACC'
]

PARAMETERS = {'SDate': '2005-01-01', 'EDate': '2025-12-31', 'Frq': 'FQ', 'Curn' : 'USD'}


if __name__ == "__main__":
    ld.open_session()
    lseg_consensus.pull_and_save('fundamentals_raw', FIELDS, PARAMETERS, chunk_size=8)
    ld.close_session()


