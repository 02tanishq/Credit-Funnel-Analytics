"""
Data Quality Test Suite
Validates schema integrity, null constraints, duplicate primary keys,
date ranges, value bounds, and statistical property invariants.
"""

import pytest
import duckdb
import numpy as np
import pandas as pd
from src.stats import wilson_score_interval, two_proportion_z_test

PARQUET_PATH = "data/processed/common_applications.parquet"


@pytest.fixture(scope="session")
def duck_conn():
    """Shared DuckDB connection fixture querying the canonical Parquet table."""
    con = duckdb.connect()
    yield con
    con.close()


def test_schema_columns_exist(duck_conn):
    """Verify all required canonical columns exist with expected names."""
    df_desc = duck_conn.execute(f"DESCRIBE SELECT * FROM read_parquet('{PARQUET_PATH}') LIMIT 1").df()
    cols = df_desc['column_name'].tolist()
    expected = [
        'application_id', 'application_date', 'application_year', 'loan_amount',
        'dti', 'dti_band', 'amount_band', 'risk_score', 'has_risk_score',
        'addr_state', 'emp_length', 'emp_length_years', 'emp_length_band',
        'loan_purpose', 'is_approved', 'loan_status', 'outcome_bucket', 'funnel_stage'
    ]
    for exp_col in expected:
        assert exp_col in cols, f"Missing required column: {exp_col}"


def test_critical_fields_no_unexpected_nulls(duck_conn):
    """Verify primary key, date, and decision flag contain zero null values."""
    res = duck_conn.execute(f"""
        SELECT 
            count(CASE WHEN application_id IS NULL THEN 1 END) AS null_ids,
            count(CASE WHEN application_date IS NULL THEN 1 END) AS null_dates,
            count(CASE WHEN is_approved IS NULL THEN 1 END) AS null_approvals,
            count(CASE WHEN loan_amount IS NULL THEN 1 END) AS null_amounts
        FROM read_parquet('{PARQUET_PATH}')
    """).fetchone()

    assert res[0] == 0, f"Found {res[0]} null application_ids!"
    assert res[1] == 0, f"Found {res[1]} null application_dates!"
    assert res[2] == 0, f"Found {res[2]} null is_approved flags!"
    assert res[3] == 0, f"Found {res[3]} null loan_amounts!"


def test_date_range_bounds(duck_conn):
    """Verify application dates fall strictly within the 2007 to 2018 window."""
    res = duck_conn.execute(f"""
        SELECT 
            min(application_date) AS min_d,
            max(application_date) AS max_d,
            min(application_year) AS min_y,
            max(application_year) AS max_y
        FROM read_parquet('{PARQUET_PATH}')
    """).fetchone()

    assert str(res[0]) >= "2007-01-01", f"Date below minimum: {res[0]}"
    assert str(res[1]) <= "2018-12-31", f"Date above maximum: {res[1]}"
    assert res[2] == 2007, f"Min year is {res[2]}, expected 2007"
    assert res[3] == 2018, f"Max year is {res[3]}, expected 2018"


def test_binary_decision_flag(duck_conn):
    """Verify is_approved contains only {0, 1}."""
    res = duck_conn.execute(f"""
        SELECT DISTINCT is_approved FROM read_parquet('{PARQUET_PATH}') ORDER BY 1
    """).fetchall()
    values = [r[0] for r in res]
    assert values == [0, 1], f"Unexpected values in is_approved: {values}"


def test_positive_loan_amounts(duck_conn):
    """Verify accepted loans always have strictly positive amounts."""
    res = duck_conn.execute(f"""
        SELECT count(*) FROM read_parquet('{PARQUET_PATH}')
        WHERE is_approved = 1 AND loan_amount <= 0;
    """).fetchone()[0]
    assert res == 0, f"Found {res} accepted loans with non-positive amounts!"


def test_wilson_score_interval_bounds():
    """Verify mathematical properties of Wilson score interval function."""
    p, l, u = wilson_score_interval(0, 100)
    assert l == 0.0
    assert u > 0.0 and u < 1.0

    p, l, u = wilson_score_interval(100, 100)
    assert p == 1.0
    assert l > 0.0 and l < 1.0
    assert u == 1.0

    p, l, u = wilson_score_interval(756, 10000)
    assert np.isclose(p, 0.0756)
    assert 0.0 <= l <= p <= u <= 1.0


def test_two_proportion_z_test_significance():
    """Verify hypothesis test identifies significant vs non-significant differences."""
    # Large distinct samples
    res_sig = two_proportion_z_test(1000, 10000, 500, 10000)
    assert res_sig["is_significant"] is True
    assert res_sig["p_value"] < 0.001

    # Identical proportions
    res_null = two_proportion_z_test(500, 10000, 500, 10000)
    assert res_null["is_significant"] is False
    assert res_null["p_value"] == 1.0
