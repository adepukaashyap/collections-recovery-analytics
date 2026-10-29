#!/usr/bin/env python3
"""Estimate intent-to-treat effects only after genuine pilot outcomes are supplied."""
from pathlib import Path
import pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parents[1]; TPL=ROOT/'data/templates/pilot_results_template.csv'; EXP=ROOT/'data/experiment/pilot_results.csv'; REPORTS=ROOT/'reports'; OUT=ROOT/'data/processed'
required={'eligible_flag','randomization_arm','net_cash_30d_inr','treatment_cost_30d_inr'}
if not EXP.exists():
    pd.DataFrame(columns=pd.read_csv(TPL,nrows=0).columns).to_csv(EXP,index=False)
d=pd.read_csv(EXP,low_memory=False)
result={'status':'NOT_RUN','reason':'No populated randomized pilot outcomes supplied','n_control':0,'n_treatment':0,'cash_lift_per_eligible_inr':None,'cash_lift_ci95_low_inr':None,'cash_lift_ci95_high_inr':None,'cost_lift_per_eligible_inr':None,'net_benefit_lift_per_eligible_inr':None,'causal_roi_pct':None}
if len(d)>0 and required.issubset(d.columns):
    d['eligible_flag']=d.eligible_flag.astype('string').str.lower().isin(['true','1','yes','eligible'])
    d=d.loc[d.eligible_flag & d.randomization_arm.astype('string').str.lower().isin(['control','treatment'])].copy()
    for col in ['net_cash_30d_inr','treatment_cost_30d_inr']:
        d[col]=pd.to_numeric(d[col],errors='coerce')
    d=d.dropna(subset=['net_cash_30d_inr','treatment_cost_30d_inr'])
    c=d[d.randomization_arm.astype(str).str.lower().eq('control')]; t=d[d.randomization_arm.astype(str).str.lower().eq('treatment')]
    if len(c)>=2 and len(t)>=2:
        cash_lift=float(t.net_cash_30d_inr.mean()-c.net_cash_30d_inr.mean())
        cost_lift=float(t.treatment_cost_30d_inr.mean()-c.treatment_cost_30d_inr.mean())
        se=float(np.sqrt(t.net_cash_30d_inr.var(ddof=1)/len(t)+c.net_cash_30d_inr.var(ddof=1)/len(c)))
        lo=cash_lift-1.96*se; hi=cash_lift+1.96*se
        net_lift=cash_lift-cost_lift
        result={'status':'ESTIMATED_FROM_SUPPLIED_PILOT','reason':'Unadjusted intent-to-treat difference; approximate 95% normal CI; review skew/strata and pre-registered analysis before decision','n_control':len(c),'n_treatment':len(t),'cash_lift_per_eligible_inr':cash_lift,'cash_lift_ci95_low_inr':lo,'cash_lift_ci95_high_inr':hi,'cost_lift_per_eligible_inr':cost_lift,'net_benefit_lift_per_eligible_inr':net_lift,'causal_roi_pct':(net_lift/cost_lift*100 if cost_lift>0 else None)}
OUT.mkdir(exist_ok=True,parents=True); pd.DataFrame([result]).to_csv(OUT/'counterfactual_pilot_estimate.csv',index=False)
if result['status']=='NOT_RUN':
    status_html='''<div class="panel warning"><h2>Status: not run</h2><p>No genuine randomized treatment/control outcome data are populated. This is intentional; no causal effect or causal ROI is fabricated.</p><p>Populate <code>data/experiment/pilot_results.csv</code> only after approved randomization and the 30-day outcome window, then run <code>python src/analyze_counterfactual_pilot.py</code>.</p></div>'''
else:
    status_html=f'''<div class="panel"><h2>Estimate from supplied pilot data</h2><p>Control n={result['n_control']:,}; treatment n={result['n_treatment']:,}.</p><p>Cash lift per eligible account: ₹{result['cash_lift_per_eligible_inr']:,.2f}; approximate 95% CI ₹{result['cash_lift_ci95_low_inr']:,.2f} to ₹{result['cash_lift_ci95_high_inr']:,.2f}.</p><p>Cost lift per eligible account: ₹{result['cost_lift_per_eligible_inr']:,.2f}; net-benefit lift: ₹{result['net_benefit_lift_per_eligible_inr']:,.2f}.</p><p>ROI is reported only when incremental treatment cost is positive; adjust for strata, heavy tails, clustering, and pre-registered estimands before using for a funding decision.</p></div>'''
page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Counterfactual Pilot Estimate</title><link rel="stylesheet" href="investment_business_case.css"></head><body><header><p class="eyebrow">CAUSAL MEASUREMENT · RESULTS GATE</p><h1>Randomized targeting pilot estimate</h1><p>Results are computed only from populated, eligible treatment/control pilot records.</p><span class="pill">No invented lift</span></header><main>'''+status_html+'''<section class="panel"><h2>Analysis contract</h2><p>Primary outcome: 30-day net cash per eligible account, intent-to-treat. Report treatment-control difference, uncertainty, incremental cost and guardrails. The current script provides a basic unadjusted estimate; final decision analysis should include pre-registered stratification, clustering and distribution-robust inference where appropriate.</p></section><p><a href="counterfactual_readiness.html">Back to pilot readiness</a></p></main></body></html>'''
(REPORTS/'counterfactual_pilot_estimate.html').write_text(page,encoding='utf-8')
print(f"Counterfactual estimator status: {result['status']}")
