"""
Row Count Reconciliation Test Suite
Rigorous audit verifying that every raw row is accounted for, trailing null rows are
explicitly logged and dropped, and stage sums reconcile exactly without discrepancy.
"""

import pytest
import duckdb
import pandas as pd

PARQUET_PATH = "data/processed/common_applications.parquet"
MARTS_DIR = "data/marts"


@pytest.fixture(scope="session")
def duck_conn():
    con = duckdb.connect()
    yield con
    con.close()


def test_row_count_reconciliation_total(duck_conn):
    """
    Verify exact total count matches 29,909,409:
    Raw accepted (2,260,701) - 33 null rows = 2,260,668
    Raw rejected (27,648,741) = 27,648,741
    Total = 29,909,409
    """
    res = duck_conn.execute(f"""
        SELECT 
            count(*) AS total_rows,
            count(CASE WHEN is_approved = 1 THEN 1 END) AS accepted_rows,
            count(CASE WHEN is_approved = 0 THEN 1 END) AS rejected_rows
        FROM read_parquet('{PARQUET_PATH}')
    """).fetchone()

    total_rows, accepted_rows, rejected_rows = res

    assert accepted_rows == 2260668, f"Accepted row count {accepted_rows} != 2,260,668"
    assert rejected_rows == 27648741, f"Rejected row count {rejected_rows} != 27,648,741"
    assert total_rows == 29909409, f"Total row count {total_rows} != 29,909,409"
    assert (accepted_rows + rejected_rows) == total_rows


def test_stage_outcome_breakdown_reconciled(duck_conn):
    """Verify sum of Stage 3 portfolio outcomes equals total Stage 2 funded loans."""
    res = duck_conn.execute(f"""
        SELECT 
            outcome_bucket,
            count(*) AS cnt
        FROM read_parquet('{PARQUET_PATH}')
        WHERE is_approved = 1
        GROUP BY outcome_bucket
    """).fetchall()

    outcome_dict = {r[0]: r[1] for r in res}
    total_outcomes = sum(outcome_dict.values())

    assert total_outcomes == 2260668, f"Stage 3 total {total_outcomes} != 2,260,668"
    assert outcome_dict["Fully Paid"] == 1078739, f"Fully Paid count mismatch: {outcome_dict.get('Fully Paid')}"
    assert outcome_dict["Current"] == 886753, f"Current count mismatch: {outcome_dict.get('Current')}"
    assert outcome_dict["Late"] == 25816, f"Late count mismatch: {outcome_dict.get('Late')}"
    assert outcome_dict["Charged Off"] == 269360, f"Charged Off count mismatch: {outcome_dict.get('Charged Off')}"


def test_marts_reconcile_with_parquet():
    """Verify exported CSV marts reconcile with underlying Parquet totals."""
    # 1. Funnel summary mart
    df_funnel = pd.read_csv(f"{MARTS_DIR}/mart_funnel_summary.csv")
    applied_cnt = df_funnel.loc[df_funnel['stage_name'] == 'Stage 1: Applied', 'applicant_count'].values[0]
    funded_cnt = df_funnel.loc[df_funnel['stage_name'] == 'Stage 2: Approved and Funded', 'applicant_count'].values[0]
    
    assert applied_cnt == 29909409
    assert funded_cnt == 2260668

    # 2. Cohort vintage mart
    df_cohort = pd.read_csv(f"{MARTS_DIR}/mart_cohort_vintage.csv")
    assert df_cohort['total_funded_loans'].sum() == 2260668
    assert df_cohort['charged_off_count'].sum() == 269360
    assert df_cohort['fully_paid_count'].sum() == 1078739
    assert len(df_cohort) == 12  # Years 2007 to 2018
