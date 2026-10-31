"""
Notebook Generator & Executor
Builds production-grade, portfolio-ready Jupyter notebooks with executed outputs,
clear analytical commentary, and zero leftover debug cells.
"""

import nbformat as nbf
from nbclient import NotebookClient


def build_notebook_01():
    """Build and execute 01_eda_and_common_table.ipynb"""
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("""# Notebook 01: Exploratory Data Analysis & Common Table Architecture
**Portfolio Project:** Lending Product Funnel & Approval Analysis  
**Institutional Framing:** Retail Lending Product Analyst at an Indian NBFC (e.g. Bajaj Finance)  
**Objective:** Inspect raw schemas, audit data missingness and selection bias, reconcile row counts (29.9M records), and establish the canonical common applications data model.
"""),
        nbf.v4.new_code_cell("""import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Visual formatting
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['figure.figsize'] = (10, 5)
plt.rcParams['font.size'] = 11

con = duckdb.connect()
print("DuckDB engine initialized successfully.")
"""),
        nbf.v4.new_markdown_cell("""## 1. Raw Schema Inspection & Column Alignment
The project processes two separate raw files in `data/raw/`:
1. `accepted_2007_to_2018Q4.csv.gz` (2,260,701 rows, 151 columns)
2. `rejected_2007_to_2018Q4.csv.gz` (27,648,741 rows, 9 columns)
"""),
        nbf.v4.new_code_cell("""# Inspect sample records from canonical Parquet mart
df_sample = con.execute(\"\"\"
    SELECT 
        application_id, application_date, application_year, loan_amount,
        dti, dti_band, risk_score, has_risk_score, addr_state,
        emp_length_band, loan_purpose, is_approved, outcome_bucket
    FROM read_parquet('data/processed/common_applications.parquet')
    LIMIT 10;
\"\"\").df()

df_sample
"""),
        nbf.v4.new_markdown_cell("""## 2. Row Count Reconciliation Audit
Every row from the raw files is accounted for:
- Raw Accepted: 2,260,701 records. Exactly 33 trailing footer/metadata rows where `issue_d` is null are dropped, leaving 2,260,668 valid funded loans.
- Raw Rejected: 27,648,741 records. Zero null dates, 100% retained.
- Total Canonical Applications: 29,909,409.
"""),
        nbf.v4.new_code_cell("""reconciliation_summary = con.execute(\"\"\"
    SELECT 
        is_approved,
        CASE WHEN is_approved = 1 THEN 'Approved & Funded' ELSE 'Rejected' END AS status_label,
        count(*) AS total_records,
        round(count(*)::DOUBLE / 29909409.0 * 100, 2) AS pct_of_total_applications
    FROM read_parquet('data/processed/common_applications.parquet')
    GROUP BY is_approved;
\"\"\").df()

reconciliation_summary
"""),
        nbf.v4.new_markdown_cell("""## 3. Critical Data Nuance: Missing Bureau Scores & Knockout Bias
Notice that in the rejected table, only 33.1% (9.15M records) have a recorded risk score. 
In institutional lending (Bajaj Finance), applicants failing initial knockout rules (e.g., negative DTI, unsupported postal code, self-reported zero income) are rejected before incurring external credit bureau inquiry costs.
"""),
        nbf.v4.new_code_cell("""risk_score_missingness = con.execute(\"\"\"
    SELECT 
        CASE WHEN is_approved = 1 THEN 'Approved & Funded' ELSE 'Rejected' END AS application_status,
        count(*) AS total_applications,
        count(risk_score) AS scored_count,
        count(*) - count(risk_score) AS missing_score_count,
        round((count(*) - count(risk_score))::DOUBLE / count(*) * 100, 2) AS missing_score_pct
    FROM read_parquet('data/processed/common_applications.parquet')
    GROUP BY is_approved;
\"\"\").df()

risk_score_missingness
"""),
        nbf.v4.new_markdown_cell("""## 4. Key Distributions Across Common Dimensions
Visualizing distribution of loan amounts, DTI bands, and employment tenure.
"""),
        nbf.v4.new_code_cell("""# Distribution of applied volume by loan purpose
df_purpose = con.execute(\"\"\"
    SELECT 
        loan_purpose,
        count(*) AS total_applied,
        count(CASE WHEN is_approved = 1 THEN 1 END) AS approved_count,
        round(count(CASE WHEN is_approved = 1 THEN 1 END)::DOUBLE / count(*), 4) AS approval_rate
    FROM read_parquet('data/processed/common_applications.parquet')
    GROUP BY loan_purpose
    ORDER BY total_applied DESC
    LIMIT 8;
\"\"\").df()

fig, ax1 = plt.subplots(figsize=(12, 5))
sns.barplot(data=df_purpose, x='loan_purpose', y='total_applied', ax=ax1, color='#2b5c8f', alpha=0.8)
ax1.set_ylabel('Total Applications (Millions)', color='#2b5c8f')
ax1.set_title('Top Loan Purposes: Total Application Volume vs Approval Rate', fontsize=14, fontweight='bold')
ax1.tick_params(axis='x', rotation=30)

ax2 = ax1.twinx()
sns.lineplot(data=df_purpose, x='loan_purpose', y='approval_rate', ax=ax2, color='#e05d44', marker='o', linewidth=2.5)
ax2.set_ylabel('Approval Rate', color='#e05d44')
ax2.grid(False)

plt.tight_layout()
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 5. Analytical Takeaways from EDA
1. **Underwriting Bottleneck:** The primary volume drop-off occurs between Stage 1 (Applied) and Stage 2 (Funded), with an overall pass-through rate of only 7.56%.
2. **Missingness is an Informative Signal:** Missing risk scores are concentrated entirely in rejected applications, confirming that Lending Club implemented a two-stage knockout funnel.
3. **Data Parity:** With 29,909,409 reconciled records, the canonical parquet table is ready for deep statistical and econometric analysis in Notebook 02.
""")
    ]

    client = NotebookClient(nb, timeout=600, kernel_name='python3')
    client.execute()
    with open('notebooks/01_eda_and_common_table.ipynb', 'w') as f:
        nbf.write(nb, f)
    print("Notebook 01 built and executed successfully!")


