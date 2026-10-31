-- ==============================================================================================
-- QUERY 02: Segment Drop-offs & Wilson Score 95% Confidence Intervals
-- Business Question (Bajaj Finance / NBFC Context):
--   "Where are the steepest drop-offs in the acquisition funnel, which customer segments deviate
--    most from portfolio benchmark, and are these differences statistically sound? 
--    (Reporting counts next to every rate, with 95% Wilson Score Confidence Intervals)."
--
-- Statistical Methodology:
--   Wilson Score interval is used instead of normal approximation (Wald) to guarantee bounds
--   remain strictly in [0, 1] without distortion for extreme segment sizes or conversion rates.
--   Confidence level = 95% (z = 1.959964, z^2 = 3.841459).
-- ==============================================================================================

WITH segment_metrics AS (
    SELECT 
        'DTI Band' AS segment_type,
        dti_band AS segment_name,
        count(*) AS total_applied,
        count(CASE WHEN is_approved = 1 THEN 1 END) AS approved_count,
        count(CASE WHEN is_approved = 0 THEN 1 END) AS rejected_count
    FROM common_applications
    GROUP BY dti_band
    
    UNION ALL
    
    SELECT 
        'Employment Length' AS segment_type,
        emp_length_band AS segment_name,
        count(*) AS total_applied,
        count(CASE WHEN is_approved = 1 THEN 1 END) AS approved_count,
        count(CASE WHEN is_approved = 0 THEN 1 END) AS rejected_count
    FROM common_applications
    GROUP BY emp_length_band

    UNION ALL

    SELECT 
        'Ticket Size Band' AS segment_type,
        amount_band AS segment_name,
        count(*) AS total_applied,
        count(CASE WHEN is_approved = 1 THEN 1 END) AS approved_count,
        count(CASE WHEN is_approved = 0 THEN 1 END) AS rejected_count
    FROM common_applications
    GROUP BY amount_band

    UNION ALL

    SELECT 
        'Loan Purpose' AS segment_type,
        loan_purpose AS segment_name,
        count(*) AS total_applied,
        count(CASE WHEN is_approved = 1 THEN 1 END) AS approved_count,
        count(CASE WHEN is_approved = 0 THEN 1 END) AS rejected_count
    FROM common_applications
    GROUP BY loan_purpose
),
wilson_ci AS (
    SELECT 
        segment_type,
        segment_name,
        total_applied,
        approved_count,
        rejected_count,
        round(rejected_count::DOUBLE / total_applied, 4) AS dropoff_rate,
        round(approved_count::DOUBLE / total_applied, 4) AS approval_rate,
        -- Wilson Score Interval calculations
        -- p_hat = approved_count / total_applied
        -- Denominator = 1 + z^2 / n
        (1.0 + 3.841459 / total_applied) AS denom,
        -- Center adjusted = (p_hat + z^2 / (2n)) / denom
        ((approved_count::DOUBLE / total_applied) + (1.920729 / total_applied)) / (1.0 + 3.841459 / total_applied) AS center_adj,
        -- Margin of error
        (1.959964 / (1.0 + 3.841459 / total_applied)) * 
        sqrt(
            (((approved_count::DOUBLE / total_applied) * (1.0 - (approved_count::DOUBLE / total_applied))) / total_applied) +
            (3.841459 / (4.0 * total_applied * total_applied))
        ) AS margin_err
    FROM segment_metrics
    WHERE total_applied > 0
)
SELECT 
    segment_type,
    segment_name,
    total_applied AS total_applicants,
    approved_count AS approved_and_funded,
    rejected_count AS dropped_off_applicants,
    dropoff_rate,
    approval_rate,
    round(greatest(0.0, center_adj - margin_err), 4) AS approval_ci_lower_95,
    round(least(1.0, center_adj + margin_err), 4) AS approval_ci_upper_95,
    round((approval_rate - 0.0756), 4) AS diff_from_portfolio_avg
FROM wilson_ci
ORDER BY segment_type, dropoff_rate DESC;
