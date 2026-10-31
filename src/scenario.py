"""
Underwriting Product Recommendations & Sensitivity Scenario Engine
Simulates financial impacts (incremental volume, loan counts, expected credit losses)
for proposed credit policy changes under explicit sensitivity bounds.
"""

from typing import Dict, Any, List
import pandas as pd
import duckdb

PARQUET_PATH = "data/processed/common_applications.parquet"


def simulate_scenario_1_near_prime_expansion() -> pd.DataFrame:
    """
    Scenario 1: "Near-Prime Tiered DTI Expansion"
    Business Recommendation:
      Relax the strict 20% DTI knockout threshold to 28% specifically for established
      wage-earners (Employment Length >= 5 years) seeking debt consolidation.
      
    Target Segment:
      Applicants with DTI between 20% and 30%, Employment Length >= 5 years, currently rejected.
    """
    con = duckdb.connect()
    res = con.execute(f"""
        SELECT 
            count(*) AS target_pool_applicants,
            round(avg(loan_amount), 2) AS avg_ticket_size
        FROM read_parquet('{PARQUET_PATH}')
        WHERE dti_band = '20-30%'
          AND emp_length_band IN ('5-9 years', '10+ years')
          AND is_approved = 0;
    """).fetchone()
    con.close()

    target_pool = res[0]
    avg_ticket = res[1]

    # Sensitivity tiers:
    # Simulated approval rate: 18% of currently rejected borderline applicants qualify
    tiers = [
        {
            "tier": "Pessimistic (+35% Risk Surge)",
            "approval_rate": 0.18,
            "charge_off_rate": 0.189,  # 14.0% base * 1.35
            "rationale": "Adverse selection causes incremental defaults to surge 35% above prime cohort benchmark"
        },
        {
            "tier": "Base Case (Cohort Parity)",
            "approval_rate": 0.18,
            "charge_off_rate": 0.140,  # Matches mature 5+ year employed debt consolidation default rate
            "rationale": "Incremental borrowers default at exact historical rate of seasoned 5+ year employees"
        },
        {
            "tier": "Optimistic (-15% Risk Reduction)",
            "approval_rate": 0.18,
            "charge_off_rate": 0.119,  # 14.0% base * 0.85
            "rationale": "Ticket capping at $15k and automated mandate debits mitigate defaults by -15%"
        }
    ]

    records = []
    for t in tiers:
        inc_loans = round(target_pool * t["approval_rate"])
        inc_vol = round(inc_loans * avg_ticket, 2)
        exp_losses = round(inc_vol * t["charge_off_rate"], 2)
        records.append({
            "scenario": "Scenario 1: Near-Prime Tiered DTI Expansion",
            "sensitivity_tier": t["tier"],
            "target_applicant_pool": target_pool,
            "simulated_approval_rate": t["approval_rate"],
            "incremental_funded_loans": inc_loans,
            "avg_ticket_size_usd": avg_ticket,
            "incremental_funded_volume_usd": inc_vol,
            "expected_charge_off_rate": t["charge_off_rate"],
            "expected_credit_losses_usd": exp_losses,
            "assumptions_and_risks": t["rationale"]
        })

    return pd.DataFrame(records)


def simulate_scenario_2_small_business_tightening() -> pd.DataFrame:
    """
    Scenario 2: "Small Business / High-Ticket Risk Tightening"
    Business Recommendation:
      Unsecured Small Business loans > $25,000 exhibit high charge-off rates (>24.5%).
      Introduce strict ticket capping at $20,000 and require a minimum FICO of 720.
      
    Target Segment:
      Unsecured Small Business loans with ticket size > $25,000 currently approved.
    """
    con = duckdb.connect()
    res = con.execute(f"""
        SELECT 
            count(*) AS target_pool_applicants,
            round(avg(loan_amount), 2) AS avg_ticket_size
        FROM read_parquet('{PARQUET_PATH}')
        WHERE loan_purpose = 'small_business'
          AND loan_amount > 25000
          AND is_approved = 1;
    """).fetchone()
    con.close()

    target_pool = res[0]
    avg_ticket = res[1]

    # Sensitivity tiers for reduction in exposure
    tiers = [
        {
            "tier": "Pessimistic (Excess Churn / Lost Margin)",
            "volume_reduction_pct": -0.30,
            "avoided_charge_off_rate": 0.245,
            "rationale": "Underwriting friction spills over to prime borrowers, eroding fee and interest margin"
        },
        {
            "tier": "Base Case (Targeted Risk Pruning)",
            "volume_reduction_pct": -0.25,
            "avoided_charge_off_rate": 0.215,
            "rationale": "Avoided write-offs exceed lost fee income, expanding portfolio Net Interest Margin (NIM)"
        },
        {
            "tier": "Optimistic (Capital Re-allocation)",
            "volume_reduction_pct": -0.20,
            "avoided_charge_off_rate": 0.180,
            "rationale": "Preserved capital reallocated to high-tenure consumer debt consolidation at superior RAROC"
        }
    ]

    records = []
    for t in tiers:
        chg_loans = round(target_pool * t["volume_reduction_pct"])
        chg_vol = round(chg_loans * avg_ticket, 2)
        # Avoided loss is positive capital preserved
        avoided_losses = round(abs(chg_vol) * t["avoided_charge_off_rate"], 2)
        records.append({
            "scenario": "Scenario 2: Small Business Risk Tightening",
            "sensitivity_tier": t["tier"],
            "target_applicant_pool": target_pool,
            "simulated_approval_rate": t["volume_reduction_pct"],
            "incremental_funded_loans": chg_loans,
            "avg_ticket_size_usd": avg_ticket,
            "incremental_funded_volume_usd": chg_vol,
            "expected_charge_off_rate": t["avoided_charge_off_rate"],
            "expected_credit_losses_usd": avoided_losses,
            "assumptions_and_risks": t["rationale"]
        })

    return pd.DataFrame(records)


def run_all_scenarios() -> pd.DataFrame:
    """Run both policy scenarios and return combined summary dataframe."""
    df1 = simulate_scenario_1_near_prime_expansion()
    df2 = simulate_scenario_2_small_business_tightening()
    return pd.concat([df1, df2], ignore_index=True)


if __name__ == "__main__":
    df = run_all_scenarios()
    print("Underwriting Policy Sensitivity Scenarios:")
    print(df[['scenario', 'sensitivity_tier', 'incremental_funded_loans', 'incremental_funded_volume_usd', 'expected_charge_off_rate', 'expected_credit_losses_usd']].to_string(index=False))
