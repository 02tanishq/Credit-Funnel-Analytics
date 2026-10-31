# Executive Memo: Lending Product Funnel & Approval Analysis

**To:** Investment Committee & Retail Credit Risk Policy Group (Bajaj Finance Context)  
**From:** Senior Product Analyst / Data Engineer  
**Date:** October 31, 2026  
**Subject:** End-to-End Funnel Conversion, Underwriting Econometrics, Portfolio Vintages & Underwriting Policy Scenarios  
**Dataset & Scope:** 29,909,409 Lending Club Applications (2007–2018) | Exactly Reconciled (0.00% Discrepancy)

---

## 1. Executive Summary & Pipeline Disbursal Metrics

Out of **29,909,409 total applications** submitted between May 2007 and December 2018, only **2,260,668 were approved and funded**, representing an overall pipeline pass-through rate of **7.56%** (`sql/01_stage_conversion_rates.sql`). The remaining **27,648,741 applicants (92.44%)** were dropped at the underwriting gate.

| Pipeline Stage | Total Contracts ($N$) | Stage Conversion Rate | Cumulative Conversion | Primary Risk / Operational Dynamic |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1: Applied (Inflow)** | 29,909,409 | 100.00% | 100.00% | Raw customer demand across digital channels |
| **Stage 2: Approved & Funded** | 2,260,668 | **7.56%** | **7.56%** | Effective funded loans (*approved-but-abandoned unrecorded*) |
| **Stage 3a: Fully Paid** | 1,078,739 | 47.72% | 3.61% | Principal + contracted interest successfully recovered |
| **Stage 3b: Current (Active)** | 886,753 | 39.23% | 2.96% | Active performing book (heavily concentrated in 2017–2018) |
| **Stage 3c: Late (PAR 15–120)** | 25,816 | 1.14% | 0.09% | Early/mid delinquency portfolio at risk |
| **Stage 3d: Charged Off (Loss)** | 269,360 | **11.92%** | **0.90%** | Cumulative principal default write-offs |

---

## 2. Key Analytical & Econometric Insights

### Insight 1: Steepest Funnel Drop-off Occurs at the DTI Underwriting Gate (`sql/02_segment_dropoff_confidence_intervals.sql`)
- Applicants with Debt-To-Income (DTI) ratios between **0–10%** achieve an approval rate of **24.18%** (95% Wilson Score CI: `[24.13%, 24.23%]`, $N = 2,525,658$).
- Conversely, applicants in the **>40% DTI band** collapse to an approval rate of **0.39%** (95% CI: `[0.38%, 0.40%]`, $N = 3,598,624$).
- A two-sample pooled z-test confirms this difference is statistically significant ($z = 328.4$, $p < 10^{-300}$).
- **Institutional Context:** In rejected files, **1,203,063 records** have a recorded DTI of `-1%`, which indicates uncomputable income / thin-file knockout.

### Insight 2: Bureau Score Pulling Reflects a Two-Stage Knockout Hurdle (`sql/03_approval_drivers_summary.sql`)
- In the rejected dataset, **66.90% (18,497,630 records)** have null credit scores. Lending Club implemented a cost-saving knockout rule: applicants failing basic geographic or income verification were rejected before incurring third-party credit bureau API inquiry costs.
- Among scored applicants ($N = 95,452$ balanced sample, AUC = 0.9348, Pseudo $R^2 = 0.4523$):
  - **FICO Elasticity:** Each 50-point increase in risk score multiplies approval odds by **2.52x** (Odds Ratio = 2.523, 95% CI: `[2.466, 2.582]`, $p < 10^{-300}$).
  - **Employment Anchor:** Each additional year of verified job stability increases approval odds by **+48.4%** (Odds Ratio = 1.484, 95% CI: `[1.475, 1.494]`, $p < 10^{-300}$).
  - **DTI Friction:** Each +10% increase in DTI suppresses approval odds by **-22.4%** (Odds Ratio = 0.776, 95% CI: `[0.765, 0.788]`, $p < 10^{-200}$).
  - **Purpose Penalty:** Small Business loan applications face an **88% lower odds** of approval than consumer debt consolidation (Odds Ratio = 0.223, 95% CI: `[0.184, 0.271]`, $p < 10^{-50}$).

### Insight 3: Maturation Lag & Right-Censoring Distort Recent Cohorts (`sql/04_cohort_vintage_analysis.sql`)
- Nominal cumulative charge-off rates for **2018 (1.79%)** and **2017 (8.83%)** appear misleadingly pristine compared to **2014 (17.47%)** and **2015 (18.00%)**.
- This is entirely driven by right-censoring: **86.85% of 2018 loans** and **59.69% of 2017 loans** remain active contracts (`Current`).
- Evaluating mature resolved loans (`Charged Off / (Fully Paid + Charged Off)`), the true terminal credit loss benchmark across mature cohorts is **18.4%–20.2%**.

### Insight 4: Quadrant Misallocation in Small Business vs Debt Consolidation (`sql/05_segment_risk_value_matrix.sql`)
- Unsecured Small Business loans $> \$25,000$ exhibit a **24.5% realized default rate** (Quadrant IV: High Approval, High Risk).
- Conversely, Debt Consolidation applicants with DTI 20–30% and $\ge 5$ years employment exhibit high rejection (~85%) despite a modest **14.0% default rate** upon approval (Quadrant II: Growth Goldmine).

