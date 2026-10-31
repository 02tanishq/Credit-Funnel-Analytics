-- ==============================================================================================
-- QUERY 06: Product Policy Scenarios & Sensitivity Simulations
-- Business Question (Bajaj Finance / NBFC Context):
--   "What is the projected portfolio impact (incremental funded contracts, disbursed volume,
--    and expected write-off ranges) of modifying underwriting thresholds for target segments?
--    How do financial outcomes fluctuate across Pessimistic, Base Case, and Optimistic sensitivity bands?"
--
-- Institutional Disclaimer:
--   These models represent SCENARIO ESTIMATES WITH SENSITIVITY RANGES, NOT DETERMINISTIC PREDICTIONS.
--   Credit outcomes depend on macroeconomic stability, collections operational efficiency, and
--   borrower take-up rates.
-- ==============================================================================================

-- Scenario 1: Near-Prime Tiered DTI Expansion
-- Target Segment: Applicants with DTI 20-30% and Employment Length >= 5 years
-- Underwriting Intervention: Relax blunt DTI knockout gate from 20% to 28% for established wage earners.
WITH scenario1_pool AS (
    SELECT 
        count(*) AS target_pool_applicants,
        avg(loan_amount) AS avg_ticket_size
    FROM common_applications
    WHERE dti_band = '20-30%'
      AND emp_length_band IN ('5-9 years', '10+ years')
      AND is_approved = 0
),
scenario1_sensitivity AS (
    SELECT 
        'Scenario 1: Near-Prime Tiered DTI Bridge (DTI 20-30%, Emp 5+ yrs)' AS scenario_name,
        'Pessimistic (+35% Default Surge)' AS sensitivity_tier,
        target_pool_applicants,
        0.18 AS simulated_approval_rate,
        round(target_pool_applicants * 0.18) AS incremental_funded_loans,
        round(target_pool_applicants * 0.18 * avg_ticket_size, 2) AS incremental_funded_volume_usd,
        0.189 AS expected_charge_off_rate,
        round(target_pool_applicants * 0.18 * avg_ticket_size * 0.189, 2) AS expected_credit_losses_usd,
        'Adverse selection causes incremental defaults to surge 35% above prime benchmark' AS risk_rationale
    FROM scenario1_pool
    
    UNION ALL
    
    SELECT 
        'Scenario 1: Near-Prime Tiered DTI Bridge (DTI 20-30%, Emp 5+ yrs)',
        'Base Case (Cohort Parity)',
        target_pool_applicants,
        0.18,
        round(target_pool_applicants * 0.18),
        round(target_pool_applicants * 0.18 * avg_ticket_size, 2),
        0.140,
        round(target_pool_applicants * 0.18 * avg_ticket_size * 0.140, 2),
        'Incremental borrowers default at exact historical rate of seasoned 5+ year employees'
    FROM scenario1_pool

    UNION ALL

    SELECT 
        'Scenario 1: Near-Prime Tiered DTI Bridge (DTI 20-30%, Emp 5+ yrs)',
        'Optimistic (-15% Default Reduction)',
        target_pool_applicants,
        0.18,
        round(target_pool_applicants * 0.18),
        round(target_pool_applicants * 0.18 * avg_ticket_size, 2),
        0.119,
        round(target_pool_applicants * 0.18 * avg_ticket_size * 0.119, 2),
        'Targeted ticket sizing capped at $15k and automated mandate debits mitigate defaults'
    FROM scenario1_pool
),

-- Scenario 2: Small Business / High-Ticket Risk Tightening
-- Target Segment: Unsecured Small Business Loans > $25,000
-- Underwriting Intervention: Implement strict FICO cutoff (720+) and cap unsecured exposure at $20k.
scenario2_pool AS (
    SELECT 
        count(*) AS target_pool_applicants,
        avg(loan_amount) AS avg_ticket_size
    FROM common_applications
    WHERE loan_purpose = 'small_business'
      AND loan_amount > 25000
      AND is_approved = 1
),
scenario2_sensitivity AS (
    SELECT 
        'Scenario 2: Small Business / High-Ticket Risk Tightening (> $25k Ticket)' AS scenario_name,
        'Pessimistic (Excess Churn / Lost Margin)' AS sensitivity_tier,
        target_pool_applicants,
        -0.30 AS simulated_volume_reduction_pct,
        round(target_pool_applicants * -0.30) AS reduced_funded_loans,
        round(target_pool_applicants * -0.30 * avg_ticket_size, 2) AS reduced_origination_volume_usd,
        0.245 AS avoided_charge_off_rate,
        round(target_pool_applicants * 0.30 * avg_ticket_size * 0.245, 2) AS avoided_credit_losses_usd,
        'High customer drop-off spills into prime borrowers, eroding fee and interest margin' AS risk_rationale
    FROM scenario2_pool

    UNION ALL

    SELECT 
        'Scenario 2: Small Business / High-Ticket Risk Tightening (> $25k Ticket)',
        'Base Case (Targeted Risk Pruning)',
        target_pool_applicants,
        -0.25,
        round(target_pool_applicants * -0.25),
        round(target_pool_applicants * -0.25 * avg_ticket_size, 2),
        0.215,
        round(target_pool_applicants * 0.25 * avg_ticket_size * 0.215, 2),
        'Capital preserved from avoided write-offs exceeds lost fee income, expanding net margin'
    FROM scenario2_pool

    UNION ALL

    SELECT 
        'Scenario 2: Small Business / High-Ticket Risk Tightening (> $25k Ticket)',
        'Optimistic (Reallocated Capital into Consumer Prime)',
        target_pool_applicants,
        -0.20,
        round(target_pool_applicants * -0.20),
        round(target_pool_applicants * -0.20 * avg_ticket_size, 2),
        0.180,
        round(target_pool_applicants * 0.20 * avg_ticket_size * 0.180, 2),
        'Preserved capital re-routed to 10+ year employee debt consolidation at superior RAROC'
    FROM scenario2_pool
)
SELECT * FROM scenario1_sensitivity
UNION ALL
SELECT * FROM scenario2_sensitivity;
