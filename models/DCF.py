""""
Full DCF 
"""

import pandas as pd
import numpy as np
from pathlib import Path
import duckdb


DB_PATH = Path(__file__).parent.parent / 'data' / 'thesis.duckdb'


def load_panel() -> pd.DataFrame:
    """
    Laod the panel_clean with all the data
    that we need.
    """
    
    with duckdb.connect(str(DB_PATH)) as con:
        df_panel = con.execute("""
            SELECT p.*,
                pr.adj_ebit,
                pr.adj_ebit_margin,
                pr.smooth_capex_ratio,
                pr.smooth_da_ratio,
                pr.delta_nwc_rev,
                pr.net_reinvestment_ratio
            FROM panel_clean p
            LEFT JOIN preprocessing pr
                ON p.Instrument = pr.Instrument
                AND p.quarter_date = pr.quarter_date
            """).df()
        
    return df_panel
    

class DCF:
    
    def __init__(self, row: pd.Series) -> None:
        """
        We go by row and filter through each column 
        to get what we need from panel
        """
        
        self.ebit_fy1 = row['ebit_mean_fy1']
        self.ebit_fy2 = row['ebit_mean_fy2']
        self.eps_fy1 = row['eps_mean_fy1']
        self.eps_fy2 = row['eps_mean_fy2']
        self.eps_fy3 = row['eps_mean_fy3']
        self.rev_1 = row['rev_mean_fy1']
        self.rev_2 = row['rev_mean_fy2']
        self.ltg = row['ltg_mean']
        self.market_cap = row['market_cap']
        self.net_debt = row['total_debt'] - row['cash']
        self.n_analysts = row['n_analysts']
        self.wacc_computed = row['wacc_computed']
        self.marginal_tax = 0.35 if row['quarterdate'] < '2018-01-01' else 0.21
        # We still need to calculate the ratios
        self.da_ratio = row['smooth_da_ratio']
        self.capex_ratio = row['smooth_capex_ratio']
        #Still need delta NWC for fcff
        self.delta_nwc = row['delta_NWC_rev']

    def fcff(self, ebit: float, revenue: float) -> float:
        """
        Calculate free cash flow to firm, using average CapEx values
        to smoothen them
        """
        
        nopat = ebit + (1 - self.marignal_tax)
        da = revenue * self.da_ratio
        capex = revenue * self.capex_ratio
        fcff = nopat + da - capex
        
        return fcff
    
    def cash_flows(self) -> list[float]:
        pass
    
    def intrinsic_value(self) -> float:
        pass
    

if __name__ == '__main__':
    pass