---

## 3. Product & Underwriting Policy Recommendations

| Recommendation | Proposed Policy Intervention | Target Population | Projected Incremental Volume | Expected Credit Losses | Key Downside Risks & Mitigations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Near-Prime Tiered DTI Bridge** | Relax blunt DTI gate from 20% to 28% for established wage earners ($\ge 5$ yrs employment) seeking debt consolidation. | 513,056 qualified rejected applicants | **+\$1.25B Disbursed** (+92,350 funded loans at 18% pass rate) | **\$148.9M to \$236.5M** (11.9% to 18.9% loss rate across sensitivity tiers) | **Risk:** Adverse selection in higher DTI tier.<br>**Mitigation:** Cap ticket sizes at \$15k; require NACH direct debit mandate. |
| **2. High-Ticket Small Business Tightening** | Cap unsecured Small Business loans at \$20,000 and mandate a minimum FICO of 720. | 4,788 high-ticket approved contracts | **-\$39.6M Exposure** (-1,197 volatile high-ticket loans) | **+\$8.5M Capital Preserved** (Avoided write-offs at 21.5% base loss rate) | **Risk:** Drop-off of prime small business owners.<br>**Mitigation:** Offer secured asset-backed credit line as a cross-sell alternative. |

*Note: All projections represent scenario sensitivity ranges (Pessimistic, Base Case, Optimistic) as detailed in `sql/06_scenario_policy_simulations.sql` and `src/scenario.py`.*

---

## 4. Interview Preparation: The 5 Critical Vulnerabilities & Defenses

When defending this analytics project in an interview with senior leadership at an Indian NBFC (Bajaj Finance), be prepared to address these five specific limitations:

1. **Vulnerability: Approved vs Funded Conflation (Omitted Offer Abandonment)**  
   *Interviewer Question:* *"You report an approval rate of 7.56%, but isn't that actually a disbursal rate? What happened to sanctioned borrowers who declined the APR?"*  
   *Candidate Defense:* "Yes, exactly. In Indian NBFC terms, Stage 2 here measures Disbursal Conversion rather than Sanction Conversion. The public Lending Club schema records accepted loans only after they are fully funded and issued on the exchange. If we had offer-stage data, we could isolate underwriting rejection from customer pricing abandonment, which is vital for optimizing our product pricing elasticity."

2. **Vulnerability: Missing Bureau Scores in Rejected Data (Knockout Truncation Bias)**  
   *Interviewer Question:* *"You ran logistic regression with risk scores, but 67% of rejected applicants don't have one. Doesn't that introduce severe truncation bias?"*  
   *Candidate Defense:* "Yes. Lending Club operated a sequential two-stage hurdle: applicants who failed pre-qualification knockout criteria (unserviceable DTI, zero self-reported income, unserviceable geography) were rejected immediately without paying credit bureau API pull fees. Rather than imputing fake bureau scores onto thin-file rejects, we audited `has_risk_score` as an explicit indicator of passing the pre-screen and estimated our continuous scoring model strictly on the scored population (AUC = 0.935)."

3. **Vulnerability: Right-Censoring in 2017–2018 Cohorts**  
   *Interviewer Question:* *"Why did your vintage analysis show 2018 having only a 1.79% default rate? Did underwriting quality dramatically improve?"*  
   *Candidate Defense:* "No, that is a classic right-censoring pitfall. As shown in `sql/04_cohort_vintage_analysis.sql`, 86.85% of 2018 loans were still active and performing at snapshot time. Because 36-month and 60-month contracts experience peak charge-offs between months 12 and 24, unseasoned cohorts appear deceptively healthy. We avoided this error by benchmarking policy decisions against mature 2013–2015 cohorts where over 95% of contracts are closed."

4. **Vulnerability: Counterfactual Uncertainty on Rejected Borrowers (Reject Inference)**  
   *Interviewer Question:* *"How can you recommend expanding into rejected DTI segments when you have zero repayment data on those rejected applicants?"*  
   *Candidate Defense:* "This is the classic credit risk 'reject inference' dilemma. Because counterfactual performance cannot be observed directly, we explicitly avoided single-point deterministic forecasts. Instead, our scenario simulator in `src/scenario.py` stress-tested the intervention with a +35% relative default surge (18.9% loss rate) in the pessimistic tier. The recommendation remains profitable only because high-tenure employment provides an anchoring proxy for income recovery."

5. **Vulnerability: Macroeconomic Shifts Across the 11-Year Window (2007–2018)**  
   *Interviewer Question:* *"Your dataset spans the 2008 Global Financial Crisis through peak fintech expansion. How did you control for structural macroeconomic regime changes?"*  
   *Candidate Defense:* "Credit standards and risk appetites fluctuated significantly—2007–2008 loans experienced over 20% write-offs before Lending Club tightened criteria. To control for this, our SQL marts (`mart_cohort_vintage.csv` and `mart_funnel_by_segment.csv`) segment all conversion and loss metrics by origination vintage year, ensuring underwriting comparisons are anchored within homogenous operational regimes."
