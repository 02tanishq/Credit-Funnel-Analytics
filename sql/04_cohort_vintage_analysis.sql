-- ==============================================================================================
-- QUERY 04: Vintage / Cohort Analysis of Approved Loans by Origination Year
-- Business Question (Bajaj Finance / NBFC Context):
--   "How does cumulative credit risk (charge-off rate) mature across origination year cohorts over
--    loan lifetime, and how do unseasoned cohorts (2017-2018) distort top-line loss metrics due
--    to right-censoring? What is the true mature loss benchmark for credit underwriting?"
--
-- Technical Methodology:
--   - Implemented in PostgreSQL-compliant syntax using Common Table Expressions (CTEs)
--   - Uses window functions (LAG for YoY growth, SUM() OVER for cumulative portfolio metrics)
--   - Computes both 'Nominal Charge-Off Rate' (losses / total funded) and 'Resolved Default Rate'
--     (losses / (fully paid + charged off)) to isolate maturity lag from true credit performance.
-- ==============================================================================================

WITH cohort_base AS (
    SELECT 
        orig_year,
        total_funded_loans,
        total_funded_volume,
        fully_paid_count,
        current_count,
        late_count,
        charged_off_count,
        -- Resolved loans = contracts that have reached terminal state (no longer active)
        (fully_paid_count + charged_off_count) AS resolved_loans_count
    FROM mart_cohort_vintage
),
cohort_window_metrics AS (
    SELECT 
        orig_year,
        total_funded_loans,
        total_funded_volume,
        fully_paid_count,
        current_count,
        late_count,
        charged_off_count,
        resolved_loans_count,
        
        -- Nominal Charge-Off Rate (% of all loans issued)
        round(charged_off_count::DOUBLE / total_funded_loans, 4) AS nominal_charge_off_rate,
        
        -- Mature Resolved Default Rate (% of closed contracts, eliminating right-censoring)
        round(charged_off_count::DOUBLE / nullif(resolved_loans_count, 0), 4) AS resolved_default_rate,
        
        -- Portfolio Maturity Ratio (% of cohort loans that have closed)
        round(resolved_loans_count::DOUBLE / total_funded_loans, 4) AS cohort_maturity_ratio,

        -- Window Function 1: Year-over-Year Growth in Funded Volume
        round(
            (total_funded_volume - lag(total_funded_volume, 1) OVER (ORDER BY orig_year)) /
            nullif(lag(total_funded_volume, 1) OVER (ORDER BY orig_year), 0), 4
        ) AS yoy_volume_growth,

        -- Window Function 2: Cumulative Disbursed Capital to Date
        sum(total_funded_volume) OVER (ORDER BY orig_year ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total_disbursed,

        -- Window Function 3: Cumulative Write-offs Recognized to Date
        sum(charged_off_count) OVER (ORDER BY orig_year ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total_defaults
    FROM cohort_base
)
SELECT 
    orig_year,
    total_funded_loans,
    round(total_funded_volume / 1000000.0, 2) AS funded_volume_millions_usd,
    yoy_volume_growth,
    round(running_total_disbursed / 1000000.0, 2) AS cumulative_volume_millions_usd,
    fully_paid_count,
    current_count,
    late_count,
    charged_off_count,
    cohort_maturity_ratio,
    nominal_charge_off_rate,
    resolved_default_rate,
    CASE 
        WHEN cohort_maturity_ratio >= 0.95 THEN 'Mature Cohort (Terminal Performance)'
        WHEN cohort_maturity_ratio >= 0.50 THEN 'Maturing Cohort (Mid-Seasoning)'
        ELSE 'Immature Cohort (Severe Right-Censoring)'
    END AS cohort_classification
FROM cohort_window_metrics
ORDER BY orig_year;
