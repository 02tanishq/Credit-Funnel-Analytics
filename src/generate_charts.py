"""
Chart Generator for Executive Presentation & Portfolio Documentation
Saves high-resolution figures to docs/images/ for README and FINDINGS.md.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

os.makedirs("docs/images", exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 11

MARTS_DIR = "data/marts"


def chart_funnel():
    """Figure 1: Funnel Waterfall & Stage Drop-offs."""
    df = pd.read_csv(f"{MARTS_DIR}/mart_funnel_summary.csv")
    stages = ["Stage 1: Applied", "Stage 2: Approved & Funded", "Fully Paid", "Current", "Charged Off", "Late (15-120 DPD)"]
    counts = [29909409, 2260668, 1078739, 886753, 269360, 25816]
    pcts = ["100.0%", "7.56% of Inflow", "47.72% of Funded", "39.23% of Funded", "11.92% of Funded", "1.14% of Funded"]
    colors = ['#1e3d59', '#17b978', '#2ecc71', '#3498db', '#e74c3c', '#f39c12']

    fig, ax = plt.subplots(figsize=(11, 5.5))
    bars = ax.barh(stages[::-1], [c / 1e6 for c in counts[::-1]], color=colors[::-1], edgecolor='black', linewidth=0.8, alpha=0.9)
    
    for bar, pct, cnt in zip(bars, pcts[::-1], counts[::-1]):
        width = bar.get_width()
        ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, f"{cnt:,} ({pct})",
                va='center', ha='left', fontsize=10, fontweight='bold', color='#2c3e50')

    ax.set_xlim(0, 34)
    ax.set_xlabel('Applicants / Contracts (Millions)', fontweight='bold')
    ax.set_title('Lending Product Pipeline: Full Funnel Conversion & Outcome Distribution (2007–2018)',
                 fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig('docs/images/funnel_waterfall.png', dpi=300)
    plt.close()
    print("Saved docs/images/funnel_waterfall.png")


def chart_cohort_vintages():
    """Figure 2: Cohort Vintage Maturation Curves."""
    df = pd.read_csv(f"{MARTS_DIR}/mart_cohort_vintage.csv")
    
    fig, ax1 = plt.subplots(figsize=(11, 5.5))
    ax1.plot(df['orig_year'], df['cumulative_charge_off_rate'] * 100, marker='s', color='#c0392b', linewidth=2.8, label='Nominal Write-off Rate (% Funded)')
    ax1.plot(df['orig_year'], df['current_rate'] * 100, marker='o', color='#2980b9', linewidth=2.8, linestyle='--', label='Active / Current Ratio (% Funded)')
    
    ax1.axvspan(2016.5, 2018.5, color='#f1c40f', alpha=0.18, label='Unseasoned Cohorts (Right-Censored)')
    ax1.set_xlabel('Origination Vintage Year', fontweight='bold')
    ax1.set_ylabel('Percentage of Cohort Volume (%)', fontweight='bold', color='#2c3e50')
    ax1.set_title('Cohort Maturation Analysis: Loss Curves Distorted by Loan Seasoning (2007–2018)',
                 fontsize=13, fontweight='bold', pad=15)
    ax1.legend(loc='center left', frameon=True)
    ax1.set_xticks(df['orig_year'])
    plt.tight_layout()
    plt.savefig('docs/images/cohort_vintage_curves.png', dpi=300)
    plt.close()
    print("Saved docs/images/cohort_vintage_curves.png")


def chart_approval_odds_ratios():
    """Figure 3: Econometric Odds Ratios from Logistic Regression."""
    driver_data = [
        {"Driver": "Auto Financing", "Odds_Ratio": 0.167, "Color": "#e74c3c"},
        {"Driver": "Small Business", "Odds_Ratio": 0.223, "Color": "#e74c3c"},
        {"Driver": "Medical Expenses", "Odds_Ratio": 0.353, "Color": "#e74c3c"},
        {"Driver": "Major Purchase", "Odds_Ratio": 0.584, "Color": "#e74c3c"},
        {"Driver": "Home Improvement", "Odds_Ratio": 0.626, "Color": "#e74c3c"},
        {"Driver": "Debt-To-Income (+10% DTI)", "Odds_Ratio": 0.776, "Color": "#e74c3c"},
        {"Driver": "Requested Ticket (+$5,000)", "Odds_Ratio": 0.951, "Color": "#e74c3c"},
        {"Driver": "Employment Tenure (+1 yr)", "Odds_Ratio": 1.484, "Color": "#27ae60"},
        {"Driver": "Credit Card Refinance", "Odds_Ratio": 1.718, "Color": "#27ae60"},
        {"Driver": "Bureau Score (+50 pts)", "Odds_Ratio": 2.523, "Color": "#27ae60"}
    ]
    df = pd.DataFrame(driver_data)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    bars = ax.barh(df['Driver'], df['Odds_Ratio'], color=df['Color'], edgecolor='black', linewidth=0.7, alpha=0.88)
    ax.axvline(1.0, color='black', linestyle='--', linewidth=1.2, label='Neutral Odds (OR = 1.0)')
    
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.05, bar.get_y() + bar.get_height()/2, f"{width:.2f}x",
                va='center', ha='left', fontsize=10, fontweight='bold', color='#2c3e50')

    ax.set_xlim(0, 3.0)
    ax.set_xlabel('Odds Ratio of Underwriting Approval (Reference: Debt Consolidation)', fontweight='bold')
    ax.set_title('Underwriting Approval Drivers: Econometric Odds Ratios (AUC = 0.9348)',
                 fontsize=13, fontweight='bold', pad=15)
    ax.legend(loc='lower right')
    plt.tight_layout()
    plt.savefig('docs/images/approval_odds_ratios.png', dpi=300)
    plt.close()
    print("Saved docs/images/approval_odds_ratios.png")


def chart_segment_matrix():
    """Figure 4: 2x2 Segment Value Matrix."""
    df = pd.read_csv(f"{MARTS_DIR}/mart_segment_risk_return.csv")
    
    fig, ax = plt.subplots(figsize=(11, 6))
    scatter = ax.scatter(
        df['approval_rate'] * 100,
        df['charge_off_rate'] * 100,
        s=df['applied_count'] / 15000,
        c=df['charge_off_rate'] * 100,
        cmap='coolwarm',
        alpha=0.75,
        edgecolor='black',
        linewidth=0.8
    )
    
    ax.axvline(7.56, color='black', linestyle='--', linewidth=1.2, label='Portfolio Avg Approval (7.56%)')
    ax.axhline(16.0, color='red', linestyle='--', linewidth=1.2, label='Benchmark Default Rate (16.0%)')
    
    # Quadrant annotations
    ax.text(2.0, 8.0, "QUADRANT II:\nGrowth Goldmine\n(Low Approval, Low Default)", fontsize=11, fontweight='bold', color='#1e8449', bbox=dict(facecolor='white', alpha=0.8, edgecolor='#1e8449'))
    ax.text(18.0, 8.0, "QUADRANT I:\nPrime Core\n(High Approval, Low Default)", fontsize=11, fontweight='bold', color='#2e86c1', bbox=dict(facecolor='white', alpha=0.8, edgecolor='#2e86c1'))
    ax.text(18.0, 24.0, "QUADRANT IV:\nLeakage Danger Zone\n(High Approval, High Default)", fontsize=11, fontweight='bold', color='#c0392b', bbox=dict(facecolor='white', alpha=0.8, edgecolor='#c0392b'))
    ax.text(2.0, 24.0, "QUADRANT III:\nSubprime Gate\n(Appropriate Rejections)", fontsize=11, fontweight='bold', color='#7d3c98', bbox=dict(facecolor='white', alpha=0.8, edgecolor='#7d3c98'))

    ax.set_xlabel('Underwriting Approval Rate (%)', fontweight='bold')
    ax.set_ylabel('Realized Charge-Off Rate (% Funded)', fontweight='bold')
    ax.set_title('Segment Value Matrix: Identifying Growth Opportunities vs Risk Leakage',
                 fontsize=13, fontweight='bold', pad=15)
    ax.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig('docs/images/segment_risk_return_quadrants.png', dpi=300)
    plt.close()
    print("Saved docs/images/segment_risk_return_quadrants.png")


if __name__ == "__main__":
    chart_funnel()
    chart_cohort_vintages()
    chart_approval_odds_ratios()
    chart_segment_matrix()
