""""
Full DCF

VE = ln(MarketCap / IntrinsicValue)

- VE = 0: market price equals your DCF intrinsic value exactly
- VE > 0: market is overvalued relative to your model; market cap exceeds intrinsic value. 
- VE < 0: market is undervalued; intrinsic value exceeds market cap. 
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
                pr.smooth_rd_ratio,
                pr.smooth_rd_amort_ratio,
                pr.delta_nwc_rev,
                pr.smooth_delta_nwc_ratio,
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
PHARMA_LTG_FALLBACK = 0.06 #Long run Pharma revenue growth rate, find citation
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
        self.rev_fy1 = row['rev_mean_fy1']
        self.rev_fy2 = row['rev_mean_fy2']
        self.ebit_margin = row['adj_ebit_margin']
        self.ltg_mean = row['ltg_mean']
        self.ltg = self._get_ltg()
        self.market_cap = row['market_cap']
        total_debt = 0.0 if pd.isna(row['total_debt']) else row['total_debt']
        cash = 0.0 if pd.isna(row['cash']) else row['cash']
        self.net_debt = total_debt - cash
        self.n_analysts = row['n_analysts']
        self.wacc_computed = row['wacc_computed']
        self.marginal_tax = 0.35 if row['quarter_date'] < pd.Timestamp('2018-01-01') else 0.21

        self.da_ratio = 0.0 if pd.isna(row['smooth_da_ratio']) else row['smooth_da_ratio']
        self.capex_ratio = 0.0 if pd.isna(row['smooth_capex_ratio']) else row['smooth_capex_ratio']
        self.rd_ratio = 0.0 if pd.isna(row['smooth_rd_ratio']) else row['smooth_rd_ratio']
        self.rd_amort_ratio = 0.0 if pd.isna(row['smooth_rd_amort_ratio']) else row['smooth_rd_amort_ratio']

        self.delta_nwc = 0.0 if pd.isna(row['delta_nwc_rev']) else row['delta_nwc_rev']
        # self.smooth_delta_nwc = row['smooth_delta_nwc_ratio']
    

    def _get_ltg(self) -> float:
        """
        Helper function to get the long term growth
        """
        
        if pd.notna(self.ltg_mean) and self.ltg_mean > 0:
            return min(self.ltg_mean / 100, PHARMA_CAP)
        if pd.notna(self.rev_fy1) and pd.notna(self.rev_fy2) and self.rev_fy1 > 0:
            return (self.rev_fy2 - self.rev_fy1) / self.rev_fy1
        
        return PHARMA_LTG_FALLBACK
    
    
    def fcff(self, ebit: float, revenue: float) -> float:
        """
        Calculate free cash flow to firm, using average CapEx values
        to smoothen them
        """
        
        nopat = ebit * (1 - self.marginal_tax)
        da = revenue * self.da_ratio
        capex = revenue * self.capex_ratio
        fcff = nopat + da - capex - (revenue * self.delta_nwc)
        
        return fcff
    
    
    def cash_flows(self, years: int=FORECAST_HORIZON) -> tuple[list[float], float, float]:
        """
        Projecting cashflows over the FORECAST_HORIZION, using the 
        analyst estimates. We have the first two years and extrapolate 
        from there. We get the growth rate by fading ltg linearly to
        terminal growth
        """
        
        flows = []
        
        adj_ebit_fy1 = self.ebit_fy1 + self.rev_fy1 * (self.rd_ratio - self.rd_amort_ratio)
        adj_ebit_fy2 = self.ebit_fy2 + self.rev_fy2 * (self.rd_ratio - self.rd_amort_ratio)

        flows.append(self.fcff(adj_ebit_fy1, self.rev_fy1))
        flows.append(self.fcff(adj_ebit_fy2, self.rev_fy2))

        rev_fy3  = self.rev_fy2 * (1 + self.ltg)
        if pd.notna(self.ebit_fy2) and pd.notna(self.rev_fy2) and self.rev_fy2 > 0:
            margin = (self.ebit_fy2 + self.rev_fy2 * (self.rd_ratio - self.rd_amort_ratio)) / self.rev_fy2
        else:
            margin = self.ebit_margin
        
        ebit3 = rev_fy3 * margin
        flows.append(self.fcff(ebit3, rev_fy3))

        rev_t  = rev_fy3
        ebit_t = ebit3
        for t in range(4, years + 1):
            fade = (t - 3) / (years - 3)  
            g_t = self.ltg + fade * (TERMINAL_GROWTH - self.ltg)
            rev_t = rev_t * (1 + g_t)
            ebit_t = rev_t * margin
            flows.append(self.fcff(ebit_t, rev_t))

        return flows, ebit_t, rev_t
    
    
    def terminal_value_calc(self, fcff_10: float) -> float:
        """
        Teriminal value
        """
        
        terminal_value = (fcff_10 * (1 + TERMINAL_GROWTH)) / (self.wacc_computed - TERMINAL_GROWTH)
        return terminal_value
    
    
    def intrinsic_value_calc(self) -> float | None:
        """
        Calculate intrinsic value
        """
        
        if self.wacc_computed <= TERMINAL_GROWTH:
            return None
        
        flows, _, _ = self.cash_flows()
        terminal_value = self.terminal_value_calc(flows[-1])
        
        pv_cashflows = 0.0
        for t, fcff in enumerate(flows):
            pv_cashflows += fcff / ((1 + self.wacc_computed) ** (t + 1))

        pv_terminal_value = terminal_value / ((1 + self.wacc_computed) ** FORECAST_HORIZON)
        
        firm_value = pv_cashflows + pv_terminal_value
        equity_value = firm_value - self.net_debt
        
        if pd.isna(firm_value) or firm_value <= 0:
            return None
        
        return equity_value, firm_value
    
# ================================ Running the DCF ===========================

if __name__ == '__main__':
    
    df_panel = load_panel()
    df_filter = df_panel[df_panel['n_analysts'] >= 3].copy()
    
    results = []
    
    for _, row in df_filter.iterrows():
        dcf = DCF(row)
        result = dcf.intrinsic_value_calc()

        if result is None:
            continue

        intrinsic_value_equity, intrinsic_value_firm = result
        net_debt = dcf.net_debt
        
        ev_market = row['market_cap'] + net_debt
        ve_equity = np.log(row['market_cap'] / intrinsic_value_equity) if intrinsic_value_equity > 0 else np.nan
        ve_firm = np.log(ev_market / intrinsic_value_firm) if (intrinsic_value_firm > 0 and ev_market > 0) else np.nan
        
        results.append({
            'Instrument': row['Instrument'],
            'quarter_date': row['quarter_date'],
            'intrinsic_value_equity': intrinsic_value_equity,
            'intrinsic_value_firm': intrinsic_value_firm,
            'market_cap': row['market_cap'],
            'valuation_error_equity': ve_equity,
            'valuation_error_firm':ve_firm
        })
        
    df_valuation_error = pd.DataFrame(results)
        
    firm_counts = df_valuation_error.groupby('Instrument')['quarter_date'].count()
    firms_keep = firm_counts[firm_counts >= 6].index
    df_ve_clean = df_valuation_error[df_valuation_error['Instrument'].isin(firms_keep)]
    
    with duckdb.connect(DB_PATH) as con:
        con.execute('DROP TABLE IF EXISTS valuation_errors')
        con.register('df_ve_clean', df_ve_clean)
        con.execute('CREATE TABLE valuation_errors AS SELECT * FROM df_ve_clean')
    
    print(f"Valuations computed: {len(df_ve_clean)} rows, {df_ve_clean['Instrument'].nunique()} firms")
        
        