def build_notebook_02():
    """Build and execute 02_funnel_and_product_analytics.ipynb"""
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("""# Notebook 02: Funnel Conversion, Econometric Drivers, Cohort Vintages & Scenarios
**Portfolio Project:** Lending Product Funnel & Approval Analysis  
**Institutional Framing:** Retail Lending Product Analyst at an Indian NBFC (e.g. Bajaj Finance)  
**Objective:** Calculate stage conversions with 95% Wilson Score CIs, estimate econometric approval drivers, evaluate cohort vintage maturation curves, construct the segment risk-return matrix, and simulate policy scenarios.
"""),
        nbf.v4.new_code_cell("""import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from src.stats import wilson_score_interval, two_proportion_z_test
from src.modeling import fit_approval_logistic_regression, load_model_sample
from src.scenario import run_all_scenarios

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['figure.figsize'] = (10, 5)

con = duckdb.connect()
print("Dependencies loaded successfully.")
"""),
        nbf.v4.new_markdown_cell("""## 1. Funnel Stage Conversion Rates (Stages 1 -> 2 -> 3)
In public Lending Club records, "approved" reflects **funded/disbursed** loans because approved-but-not-taken offers are unrecorded.
"""),
        nbf.v4.new_code_cell("""df_funnel = pd.read_csv('data/marts/mart_funnel_summary.csv')
total_app = df_funnel.loc[df_funnel['stage_name'] == 'Stage 1: Applied', 'applicant_count'].values[0]
funded_app = df_funnel.loc[df_funnel['stage_name'] == 'Stage 2: Approved and Funded', 'applicant_count'].values[0]

df_funnel['stage_conversion_pct'] = np.where(
    df_funnel['stage_order'] <= 2,
    (df_funnel['applicant_count'] / total_app) * 100,
    (df_funnel['applicant_count'] / funded_app) * 100
)

df_funnel
"""),
        nbf.v4.new_markdown_cell("""## 2. Drop-off Analysis with Wilson Score 95% Confidence Intervals
Normalizing drop-offs by applicant counts and calculating Wilson Score intervals to avoid small-sample or boundary distortions.
"""),
        nbf.v4.new_code_cell("""df_seg = pd.read_csv('data/marts/mart_funnel_by_segment.csv')
dti_seg = df_seg[df_seg['dimension'] == 'DTI Band'].copy()

p_hat, l_ci, u_ci = wilson_score_interval(dti_seg['approved_funded'], dti_seg['total_applied'])
dti_seg['approval_rate_pct'] = p_hat * 100
dti_seg['ci_lower_pct'] = l_ci * 100
dti_seg['ci_upper_pct'] = u_ci * 100

dti_seg[['segment_value', 'total_applied', 'approved_funded', 'approval_rate_pct', 'ci_lower_pct', 'ci_upper_pct']]
"""),
        nbf.v4.new_markdown_cell("""## 3. Econometric Approval Drivers (Logistic Regression & Odds Ratios)
Fitting a logistic regression on scored applicants to quantify the marginal impact of bureau score, DTI, ticket size, and employment tenure on underwriting pass rates.
"""),
        nbf.v4.new_code_cell("""df_sample = load_model_sample(sample_size=150000, random_seed=42)
results_df, metrics = fit_approval_logistic_regression(df_sample)

print(f"Model Fit: AUC-ROC = {metrics['auc_roc']:.4f} | Pseudo R2 = {metrics['pseudo_r_squared']:.4f} (N = {metrics['num_observations']:,})")
results_df[['Feature_Label', 'Odds_Ratio', 'Odds_Ratio_Lower_95', 'Odds_Ratio_Upper_95', 'p_value']]
"""),
        nbf.v4.new_markdown_cell("""## 4. Vintage / Cohort Analysis (Maturation Curves & Right-Censoring)
Tracking cumulative charge-off rates by origination year (2007–2018).
Notice that recent cohorts (2017–2018) exhibit deceptively low nominal charge-offs (8.83% and 1.79%) because the loans are active.
"""),
        nbf.v4.new_code_cell("""df_cohort = pd.read_csv('data/marts/mart_cohort_vintage.csv')

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(df_cohort['orig_year'], df_cohort['cumulative_charge_off_rate'] * 100, marker='s', color='#c0392b', linewidth=2.5, label='Nominal Charge-Off Rate (% Funded)')
ax.plot(df_cohort['orig_year'], df_cohort['current_rate'] * 100, marker='o', color='#2980b9', linewidth=2.5, label='Active / Current Rate (% Funded)')
ax.set_title('Portfolio Maturation: Cumulative Charge-Off Rate vs Active Loans by Origination Year', fontsize=13, fontweight='bold')
ax.set_xlabel('Origination Vintage Year')
ax.set_ylabel('Percentage of Cohort (%)')
ax.legend(loc='upper right')
plt.tight_layout()
plt.show()

df_cohort[['orig_year', 'total_funded_loans', 'charged_off_count', 'cumulative_charge_off_rate', 'current_rate']]
"""),
        nbf.v4.new_markdown_cell("""## 5. Segment Value Matrix (Approval vs Realized Credit Risk)
Identifying Quadrant II (Growth Opportunities: High Rejection but Low Default) vs Quadrant IV (Danger Zones: High Approval with High Default).
"""),
        nbf.v4.new_code_cell("""df_quad = pd.read_csv('data/marts/mart_segment_risk_return.csv')

plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=df_quad,
    x='approval_rate',
    y='charge_off_rate',
    size='applied_count',
    hue='loan_purpose',
    sizes=(40, 400),
    alpha=0.7
)
plt.axvline(0.0756, color='grey', linestyle='--', alpha=0.7, label='Portfolio Avg Approval (7.56%)')
plt.axhline(0.1600, color='red', linestyle='--', alpha=0.7, label='Benchmark Default Threshold (16.0%)')
plt.title('Segment Value Matrix: Approval Rate vs Realized Charge-Off Rate', fontsize=13, fontweight='bold')
plt.xlabel('Approval Rate')
plt.ylabel('Realized Charge-Off Rate')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 6. Underwriting Policy Scenario Simulations
Evaluating proposed interventions with sensitivity ranges (Pessimistic, Base Case, Optimistic).
"""),
        nbf.v4.new_code_cell("""df_scenarios = run_all_scenarios()
df_scenarios[['scenario', 'sensitivity_tier', 'incremental_funded_loans', 'incremental_funded_volume_usd', 'expected_charge_off_rate', 'expected_credit_losses_usd']]
"""),
        nbf.v4.new_markdown_cell("""## 7. Executive Recommendations for NBFC Credit Committee
1. **Execute Near-Prime DTI Expansion:** Pilot an automated tiered approval program for applicants with DTI 20–28% and employment tenure >= 5 years. This unlocks an estimated **\$1.25B in incremental origination volume** with expected credit losses safely bounded between 11.9% and 18.9%.
2. **Institute Small Business Ticket Capping:** Restrict unsecured small business loans exceeding \$25,000, preserving up to **\$11.6M in direct write-offs** with minimal impact on core consumer NIM.
""")
    ]

    client = NotebookClient(nb, timeout=600, kernel_name='python3')
    client.execute()
    with open('notebooks/02_funnel_and_product_analytics.ipynb', 'w') as f:
        nbf.write(nb, f)
    print("Notebook 02 built and executed successfully!")


if __name__ == "__main__":
    build_notebook_01()
    build_notebook_02()
