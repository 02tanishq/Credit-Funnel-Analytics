"""
Econometric & Machine Learning Modeling: Approval Drivers & Selection Bias
Fits interpretable logistic regression models to quantify how observable applicant
attributes drive underwriting decisions, reporting odds ratios and selection bias limitations.
"""

from typing import Dict, Any, Tuple
import duckdb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report
import statsmodels.api as sm


PARQUET_PATH = "data/processed/common_applications.parquet"


def load_model_sample(sample_size: int = 250000, random_seed: int = 42) -> pd.DataFrame:
    """
    Load a balanced/stratified sample from common_applications.parquet to train
    interpretable logistic regression without memory bottlenecks.
    """
    con = duckdb.connect()
    query = f"""
    SELECT 
        is_approved,
        coalesce(risk_score, 620.0) AS risk_score,
        has_risk_score,
        coalesce(dti, 25.0) AS dti,
        loan_amount,
        coalesce(emp_length_years, 0) AS emp_length_years,
        loan_purpose,
        CASE WHEN is_approved = 1 THEN 'Approved' ELSE 'Rejected' END AS approval_label
    FROM read_parquet('{PARQUET_PATH}')
    USING SAMPLE {sample_size} (reservoir, {random_seed});
    """
    df = con.execute(query).df()
    con.close()
    
    # Clip extreme DTI outliers (e.g. self-reported 10,000%) to [0, 100] for stable regression
    df['dti_clipped'] = df['dti'].clip(lower=0.0, upper=100.0)
    
    # Scale continuous variables for intuitive business interpretation:
    # risk_score: per 50-point increase
    # loan_amount: per $5,000 increase
    df['risk_score_50pt'] = df['risk_score'] / 50.0
    df['loan_amount_5k'] = df['loan_amount'] / 5000.0
    df['dti_10pt'] = df['dti_clipped'] / 10.0
    
    return df


def fit_approval_logistic_regression(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Fit an interpretable logistic regression model on scored applicants (those who passed the 
    initial pre-screen knockout gate and had bureau scores pulled).
    
    This avoids quasi-complete separation on `has_risk_score` while properly reflecting
    the two-stage decision process used by NBFC underwriting credit engines.
    
    Returns
    -------
    (results_df, metrics_dict)
    """
    # Restrict to scored applicants to avoid quasi-complete separation
    df_scored = df[df['has_risk_score'] == 1].copy()

    # Create dummies for top loan purposes (reference category: debt_consolidation)
    purposes = ['credit_card', 'home_improvement', 'car', 'small_business', 'major_purchase', 'medical']
    for p in purposes:
        df_scored[f'purpose_{p}'] = (df_scored['loan_purpose'] == p).astype(int)

    feature_cols = [
        'risk_score_50pt',
        'dti_10pt',
        'loan_amount_5k',
        'emp_length_years',
        'purpose_credit_card',
        'purpose_home_improvement',
        'purpose_car',
        'purpose_small_business',
        'purpose_major_purchase',
        'purpose_medical'
    ]

    X = df_scored[feature_cols].copy()
    X = sm.add_constant(X)
    y = df_scored['is_approved']

    logit_model = sm.Logit(y, X).fit(disp=False, maxiter=100)
    
    params = logit_model.params
    conf = logit_model.conf_int()
    conf.columns = ['CI_Lower', 'CI_Upper']
    
    results_df = pd.DataFrame({
        'Feature': params.index,
        'Coefficient_Beta': params.values,
        'Std_Error': logit_model.bse.values,
        'z_statistic': logit_model.tvalues.values,
        'p_value': logit_model.pvalues.values,
        'Odds_Ratio': np.exp(params.values),
        'Odds_Ratio_Lower_95': np.exp(conf['CI_Lower'].values),
        'Odds_Ratio_Upper_95': np.exp(conf['CI_Upper'].values),
    })

    # Human-readable labels for interview presentation
    label_map = {
        'const': 'Baseline Intercept (Debt Consolidation, Ref)',
        'risk_score_50pt': 'Bureau Risk Score (+50 points)',
        'dti_10pt': 'Debt-To-Income Ratio (+10% DTI)',
        'loan_amount_5k': 'Requested Ticket Size (+$5,000)',
        'emp_length_years': 'Employment Tenure (+1 year)',
        'purpose_credit_card': 'Purpose: Credit Card Refinance',
        'purpose_home_improvement': 'Purpose: Home Improvement',
        'purpose_car': 'Purpose: Auto / Car Financing',
        'purpose_small_business': 'Purpose: Small Business',
        'purpose_major_purchase': 'Purpose: Major Purchase',
        'purpose_medical': 'Purpose: Medical Expenses'
    }
    results_df['Feature_Label'] = results_df['Feature'].map(lambda x: label_map.get(x, x))

    # Evaluate predictions
    y_pred_probs = logit_model.predict(X)
    auc = roc_auc_score(y, y_pred_probs)

    metrics = {
        'num_observations': int(logit_model.nobs),
        'pseudo_r_squared': float(logit_model.prsquared),
        'auc_roc': float(auc),
        'log_likelihood': float(logit_model.llf),
        'converged': bool(logit_model.mle_retvals['converged'])
    }

    return results_df, metrics


def run_modeling_pipeline() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Execute data loading, model fitting, and summary print."""
    df_sample = load_model_sample(sample_size=250000)
    results_df, metrics = fit_approval_logistic_regression(df_sample)
    return results_df, metrics


if __name__ == "__main__":
    print("Fitting Logistic Regression Approval Driver Model...")
    res, m = run_modeling_pipeline()
    print(f"\nModel Performance: AUC = {m['auc_roc']:.4f} | Pseudo R2 = {m['pseudo_r_squared']:.4f} | N = {m['num_observations']:,}")
    print("\nUnderwriting Approval Drivers (Odds Ratios & 95% CIs):")
    cols_to_print = ['Feature_Label', 'Odds_Ratio', 'Odds_Ratio_Lower_95', 'Odds_Ratio_Upper_95', 'p_value']
    print(res[cols_to_print].to_string(index=False))
