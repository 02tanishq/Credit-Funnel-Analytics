-- ==============================================================================================
-- QUERY 01: Overall & Segmented Funnel Stage Conversion Rates
-- Business Question (Bajaj Finance / NBFC Context):
--   "What is the overall funnel conversion efficiency across stages (Applied -> Approved/Funded -> Outcome),
--    and how does conversion vary across key macro dimensions (Origination Year, Geography, Loan Purpose,
--    Ticket Size, DTI, Employment Tenure)? Where are the primary conversion bottlenecks?"
--
-- Funnel Boundary Disclaimer:
--   Stage 2 represents "Approved and Funded". In Lending Club public data, approved applicants who declined
--   the loan offer (offer fallout) are not captured, and thus Stage 2 conversion measures effective disbursal rate.
-- ==============================================================================================

-- Part A: Overall Funnel Summary (Total Inflow -> Funded Disbursal -> Portfolio Resolution)
WITH total_applied AS (
    SELECT count(*) AS total_inflow
    FROM common_applications
),
stage_counts AS (
    SELECT 
        count(*) AS total_applied,
        count(CASE WHEN is_approved = 1 THEN 1 END) AS approved_funded_count,
        count(CASE WHEN outcome_bucket = 'Fully Paid' THEN 1 END) AS fully_paid_count,
        count(CASE WHEN outcome_bucket = 'Current' THEN 1 END) AS current_count,
        count(CASE WHEN outcome_bucket = 'Late' THEN 1 END) AS late_count,
        count(CASE WHEN outcome_bucket = 'Charged Off' THEN 1 END) AS charged_off_count
    FROM common_applications
)
SELECT 
    'Stage 1: Applied (Total Inflow)' AS funnel_stage,
    total_applied AS applicants,
    1.0000 AS stage_conversion_rate,
    1.0000 AS cumulative_conversion_rate
FROM stage_counts
UNION ALL
SELECT 
    'Stage 2: Approved and Funded' AS funnel_stage,
    approved_funded_count AS applicants,
    round(approved_funded_count::DOUBLE / total_applied, 4) AS stage_conversion_rate,
    round(approved_funded_count::DOUBLE / total_applied, 4) AS cumulative_conversion_rate
FROM stage_counts
UNION ALL
SELECT 
    'Stage 3a: Fully Paid (Resolved Healthy)' AS funnel_stage,
    fully_paid_count AS applicants,
    round(fully_paid_count::DOUBLE / approved_funded_count, 4) AS stage_conversion_rate,
    round(fully_paid_count::DOUBLE / total_applied, 4) AS cumulative_conversion_rate
FROM stage_counts
UNION ALL
SELECT 
    'Stage 3b: Current (Active Performing)' AS funnel_stage,
    current_count AS applicants,
    round(current_count::DOUBLE / approved_funded_count, 4) AS stage_conversion_rate,
    round(current_count::DOUBLE / total_applied, 4) AS cumulative_conversion_rate
FROM stage_counts
UNION ALL
SELECT 
    'Stage 3c: Late / Delinquent (PAR 15-120)' AS funnel_stage,
    late_count AS applicants,
    round(late_count::DOUBLE / approved_funded_count, 4) AS stage_conversion_rate,
    round(late_count::DOUBLE / total_applied, 4) AS cumulative_conversion_rate
FROM stage_counts
UNION ALL
SELECT 
    'Stage 3d: Charged Off (Default / Loss)' AS funnel_stage,
    charged_off_count AS applicants,
    round(charged_off_count::DOUBLE / approved_funded_count, 4) AS stage_conversion_rate,
    round(charged_off_count::DOUBLE / total_applied, 4) AS cumulative_conversion_rate
FROM stage_counts;


-- Part B: Conversion Rates By Origination Year (Tracking Macro Underwriting Shifts 2007-2018)
SELECT 
    application_year,
    count(*) AS total_applied,
    count(CASE WHEN is_approved = 1 THEN 1 END) AS approved_funded,
    round(count(CASE WHEN is_approved = 1 THEN 1 END)::DOUBLE / count(*), 4) AS approval_rate,
    count(CASE WHEN outcome_bucket = 'Charged Off' THEN 1 END) AS charged_off_count,
    round(count(CASE WHEN outcome_bucket = 'Charged Off' THEN 1 END)::DOUBLE / 
          nullif(count(CASE WHEN is_approved = 1 THEN 1 END), 0), 4) AS charge_off_rate_of_funded
FROM common_applications
GROUP BY application_year
ORDER BY application_year;


-- Part C: Conversion Rates By Ticket Size (Loan Amount Band)
SELECT 
    amount_band,
    count(*) AS total_applied,
    count(CASE WHEN is_approved = 1 THEN 1 END) AS approved_funded,
    round(count(CASE WHEN is_approved = 1 THEN 1 END)::DOUBLE / count(*), 4) AS approval_rate
FROM common_applications
GROUP BY amount_band
ORDER BY approval_rate DESC;


-- Part D: Conversion Rates By Debt-To-Income (DTI) Band
SELECT 
    dti_band,
    count(*) AS total_applied,
    count(CASE WHEN is_approved = 1 THEN 1 END) AS approved_funded,
    round(count(CASE WHEN is_approved = 1 THEN 1 END)::DOUBLE / count(*), 4) AS approval_rate
FROM common_applications
GROUP BY dti_band
ORDER BY approval_rate DESC;


-- Part E: Conversion Rates By Employment Length Band
SELECT 
    emp_length_band,
    count(*) AS total_applied,
    count(CASE WHEN is_approved = 1 THEN 1 END) AS approved_funded,
    round(count(CASE WHEN is_approved = 1 THEN 1 END)::DOUBLE / count(*), 4) AS approval_rate
FROM common_applications
GROUP BY emp_length_band
ORDER BY approval_rate DESC;
