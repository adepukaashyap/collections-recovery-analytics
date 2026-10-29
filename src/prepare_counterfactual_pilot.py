#!/usr/bin/env python3
"""Create a pilot planning frame; this is NOT an executed experiment or causal result."""
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; PROC=ROOT/'data/processed'; RAW=ROOT/'data/raw'; EXP=ROOT/'data/experiment'; TPL=ROOT/'data/templates'; REPORTS=ROOT/'reports'
EXP.mkdir(exist_ok=True,parents=True); TPL.mkdir(exist_ok=True,parents=True)
a=pd.read_csv(PROC/'accounts_canonical.csv',low_memory=False)
# Add a transparent balance band for future stratification; eligibility is deliberately not inferred.
balance=pd.to_numeric(a.get('outstanding_amount'),errors='coerce')
a['balance_band']=pd.cut(balance,[-float('inf'),10000,50000,200000,float('inf')],labels=['<=10k','10k-50k','50k-200k','>200k']).astype('string').fillna('UNKNOWN')
a['dpd_band']=pd.cut(pd.to_numeric(a.get('dpd'),errors='coerce'),[-float('inf'),0,30,60,90,float('inf')],labels=['<=0','1-30','31-60','61-90','>90']).astype('string').fillna('UNKNOWN')
frame=a[['account_id','borrower_id','loan_type','risk_segment','status','dpd','dpd_band','balance_band']].copy()
frame['eligibility_status']='REVIEW_REQUIRED'
frame['eligibility_reason']='Eligibility rules not approved; do not randomize until Collections/Compliance sign-off'
frame['randomization_unit']='account; consider borrower-level if linked accounts can spill over'
frame['assigned_arm']=''
frame['assignment_timestamp']=''
frame['treatment_delivered']=''
frame['first_exposure_timestamp']=''
frame['outcome_window_start']=''
frame['outcome_window_end']=''
frame['net_cash_30d_inr']=''
frame['treatment_cost_30d_inr']=''
frame['complaint_flag_30d']=''
frame['opt_out_flag_30d']=''
frame['wrong_party_contact_flag_30d']=''
frame['ptp_broken_flag_30d']=''
frame['exclusion_reason']=''
frame.to_csv(EXP/'pilot_assignment_and_outcome_template.csv',index=False)
cols=['account_id','borrower_id','loan_type','risk_segment','dpd','dpd_band','balance_band','eligible_flag','eligibility_reason','randomization_arm','assignment_timestamp','treatment_delivered','first_exposure_timestamp','outcome_window_start','outcome_window_end','net_cash_30d_inr','treatment_cost_30d_inr','complaint_flag_30d','opt_out_flag_30d','wrong_party_contact_flag_30d','ptp_broken_flag_30d','exclusion_reason']
pd.DataFrame(columns=cols).to_csv(TPL/'pilot_results_template.csv',index=False)
html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Counterfactual Pilot Readiness</title><link rel="stylesheet" href="investment_business_case.css"></head><body><header><p class="eyebrow">CAUSAL MEASUREMENT · PILOT READINESS</p><h1>Targeting pilot: ready-to-populate design</h1><p>This is a design and data-capture template, not a completed experiment.</p><span class="pill">Causal effect not measured</span></header><main><section class="panel"><h2>What has been prepared</h2><ul><li>Account-level planning frame with risk, DPD and balance strata.</li><li>Eligibility is deliberately marked REVIEW_REQUIRED; no assignment is made before business/Compliance rules are signed.</li><li>Outcome columns capture 30-day net cash, intervention cost and customer-protection guardrails.</li><li>Blank analysis template for treatment/control estimates and uncertainty.</li></ul></section><section class="panel"><h2>Run protocol</h2><ol><li>Approve eligibility and remove legal holds, disputes and restricted contacts.</li><li>Freeze the eligible population and decide account vs borrower randomization.</li><li>Randomize 50/50 within strata using a recorded seed and immutable assignment table.</li><li>Log actual delivery/exposure and all costs; do not infer treatment from a recommendation.</li><li>After 30 days, populate outcomes and run the pre-registered intent-to-treat analysis.</li></ol></section><section class="panel warning"><h2>Do not report a causal lift yet</h2><p>The provided dataset has no randomized arm, confirmed treatment exposure, 30-day experiment outcomes or intervention costs. Retrospective channel association is not a causal effect. A numeric sample size also requires an outcome variance and minimum economically meaningful effect.</p></section><p><a href="../docs/counterfactual_design.md">Open full counterfactual design</a></p></main></body></html>'''
(REPORTS/'counterfactual_readiness.html').write_text(html,encoding='utf-8')
print(f'Pilot planning template created for {len(frame):,} accounts. Eligibility and assignment intentionally remain blank pending approval.')
