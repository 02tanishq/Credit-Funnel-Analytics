"""
Streamlit Dashboard: Lending Product Funnel & Approval Analytics
Interactive application for product analysts, credit committees, and portfolio managers.
Covers funnel stages, segment drop-offs with 95% CIs, cohort vintages, approval drivers,
quadrant value matrices, sensitivity policy scenarios, and CSV mart exports.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.stats import wilson_score_interval, two_proportion_z_test
from src.scenario import run_all_scenarios

st.set_page_config(
    page_title="Lending Product Funnel & Approval Analysis",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for executive polish
st.markdown("""
<style>
    .main-header { font-size: 28px; font-weight: 700; color: #1e3d59; margin-bottom: 2px; }
    .sub-header { font-size: 15px; color: #555; margin-bottom: 20px; }
    .metric-card { background-color: #f8f9fa; border-left: 4px solid #175e9e; padding: 12px; border-radius: 4px; margin-bottom: 15px; }
    .metric-title { font-size: 13px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
    .metric-value { font-size: 24px; font-weight: 700; color: #175e9e; }
    .metric-sub { font-size: 12px; color: #888; }
    .alert-box { background-color: #e8f4fd; border: 1px solid #b8daff; padding: 12px; border-radius: 6px; font-size: 14px; color: #004085; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

MARTS_DIR = "data/marts"


@st.cache_data
def load_marts():
    """Load analytical CSV marts."""
    funnel = pd.read_csv(f"{MARTS_DIR}/mart_funnel_summary.csv")
    segments = pd.read_csv(f"{MARTS_DIR}/mart_funnel_by_segment.csv")
    cohorts = pd.read_csv(f"{MARTS_DIR}/mart_cohort_vintage.csv")
    risk_return = pd.read_csv(f"{MARTS_DIR}/mart_segment_risk_return.csv")
    scenarios = pd.read_csv(f"{MARTS_DIR}/mart_scenario_estimates.csv")
    return funnel, segments, cohorts, risk_return, scenarios


df_funnel, df_segments, df_cohorts, df_risk_return, df_scenarios = load_marts()

# Sidebar branding & controls
st.sidebar.image("https://img.icons8.com/color/96/bank-building.png", width=64)
st.sidebar.title("Credit Funnel Engine")
st.sidebar.caption("Portfolio Project: Retail Product Analyst")

nav_selection = st.sidebar.radio(
    "Navigation Modules:",
    [
        "1. Executive Funnel Overview",
        "2. Segment Drilldown & 95% CIs",
        "3. Econometric Approval Drivers",
        "4. Cohort Vintage Loss Curves",
        "5. Segment Risk-Return Matrix",
        "6. Underwriting Policy Scenarios",
        "7. Export Marts (Power BI)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Data Governance Audit:**
- Total Applications: **29,909,409**
- Approved & Funded: **2,260,668**
- Rejected: **27,648,741**
- Reconciled Discrepancy: **0.00%**
""")


# ==============================================================================
# MODULE 1: EXECUTIVE FUNNEL OVERVIEW
# ==============================================================================
if nav_selection == "1. Executive Funnel Overview":
    st.markdown('<div class="main-header">Lending Product Funnel & Conversion Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">End-to-End Pipeline Performance across 29.9M Applications (2007–2018)</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="alert-box">
        <strong>Institutional Underwriting Boundary:</strong> Stage 2 captures <em>Approved and Funded</em> applications. 
        In peer-to-peer and NBFC public records, borrowers offered credit who abandon before sanction/disbursal are unrecorded. 
        Hence, Stage 2 conversion represents effective commercial funding rate.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""<div class="metric-card"><div class="metric-title">Stage 1 Applied</div>
        <div class="metric-value">29,909,409</div><div class="metric-sub">100.0% Pipeline Inflow</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="metric-card"><div class="metric-title">Stage 2 Approved & Funded</div>
        <div class="metric-value">2,260,668</div><div class="metric-sub">7.56% Overall Conversion</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="metric-card"><div class="metric-title">Stage 3 Fully Paid</div>
        <div class="metric-value">1,078,739</div><div class="metric-sub">47.72% of Funded Loans</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown("""<div class="metric-card"><div class="metric-title">Stage 3 Charged Off (Loss)</div>
        <div class="metric-value">269,360</div><div class="metric-sub">11.92% Nominal Write-off</div></div>""", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns([3, 2])

    with col_chart1:
        st.subheader("Funnel Conversion Waterfall")
        funnel_data = [
            {"Stage": "Stage 1: Applied", "Count": 29909409, "Base": "Total"},
            {"Stage": "Stage 2: Approved & Funded", "Count": 2260668, "Base": "Applied"},
            {"Stage": "Stage 3: Fully Paid", "Count": 1078739, "Base": "Funded"},
            {"Stage": "Stage 3: Current", "Count": 886753, "Base": "Funded"},
            {"Stage": "Stage 3: Charged Off", "Count": 269360, "Base": "Funded"},
            {"Stage": "Stage 3: Late (15-120 DPD)", "Count": 25816, "Base": "Funded"}
        ]
        df_f_chart = pd.DataFrame(funnel_data)
        
        fig_funnel = go.Figure(go.Funnel(
            y=df_f_chart['Stage'][:2],
            x=df_f_chart['Count'][:2],
            textinfo="value+percent initial",
            marker={"color": ["#1e3d59", "#17b978"]}
        ))
        fig_funnel.update_layout(height=350, margin=dict(t=20, b=20, l=10, r=10))
        st.plotly_chart(fig_funnel, use_container_width=True)

    with col_chart2:
        st.subheader("Portfolio Outcome Distribution")
        df_outcomes = df_funnel[df_funnel['stage_order'] >= 3].copy()
        fig_pie = px.pie(
            df_outcomes,
            names='stage_name',
            values='applicant_count',
            color='stage_name',
            color_discrete_map={
                'Stage 3: Fully Paid': '#2ecc71',
                'Stage 3: Current': '#3498db',
                'Stage 3: Charged Off': '#e74c3c',
                'Stage 3: Late': '#f39c12'
            },
            hole=0.45
        )
        fig_pie.update_layout(height=350, margin=dict(t=20, b=20, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)


# ==============================================================================
# MODULE 2: SEGMENT DRILLDOWN & 95% CONFIDENCE INTERVALS
# ==============================================================================
elif nav_selection == "2. Segment Drilldown & 95% CIs":
    st.markdown('<div class="main-header">Segment Conversion Drop-offs & 95% Confidence Intervals</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Statistically Rigorous Drop-off Diagnostics (Wilson Score Bounds & Two-Sample Tests)</div>', unsafe_allow_html=True)

    dimension = st.selectbox(
        "Select Analytical Dimension:",
        ["DTI Band", "Employment Length", "Amount Band", "Loan Purpose", "Year", "State"]
    )

    df_sub = df_segments[df_segments['dimension'] == dimension].copy()
    
    # Calculate Wilson Score CIs
    p, l, u = wilson_score_interval(df_sub['approved_funded'], df_sub['total_applied'])
    df_sub['approval_rate_pct'] = p * 100
    df_sub['ci_lower_pct'] = l * 100
    df_sub['ci_upper_pct'] = u * 100
    df_sub['dropoff_rate_pct'] = (1.0 - p) * 100
    df_sub['ci_half_width_pct'] = (df_sub['ci_upper_pct'] - df_sub['ci_lower_pct']) / 2.0

    col1, col2 = st.columns([3, 2])
    with col1:
        st.subheader(f"Conversion Rate by {dimension} with 95% Error Bounds")
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=df_sub['segment_value'],
            y=df_sub['approval_rate_pct'],
            error_y=dict(type='data', array=df_sub['ci_half_width_pct'], visible=True),
            marker_color='#175e9e',
            text=df_sub['approval_rate_pct'].round(2).astype(str) + '%',
            textposition='auto'
        ))
        fig_bar.add_hline(y=7.56, line_dash="dash", line_color="red", annotation_text="Portfolio Avg (7.56%)")
        fig_bar.update_layout(height=420, yaxis_title="Approval & Funding Rate (%)", xaxis_title=dimension)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.subheader("Statistical Significance Testing Tool")
        st.caption("Compare any segment against portfolio benchmark or another segment using Two-Proportion z-test.")
        
        seg_names = df_sub['segment_value'].tolist()
        s1 = st.selectbox("Select Segment A:", seg_names, index=0)
        s2 = st.selectbox("Select Segment B:", seg_names, index=min(1, len(seg_names)-1))
        
        r1 = df_sub[df_sub['segment_value'] == s1].iloc[0]
        r2 = df_sub[df_sub['segment_value'] == s2].iloc[0]
        
        test_res = two_proportion_z_test(r1['approved_funded'], r1['total_applied'], r2['approved_funded'], r2['total_applied'])
        
        st.markdown(f"""
        **Hypothesis Test Results:**
        - **{s1}:** {test_res['p1']*100:.2f}% (N = {r1['total_applied']:,})
        - **{s2}:** {test_res['p2']*100:.2f}% (N = {r2['total_applied']:,})
        - **Rate Differential:** {test_res['diff']*100:+.2f}%
        - **z-statistic:** {test_res['z_stat']:.3f}
        - **p-value:** `{test_res['p_value']:.2e}`
        - **Significant at $\\alpha = 0.05$:** `{'YES (Statistically Significant)' if test_res['is_significant'] else 'NO'}`
        """)

    st.subheader(f"Audited Data Table: {dimension}")
    display_cols = ['segment_value', 'total_applied', 'approved_funded', 'dropoff_rate_pct', 'approval_rate_pct', 'ci_lower_pct', 'ci_upper_pct']
    st.dataframe(
        df_sub[display_cols].rename(columns={
            'segment_value': dimension,
            'total_applied': 'Total Applicants (N)',
            'approved_funded': 'Funded Loans (k)',
            'dropoff_rate_pct': 'Drop-off Rate (%)',
            'approval_rate_pct': 'Approval Rate (%)',
            'ci_lower_pct': 'Wilson 95% Lower (%)',
            'ci_upper_pct': 'Wilson 95% Upper (%)'
        }).style.format({
            'Total Applicants (N)': '{:,}',
            'Funded Loans (k)': '{:,}',
            'Drop-off Rate (%)': '{:.2f}%',
            'Approval Rate (%)': '{:.2f}%',
            'Wilson 95% Lower (%)': '{:.2f}%',
            'Wilson 95% Upper (%)': '{:.2f}%'
        }),
        use_container_width=True
    )


# ==============================================================================
# MODULE 3: ECONOMETRIC APPROVAL DRIVERS
# ==============================================================================
elif nav_selection == "3. Econometric Approval Drivers":
    st.markdown('<div class="main-header">Underwriting Approval Drivers & Econometric Audit</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Logistic Regression with Odds Ratios, Confidence Intervals, and Selection Bias Diagnostics</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="alert-box">
        <strong>Selection Bias & Knockout Hurdle Audit:</strong> 
        In the raw rejected dataset, 66.9% of records lack a bureau credit score because Lending Club applied 
        hard knockout rules (unserviceable DTI, zero self-reported income, invalid state) 
        before paying bureau inquiry API fees. The logistic model below evaluates scored applicants 
        who passed the initial pre-screen knockout gate (AUC = 0.9348, Pseudo R² = 0.4523).
    </div>
    """, unsafe_allow_html=True)

    # Econometric results from verified modeling pipeline
    driver_data = [
        {"Driver": "Bureau Risk Score (+50 pts)", "Odds_Ratio": 2.523, "OR_Lower": 2.466, "OR_Upper": 2.582, "p_value": "< 1e-300", "Direction": "Positive"},
        {"Driver": "Employment Tenure (+1 yr)", "Odds_Ratio": 1.484, "OR_Lower": 1.475, "OR_Upper": 1.494, "p_value": "< 1e-300", "Direction": "Positive"},
        {"Driver": "Purpose: Credit Card Refinance", "Odds_Ratio": 1.718, "OR_Lower": 1.624, "OR_Upper": 1.818, "p_value": "8.5e-79", "Direction": "Positive"},
        {"Driver": "Requested Ticket Size (+$5,000)", "Odds_Ratio": 0.951, "OR_Lower": 0.940, "OR_Upper": 0.962, "p_value": "3.4e-18", "Direction": "Negative"},
        {"Driver": "Debt-To-Income Ratio (+10% DTI)", "Odds_Ratio": 0.776, "OR_Lower": 0.765, "OR_Upper": 0.788, "p_value": "5.7e-241", "Direction": "Negative"},
        {"Driver": "Purpose: Home Improvement", "Odds_Ratio": 0.626, "OR_Lower": 0.569, "OR_Upper": 0.688, "p_value": "3.1e-22", "Direction": "Negative"},
        {"Driver": "Purpose: Major Purchase", "Odds_Ratio": 0.584, "OR_Lower": 0.507, "OR_Upper": 0.674, "p_value": "1.4e-13", "Direction": "Negative"},
        {"Driver": "Purpose: Medical Expenses", "Odds_Ratio": 0.353, "OR_Lower": 0.291, "OR_Upper": 0.430, "p_value": "1.8e-25", "Direction": "Negative"},
        {"Driver": "Purpose: Small Business", "Odds_Ratio": 0.223, "OR_Lower": 0.184, "OR_Upper": 0.271, "p_value": "2.3e-51", "Direction": "Negative"},
        {"Driver": "Purpose: Auto Financing", "Odds_Ratio": 0.167, "OR_Lower": 0.138, "OR_Upper": 0.202, "p_value": "4.5e-76", "Direction": "Negative"}
    ]
    df_drivers = pd.DataFrame(driver_data)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.subheader(r"Odds Ratios of Approval ($\exp(\beta)$)")
        fig_or = px.bar(
            df_drivers.sort_values(by="Odds_Ratio", ascending=True),
            x="Odds_Ratio",
            y="Driver",
            orientation="h",
            color="Direction",
            color_discrete_map={"Positive": "#27ae60", "Negative": "#e74c3c"},
            text="Odds_Ratio",
            error_x="OR_Upper"
        )
        fig_or.add_vline(x=1.0, line_dash="dash", line_color="black")
        fig_or.update_layout(height=480, xaxis_title="Odds Ratio (Relative to Baseline)", yaxis_title="")
        st.plotly_chart(fig_or, use_container_width=True)

    with col2:
        st.subheader("Key Econometric Findings")
        st.markdown("""
        1. **FICO Elasticity:** A +50 point lift in credit score multiplies approval odds by **2.52x** ($p < 0.001$).
        2. **Employment Anchor:** Each year of job stability increases approval odds by **+48.4%** (OR = 1.484).
        3. **DTI Sensitivity:** Every +10% increase in DTI suppresses approval odds by **-22.4%** (OR = 0.776).
        4. **Unsecured Small Business Rejection:** Commercial loan requests face an **88% lower odds** of approval than consumer debt consolidation (OR = 0.223).
        5. **Omitted Variable Limitations:** Bureau credit line depth, revolving utilization, and bank balance data are unrecorded in rejected applications.
        """)

    st.dataframe(df_drivers, use_container_width=True)


# ==============================================================================
# MODULE 4: COHORT VINTAGE LOSS CURVES
# ==============================================================================
elif nav_selection == "4. Cohort Vintage Loss Curves":
    st.markdown('<div class="main-header">Portfolio Vintage & Cohort Maturation Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Tracking Realized Charge-offs over Loan Life across Origination Vintages (2007–2018)</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="alert-box">
        <strong>The Right-Censoring Trap:</strong> 
        Top-line charge-off rates for recent cohorts (2017: 8.83%, 2018: 1.79%) appear artificially healthy. 
        This is an artifact of portfolio immaturity: 86.8% of 2018 loans and 59.7% of 2017 loans are still 
        actively paying (Current). Benchmark loss performance must be anchored to mature cohorts (2013–2015: 15.6%–18.0%).
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.subheader("Vintage Curves: Charge-off Rate vs Maturation")
        fig_cohort = go.Figure()
        fig_cohort.add_trace(go.Scatter(
            x=df_cohorts['orig_year'],
            y=df_cohorts['cumulative_charge_off_rate'] * 100,
            mode='lines+markers',
            name='Nominal Charge-Off Rate (%)',
            line=dict(color='#c0392b', width=3),
            marker=dict(size=8)
        ))
        fig_cohort.add_trace(go.Scatter(
            x=df_cohorts['orig_year'],
            y=df_cohorts['current_rate'] * 100,
            mode='lines+markers',
            name='Active / Current Rate (%)',
            line=dict(color='#2980b9', width=3, dash='dot'),
            marker=dict(size=8)
        ))
        fig_cohort.update_layout(height=420, xaxis_title="Origination Vintage Year", yaxis_title="Percentage of Cohort (%)")
        st.plotly_chart(fig_cohort, use_container_width=True)

    with col2:
        st.subheader("Annual Disbursal Volume Growth")
        fig_vol = px.bar(
            df_cohorts,
            x='orig_year',
            y=df_cohorts['total_funded_volume'] / 1e9,
            title="Total Disbursed Volume ($ Billions)",
            labels={'y': 'Disbursed Volume ($B)', 'orig_year': 'Origination Year'},
            color_discrete_sequence=['#2c3e50']
        )
        fig_vol.update_layout(height=420)
        st.plotly_chart(fig_vol, use_container_width=True)

    st.subheader("Audited Cohort Vintage Mart")
    st.dataframe(
        df_cohorts.rename(columns={
            'orig_year': 'Origination Year',
            'total_funded_loans': 'Funded Contracts',
            'total_funded_volume': 'Funded Volume ($)',
            'fully_paid_count': 'Fully Paid (n)',
            'current_count': 'Current (n)',
            'late_count': 'Late 15-120 DPD (n)',
            'charged_off_count': 'Charged Off (n)',
            'cumulative_charge_off_rate': 'Nominal Loss Rate',
            'current_rate': 'Active Contract Ratio'
        }).style.format({
            'Funded Contracts': '{:,}',
            'Funded Volume ($)': '${:,.0f}',
            'Fully Paid (n)': '{:,}',
            'Current (n)': '{:,}',
            'Late 15-120 DPD (n)': '{:,}',
            'Charged Off (n)': '{:,}',
            'Nominal Loss Rate': '{:.2%}',
            'Active Contract Ratio': '{:.2%}'
        }),
        use_container_width=True
    )


# ==============================================================================
# MODULE 5: SEGMENT RISK-RETURN MATRIX
# ==============================================================================
elif nav_selection == "5. Segment Risk-Return Matrix":
    st.markdown('<div class="main-header">Segment Value Matrix: Approval Rate vs Credit Risk</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Strategic 2x2 Matrix to Reallocate Underwriting Bandwidth for RAROC Expansion</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        fig_quad = px.scatter(
            df_risk_return,
            x="approval_rate",
            y="charge_off_rate",
            size="applied_count",
            color="loan_purpose",
            hover_name="loan_purpose",
            hover_data={"amount_band": True, "dti_band": True, "applied_count": True, "approval_rate": ":.2%", "charge_off_rate": ":.2%"},
            labels={"approval_rate": "Approval & Funding Rate", "charge_off_rate": "Realized Charge-Off Rate"},
            title="Segment Value Quadrants (Bubble Size = Applicant Volume)"
        )
        fig_quad.add_vline(x=0.0756, line_dash="dash", line_color="grey", annotation_text="Avg Approval (7.56%)")
        fig_quad.add_hline(y=0.1600, line_dash="dash", line_color="red", annotation_text="Benchmark Default (16.0%)")
        fig_quad.update_layout(height=520)
        st.plotly_chart(fig_quad, use_container_width=True)

    with col2:
        st.markdown("""
        ### Strategic Quadrants
        - **Quadrant I: Prime Core**  
          High Approval / Low Risk  
          *Strategy:* Maintain prime retention & pricing.
        - **Quadrant II: Growth Goldmine**  
          Low Approval / Low Risk  
          *Strategy:* Relax blunt DTI/tenure gates; expand originations.
        - **Quadrant III: Subprime Filter**  
          Low Approval / High Risk  
          *Strategy:* Keep knockout rules intact.
        - **Quadrant IV: Leakage Danger**  
          High Approval / High Risk  
          *Strategy:* Cap tickets & raise cutoffs.
        """)


# ==============================================================================
# MODULE 6: UNDERWRITING POLICY SCENARIOS
# ==============================================================================
elif nav_selection == "6. Underwriting Policy Scenarios":
    st.markdown('<div class="main-header">Underwriting Policy Scenario Modeling & Sensitivity</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Evaluating Strategic Interventions with Sensitivity Ranges (Not Deterministic Forecasts)</div>', unsafe_allow_html=True)

    st.subheader("Scenario 1: Near-Prime Tiered DTI Bridge (DTI 20–30%, Employment ≥ 5 yrs)")
    st.markdown("""
    **Context:** Applicants with DTI between 20% and 30% and steady employment tenure (5+ years) are currently rejected at high rates (~85%). 
    **Policy Change:** Implement a tiered DTI underwriting bridge approving 18% of this qualified borderline pool.
    """)

    df_scen1 = df_scenarios[df_scenarios['scenario_name'].str.contains('Scenario 1')].copy()
    col1, col2, col3 = st.columns(3)
    for idx, (c, tier) in enumerate(zip([col1, col2, col3], ['Pessimistic', 'Base Case', 'Optimistic'])):
        row = df_scen1[df_scen1['sensitivity_tier'].str.contains(tier)].iloc[0]
        with c:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{tier} Sensitivity</div>
                <div class="metric-value">+{row['incremental_funded_loans']:,}</div>
                <div class="metric-sub">Incremental Disbursal: ${row['incremental_funded_volume_usd']/1e6:,.1f}M<br>
                Expected Losses: ${row['expected_cumulative_charge_offs_usd']/1e6:,.1f}M ({row['expected_charge_off_rate']:.1%})</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Scenario 2: Small Business / High-Ticket Risk Tightening (> $25,000)")
    st.markdown("""
    **Context:** Unsecured Small Business loans > $25,000 exhibit high charge-off rates (>24.5%).
    **Policy Change:** Cap unsecured exposure at $20k and enforce 720+ FICO cutoff, pruning high-risk volume by 25%.
    """)

    df_scen2 = df_scenarios[df_scenarios['scenario_name'].str.contains('Scenario 2')].copy()
    col1, col2, col3 = st.columns(3)
    for idx, (c, tier) in enumerate(zip([col1, col2, col3], ['Pessimistic', 'Base Case', 'Optimistic'])):
        row = df_scen2[df_scen2['sensitivity_tier'].str.contains(tier)].iloc[0]
        with c:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{tier} Sensitivity</div>
                <div class="metric-value">{row['incremental_funded_loans']:,}</div>
                <div class="metric-sub">Exposure Reduced: ${abs(row['incremental_funded_volume_usd'])/1e6:,.1f}M<br>
                Capital Preserved: ${abs(row['expected_cumulative_charge_offs_usd'])/1e6:,.1f}M ({row['expected_charge_off_rate']:.1%})</div>
            </div>
            """, unsafe_allow_html=True)


# ==============================================================================
# MODULE 7: EXPORT MARTS (POWER BI)
# ==============================================================================
elif nav_selection == "7. Export Marts (Power BI)":
    st.markdown('<div class="main-header">Export Analytical Marts for Power BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Pre-Aggregated, Audited CSV Files Ready for Enterprise BI Dashboards</div>', unsafe_allow_html=True)

    st.markdown("""
    All analytical marts below have been materialized directly from the canonical 29.9M application dataset.
    You can download each CSV to rebuild a mirror dashboard in Power BI or Tableau.
    """)

    marts_list = [
        ("mart_funnel_summary.csv", "Overall Funnel Stages & Cumulative Conversion", df_funnel),
        ("mart_funnel_by_segment.csv", "Funnel Rates by Macro Dimensions (Year, State, Purpose, DTI, Ticket)", df_segments),
        ("mart_cohort_vintage.csv", "Origination Vintage Curves & Maturation Metrics (2007-2018)", df_cohorts),
        ("mart_segment_risk_return.csv", "Segment Value Matrix (Approval Rate vs Realized Default Rate)", df_risk_return),
        ("mart_scenario_estimates.csv", "Product Policy Recommendations & Sensitivity Ranges", df_scenarios)
    ]

    for fname, desc, df_obj in marts_list:
        with st.expander(f"📁 {fname} - {desc}", expanded=True):
            st.dataframe(df_obj.head(5), use_container_width=True)
            csv_bytes = df_obj.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"⬇️ Download {fname}",
                data=csv_bytes,
                file_name=fname,
                mime="text/csv",
                key=fname
            )
