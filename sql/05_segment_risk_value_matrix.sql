-- ==============================================================================================
-- QUERY 05: Segment Value Matrix (Approval Rate vs Realized Default Rate)
-- Business Question (Bajaj Finance / NBFC Context):
--   "Which segments represent growth opportunities (high rejection, low realized charge-off) versus
--    danger zones (high approval, high realized charge-off) for underwriting policy revision?
--    How can we reallocate credit bandwidth to maximize risk-adjusted return on capital (RAROC)?"
--
-- Strategic Matrix Definitions:
--   Benchmark Approval Rate = ~7.56% (Portfolio Average)
--   Benchmark Default Rate  = ~11.92% (Nominal) / ~19.97% (Terminal Resolved)
--
--   - Quadrant I   (High Approval, Low Default):   Prime Core Assets (Protect & Maintain)
--   - Quadrant II  (Low Approval, Low Default):    GROWTH GOLDMINE (High Rejection, Superior Credit Quality)
--   - Quadrant III (Low Approval, High Default):   Subprime Filter (Correctly Filtered Out)
--   - Quadrant IV  (High Approval, High Default):  LEAKAGE DANGER ZONE (Excessive Risk, Tighten Sanctions)
-- ==============================================================================================

WITH segment_performance AS (
    SELECT 
        loan_purpose,
        amount_band,
        dti_band,
        count(*) AS total_applied,
        count(CASE WHEN is_approved = 1 THEN 1 END) AS approved_count,
        round(count(CASE WHEN is_approved = 1 THEN 1 END)::DOUBLE / count(*), 4) AS approval_rate,
        count(CASE WHEN outcome_bucket = 'Charged Off' THEN 1 END) AS charged_off_count,
        count(CASE WHEN outcome_bucket IN ('Fully Paid', 'Charged Off') THEN 1 END) AS resolved_count,
        -- Terminal Charge-Off Rate among resolved loans
        round(
            count(CASE WHEN outcome_bucket = 'Charged Off' THEN 1 END)::DOUBLE / 
            nullif(count(CASE WHEN outcome_bucket IN ('Fully Paid', 'Charged Off') THEN 1 END), 0), 4
        ) AS terminal_charge_off_rate
    FROM common_applications
    GROUP BY loan_purpose, amount_band, dti_band
    -- Ensure statistical validity by restricting to segments with at least 500 applications and 50 resolved loans
    HAVING count(*) >= 500 
       AND count(CASE WHEN outcome_bucket IN ('Fully Paid', 'Charged Off') THEN 1 END) >= 50
),
quadrant_classification AS (
    SELECT 
        loan_purpose,
        amount_band,
        dti_band,
        total_applied,
        approved_count,
        approval_rate,
        charged_off_count,
        resolved_count,
        terminal_charge_off_rate,
        CASE
            WHEN approval_rate >= 0.08 AND terminal_charge_off_rate < 0.20 THEN 'Quadrant I: Prime Core (High Approval, Low Default)'
            WHEN approval_rate < 0.08 AND terminal_charge_off_rate < 0.18 THEN 'Quadrant II: Growth Goldmine (High Rejection, Low Default)'
            WHEN approval_rate < 0.08 AND terminal_charge_off_rate >= 0.22 THEN 'Quadrant III: Subprime Gate (Appropriate High Rejection)'
            WHEN approval_rate >= 0.08 AND terminal_charge_off_rate >= 0.22 THEN 'Quadrant IV: Leakage Risk (High Approval, High Default)'
            ELSE 'Neutral / Average Performance'
        END AS strategic_quadrant
    FROM segment_performance
)
SELECT 
    strategic_quadrant,
    loan_purpose,
    amount_band,
    dti_band,
    total_applied,
    approved_count,
    approval_rate,
    resolved_count,
    charged_off_count,
    terminal_charge_off_rate,
    -- Rank within quadrant by volume of applicants
    rank() OVER (PARTITION BY strategic_quadrant ORDER BY total_applied DESC) AS quadrant_volume_rank
FROM quadrant_classification
ORDER BY strategic_quadrant, total_applied DESC;
