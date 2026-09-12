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

# ============================ DCF calculation =========================
# Using Damodaran figures
TERMINAL_GROWTH = 0.025
FORECAST_HORIZON = 10
PHARMA_LTG_FALLBACK = 0.178
PHARMA_CAP = 0.4

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
        self.ltg = self._get_ltg()
        self.market_cap = row['market_cap']
        self.net_debt = row['total_debt'] - row['cash']
        self.n_analysts = row['n_analysts']
        self.wacc_computed = row['wacc_computed']
        self.marginal_tax = 0.35 if row['quarterdate'] < '2018-01-01' else 0.21

        self.da_ratio = row['smooth_da_ratio']
        self.capex_ratio = row['smooth_capex_ratio']

        self.delta_nwc = row['delta_NWC_rev']
    

    def _get_ltg(self) -> float:
        """
        Helper function to get the long term growth
        """
        
        if pd.notna(self.ltg) and self.ltg > 0:
            return min(self.ltg, PHARMA_CAP)
        if pd.notna(self.rev_fy1) and pd.notna(self.rev_fy2) and self.rev_fy1 > 0:
            return (self.rev_fy2 - self.rev_fy1) / self.rev_fy1
        
        return PHARMA_LTG_FALLBACK
    
    
    def fcff(self, ebit: float, revenue: float) -> float:
        """
        Calculate free cash flow to firm, using average CapEx values
        to smoothen them
        """
        
        nopat = ebit + (1 - self.marignal_tax)
        da = revenue * self.da_ratio
        capex = revenue * self.capex_ratio
        fcff = nopat + da - capex - self.delta_nwc
        
        return fcff
    
    
    def cash_flows(self, years: int=FORECAST_HORIZON) -> tuple[list[float], float, float]:
        """
        Projecting cashflows over the FORECAST_HORIZION, using the 
        analyst estimates. We have the first two years and extrapolate 
        from there. We get the growth rate by fading ltg linearly to
        terminal growth
        """
        
        flows = []

        flows.append(self.fcff(self.ebit_fy1, self.rev_fy1))
        flows.append(self.fcff(self.ebit_fy2, self.rev_fy2))

        rev3  = self.rev_fy2 * (1 + self.ltg)
        ebit3 = rev3 * self.ebit_margin
        flows.append(self.fcff(ebit3, rev3))

        rev_t  = rev3
        ebit_t = ebit3
        for t in range(4, years + 1):
            fade   = (t - 3) / (years - 3)  
            g_t    = self.ltg + fade * (TERMINAL_GROWTH - self.ltg)
            rev_t  = rev_t  * (1 + g_t)
            ebit_t = rev_t  * self.ebit_margin
            flows.append(self.fcff(ebit_t, rev_t))

        return flows, ebit_t, rev_t
    
    
    def terminal_value_calc(self, fcff_10: float) -> float:
        """
        Teriminal value
        """
        
        terminal_value = (fcff_10 * (1 + TERMINAL_GROWTH)) / (self.wacc_computed - TERMINAL_GROWTH)
        return terminal_value
    
    
    def intrinsic_value(self) -> float | None:
        """
        Calculate intrinsic value
        """
        
        flows = self.cash_flows()
        terminal_value = self.terminal_value_calc(flows[-1])
        
        pv_cashflows = 0.0
        for t, fcff in enumerate(flows):
            pv_cashflows += fcff / ((1 + self.wacc_computed) **(t + 1))

        pv_terminal_value = terminal_value / ((1 + self.wacc_computed) ** FORECAST_HORIZON)
        
        firm_value = pv_cashflows + pv_terminal_value
        equity_value = firm_value - self.net_debt
        
        if equity_value <= 0:
            return None
        
        return equity_value


if __name__ == '__main__':
    pass