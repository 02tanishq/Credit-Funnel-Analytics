-- ==============================================================================================
-- QUERY 03: Observable Approval Drivers & Selection Bias Audit
-- Business Question (Bajaj Finance / NBFC Context):
--   "Which observable applicant attributes (Credit Score proxy, DTI, Ticket Size, Employment Tenure)
--    have the highest empirical odds of clearing the underwriting policy gate, and where does
--    unobserved data introduce selection bias into our funnel analytics?"
--
-- Institutional Context & Selection Bias Audit:
--   1. 66.9% of rejected applicants (18.5M rows) lack a risk score because Lending Club applied
--      hard knockout criteria (unserviceable DTI, zero self-reported income, unsupported geography)
--      before paying bureau API fees to pull a FICO credit score.
--   2. DTI of '-1%' in rejected applications encodes missing/uncomputable income.
--   3. Interpretable odds ratios require separating applicants with credit bureau records from
--      thin-file applicants rejected at pre-qualification.
-- ==============================================================================================

-- Part A: Empirical Approval Rates and Log-Odds by Risk Score Decile
WITH scored_applicants AS (
    SELECT 
        application_id,
        risk_score,
        is_approved,
        CASE
            WHEN risk_score < 600 THEN '1. Subprime (<600)'
            WHEN risk_score < 640 THEN '2. Poor (600-639)'
            WHEN risk_score < 680 THEN '3. Fair (640-679)'
            WHEN risk_score < 720 THEN '4. Good (680-719)'
            WHEN risk_score < 760 THEN '5. Very Good (720-759)'
            ELSE '6. Excellent (760+)'
        END AS credit_tier
    FROM common_applications
    WHERE has_risk_score = 1
),
tier_stats AS (
    SELECT 
        credit_tier,
        count(*) AS total_scored_applicants,
        count(CASE WHEN is_approved = 1 THEN 1 END) AS approved_count,
        count(CASE WHEN is_approved = 0 THEN 1 END) AS rejected_count,
        round(count(CASE WHEN is_approved = 1 THEN 1 END)::DOUBLE / count(*), 4) AS approval_rate
    FROM scored_applicants
    GROUP BY credit_tier
)
SELECT 
    credit_tier,
    total_scored_applicants,
    approved_count,
    rejected_count,
    approval_rate,
    -- Empirical Odds = Approved / Rejected
    round(approved_count::DOUBLE / nullif(rejected_count, 0), 4) AS empirical_odds,
    -- Empirical Log-Odds
    round(ln(nullif(approved_count::DOUBLE / nullif(rejected_count, 0), 0)), 4) AS log_odds
FROM tier_stats
ORDER BY credit_tier;


-- Part B: Selection Bias Audit - Missingness of Bureau Risk Score vs Approval
SELECT 
    CASE WHEN has_risk_score = 1 THEN 'Bureau Score Pulled (Non-Null)' ELSE 'Pre-Screen Knockout (Null Score)' END AS bureau_pull_status,
    count(*) AS total_applicants,
    count(CASE WHEN is_approved = 1 THEN 1 END) AS approved_count,
    count(CASE WHEN is_approved = 0 THEN 1 END) AS rejected_count,
    round(count(CASE WHEN is_approved = 1 THEN 1 END)::DOUBLE / count(*), 4) AS approval_rate
FROM common_applications
GROUP BY has_risk_score
ORDER BY has_risk_score DESC;


-- Part C: Interaction of DTI and Employment Tenure on Approval Odds
SELECT 
    dti_band,
    emp_length_band,
    count(*) AS total_applicants,
    count(CASE WHEN is_approved = 1 THEN 1 END) AS approved_count,
    round(count(CASE WHEN is_approved = 1 THEN 1 END)::DOUBLE / count(*), 4) AS approval_rate
FROM common_applications
WHERE dti_band IN ('0-10%', '10-20%', '20-30%', '30-40%')
  AND emp_length_band IN ('< 1 year', '1-4 years', '5-9 years', '10+ years')
GROUP BY dti_band, emp_length_band
ORDER BY dti_band, approval_rate DESC;
