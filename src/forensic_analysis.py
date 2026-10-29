"""Reproducible forensic checks for Collections Recovery Analytics.

Important: timezone, vendor-code, identity and denominator findings are sensitivity/audit
signals, not definitive corrections where source contracts are absent.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; RAW=ROOT/'data/raw'; OUT=ROOT/'data/processed'; REPORTS=ROOT/'reports'
OUT.mkdir(exist_ok=True,parents=True); REPORTS.mkdir(exist_ok=True,parents=True)
def read(n): return pd.read_csv(RAW/f'{n}.csv',low_memory=False)
def save(df,name): df.to_csv(OUT/name,index=False); return df

def payments_audit():
    p=read('payments'); p['amount_num']=pd.to_numeric(p.amount,errors='coerce').fillna(0); p['payment_status_norm']=p.payment_status.astype('string').str.upper().str.strip(); p['event_at_parsed']=pd.to_datetime(p.event_at,errors='coerce')
    p['reference_norm']=p.payment_reference.astype('string').str.strip(); p.loc[p.reference_norm.eq(''),'reference_norm']=pd.NA
    raw_success=p.loc[p.payment_status_norm.eq('SUCCESS'),'amount_num'].sum()
    # Mirror the production pipeline's documented deterministic rule exactly:
    # on duplicate payment_id/timestamp ties, prefer populated payment references;
    # then keep the latest event per transaction reference. This prevents the
    # forensic summary from silently reporting a different canonical population.
    p['_reference_present']=p.reference_norm.notna()
    by_id=p.sort_values(['event_at_parsed','_reference_present','reference_norm'],na_position='first').drop_duplicates('payment_id',keep='last')
    by_ref=by_id.copy(); by_ref['transaction_key']=by_ref.reference_norm.fillna('MISSING_REF:'+by_ref.payment_id.astype(str)); by_ref=by_ref.sort_values('event_at_parsed',na_position='first').drop_duplicates('transaction_key',keep='last')
    by_ref['effective_amount']=np.where(by_ref.payment_status_norm.eq('SUCCESS'),by_ref.amount_num,0)
    canonical=by_ref[['payment_id','account_id','borrower_id','event_at','payment_reference','amount','payment_status','payment_method','provider_id','transaction_key','effective_amount']]
    canonical.to_csv(OUT/'payments_canonical_forensic.csv',index=False)
    ref=p.loc[p.reference_norm.notna()].groupby('reference_norm').agg(rows=('payment_id','size'),payment_ids=('payment_id','nunique'),statuses=('payment_status_norm','nunique'),amounts=('amount_num','nunique'),accounts=('account_id','nunique'),min_event=('event_at_parsed','min'),max_event=('event_at_parsed','max')).reset_index()
    ref=ref.loc[(ref.rows>1)].copy(); ref['conflict_flag']=(ref.statuses>1)|(ref.amounts>1)|(ref.accounts>1); save(ref,'payment_reference_conflicts.csv')
    rows=[('raw_payment_rows',len(p)),('raw_success_amount_before_dedup_inr',float(raw_success)),('rows_after_payment_id_dedup',len(by_id)),('rows_after_transaction_reference_dedup',len(by_ref)),('canonical_effective_success_amount_inr',float(by_ref.effective_amount.sum())),('raw_success_event_amount_minus_canonical_effective_cash_inr',float(raw_success-by_ref.effective_amount.sum())),('duplicate_reference_groups',int(len(ref))),('conflicting_reference_groups',int(ref.conflict_flag.sum())),('missing_or_blank_reference_rows',int(p.reference_norm.isna().sum())),('same_timestamp_duplicate_payment_id_groups',int((p.groupby('payment_id').event_at_parsed.nunique(dropna=False).eq(1)&p.payment_id.duplicated(keep=False).groupby(p.payment_id).transform('any')).sum()))]
    return pd.DataFrame(rows,columns=['metric','value'])

def timezone_audit():
    c=read('calls'); c['event_at_parsed']=pd.to_datetime(c.event_at,errors='coerce'); c['timezone']=c.timezone.fillna('UNKNOWN').astype(str)
    # No source contract tells us whether naive timestamps are local wall time or UTC.
    # Quantify sensitivity by interpreting each naive timestamp as the listed local zone, then converting to UTC.
    offsets={'UTC':0,'Asia/Kolkata':330,'Asia/Dubai':240}
    c['assumed_offset_min']=c.timezone.map(offsets)
    c['hour_if_naive_utc']=c.event_at_parsed.dt.hour
    c['hour_if_listed_timezone_to_utc']=(c.event_at_parsed.dt.hour-c.assumed_offset_min/60)%24
    c['hour_changes_under_sensitivity']=c.hour_if_naive_utc.ne(c.hour_if_listed_timezone_to_utc)
    c['date_if_naive_utc']=c.event_at_parsed.dt.strftime('%Y-%m-%d')
    shifted=c.event_at_parsed-pd.to_timedelta(c.assumed_offset_min,unit='m')
    c['date_if_listed_timezone_to_utc']=shifted.dt.strftime('%Y-%m-%d')
    c['date_changes_under_sensitivity']=c.date_if_naive_utc.ne(c.date_if_listed_timezone_to_utc)
    save(c[['call_id','event_at','timezone','hour_if_naive_utc','hour_if_listed_timezone_to_utc','hour_changes_under_sensitivity','date_if_naive_utc','date_if_listed_timezone_to_utc','date_changes_under_sensitivity']],'timezone_sensitivity_audit.csv')
    return pd.DataFrame([{'audit':'calls timezone sensitivity','rows':len(c),'rows_with_hour_changed':int(c.hour_changes_under_sensitivity.sum()),'pct_with_hour_changed':round(100*c.hour_changes_under_sensitivity.mean(),3),'rows_with_date_changed':int(c.date_changes_under_sensitivity.sum()),'pct_with_date_changed':round(100*c.date_changes_under_sensitivity.mean(),3),'interpretation':'Sensitivity only; source timestamp semantics are undocumented'}])

def vendor_mapping_audit():
    d=read('call_dispositions'); d['event_at']=pd.to_datetime(d.event_at,errors='coerce'); calls=read('calls')[['call_id','vendor_id','event_at']].rename(columns={'event_at':'call_event_at'}); d=d.merge(calls,on='call_id',how='left',suffixes=('','_call')); d['month']=d.event_at.dt.to_period('M').astype(str); d['disposition_code_norm']=d.disposition_code.astype('string').str.upper().str.strip()
    counts=d.groupby(['vendor_id','disposition_version','disposition_code_norm','month'],dropna=False).size().rename('rows').reset_index(); totals=d.groupby(['vendor_id','disposition_version','month'],dropna=False).size().rename('version_month_rows').reset_index(); counts=counts.merge(totals,on=['vendor_id','disposition_version','month'],how='left'); counts['share_within_vendor_version_month_pct']=100*counts.rows/counts.version_month_rows
    save(counts,'vendor_disposition_code_trends.csv')
    # Explicitly surface likely semantic aliases; this is a review queue, not an approved mapping.
    aliases={'PROMISE_TO_PAY':'PTP','PAID':'SUCCESS','NO_CONTACT':'NO_CONTACT','PTP_BROKEN':'PTP_BROKEN'}
    d['candidate_normalized_family']=d.disposition_code_norm.map(aliases).fillna(d.disposition_code_norm)
    review=d.groupby(['vendor_id','disposition_version','disposition_code_norm','candidate_normalized_family'],dropna=False).size().rename('rows').reset_index(); save(review,'vendor_disposition_mapping_review.csv')
    return pd.DataFrame([{'metric':'disposition_rows', 'value':len(d)},{'metric':'distinct_vendor_version_code_combinations','value':len(review)},{'metric':'vendors_with_multiple_disposition_versions','value':int(d.groupby('vendor_id').disposition_version.nunique().gt(1).sum())},{'metric':'warning','value':'No vendor mapping effective dates or approved crosswalk supplied; trends cannot prove a mapping change'}])

def agent_identity_audit():
    a=read('agents').copy(); a['employee_code_norm']=a.employee_code.astype('string').str.strip().str.upper(); a['agent_id_norm']=a.agent_id.astype('string').str.strip().str.upper()
    emp=a.groupby('employee_code_norm').agg(rows=('agent_id','size'),distinct_agent_ids=('agent_id_norm','nunique'),distinct_names=('agent_name','nunique'),distinct_vendors=('vendor_id','nunique'),distinct_join_dates=('joined_at','nunique')).reset_index(); emp['identity_conflict_flag']=(emp.distinct_agent_ids>1)&((emp.distinct_names>1)|(emp.distinct_vendors>1)|(emp.distinct_join_dates>1)); save(emp,'agent_employee_code_conflicts.csv')
    aid=a.groupby('agent_id_norm').agg(rows=('employee_code_norm','size'),distinct_employee_codes=('employee_code_norm','nunique'),distinct_names=('agent_name','nunique'),distinct_vendors=('vendor_id','nunique')).reset_index(); aid['identity_conflict_flag']=(aid.distinct_employee_codes>1)| (aid.distinct_names>1)|(aid.distinct_vendors>1); save(aid,'agent_id_conflicts.csv')
    return pd.DataFrame([{'metric':'raw_agent_rows','value':len(a)},{'metric':'unique_agent_ids','value':a.agent_id.nunique()},{'metric':'employee_codes_linked_to_multiple_agent_ids','value':int(emp.distinct_agent_ids.gt(1).sum())},{'metric':'employee_code_conflict_groups','value':int(emp.identity_conflict_flag.sum())},{'metric':'agent_ids_linked_to_multiple_employee_codes','value':int(aid.distinct_employee_codes.gt(1).sum())},{'metric':'agent_id_conflict_groups','value':int(aid.identity_conflict_flag.sum())}])

def denominator_audit():
    a=read('accounts'); h=read('account_status_history'); h['event_at']=pd.to_datetime(h.event_at,errors='coerce'); h['recorded_at']=pd.to_datetime(h.recorded_at,errors='coerce'); h=h.sort_values(['event_at','recorded_at'],na_position='first')
    first=h.groupby('account_id').agg(first_history_event=('event_at','min'),last_history_event=('event_at','max'),history_rows=('history_id','count'),distinct_statuses=('status','nunique')).reset_index()
    last=h.drop_duplicates('account_id',keep='last')[['account_id','status','event_at']].rename(columns={'status':'last_history_status','event_at':'last_history_event_at'})
    x=a[['account_id','status','opened_at','outstanding_amount','principal_amount']].merge(first,on='account_id',how='left').merge(last,on='account_id',how='left'); x['no_status_history']=x.history_rows.isna(); x['current_status_norm']=x.status.astype('string').str.upper(); x['history_status_norm']=x.last_history_status.astype('string').str.upper(); x['current_vs_last_history_disagree']=x.current_status_norm.ne(x.history_status_norm)&x.history_status_norm.notna(); save(x,'denominator_status_disappearance_audit.csv')
    summ=x.groupby('current_status_norm',dropna=False).agg(accounts=('account_id','nunique'),accounts_with_history=('history_rows',lambda z:int(z.notna().sum())),accounts_without_history=('no_status_history','sum'),status_disagreements=('current_vs_last_history_disagree','sum')).reset_index(); save(summ,'denominator_status_summary.csv')
    return pd.DataFrame([{'metric':'accounts','value':len(a)},{'metric':'accounts_with_no_status_history','value':int(x.no_status_history.sum())},{'metric':'accounts_whose_snapshot_status_differs_from_latest_history','value':int(x.current_vs_last_history_disagree.sum())},{'metric':'warning','value':'Snapshot status is not a historical eligible-population denominator; status history must be contract-validated'}])

def population_mix_audit():
    g=pd.read_csv(OUT/'golden_dataset_account_month.csv',low_memory=False); g['month']=g.month.astype(str)
    rows=[]
    for col in ['risk_segment','loan_type','status','timezone']:
        if col not in g: continue
        counts=g.groupby(['month',col],dropna=False).account_id.nunique().rename('accounts').reset_index(); totals=counts.groupby('month').accounts.transform('sum'); counts['share_pct']=100*counts.accounts/totals; counts['dimension']=col; counts=counts.rename(columns={col:'category'}); rows.append(counts[['month','dimension','category','accounts','share_pct']])
    mix=pd.concat(rows,ignore_index=True); save(mix,'population_mix_monthly.csv')
    # Simpson-style diagnostic: aggregate vs within-stratum direction for risk segment.
    risk=g.groupby(['month','risk_segment']).agg(accounts=('account_id','nunique'),recovered_amount=('recovered_amount','sum')).reset_index(); risk['amount_per_account']=risk.recovered_amount/risk.accounts.replace(0,np.nan)
    pivot=risk.pivot(index='risk_segment',columns='month',values='amount_per_account'); months=sorted(risk.month.unique()); records=[]
    for i in range(1,len(months)):
        prev,cur=months[i-1],months[i]; common=pivot[[prev,cur]].dropna(); improved=(common[cur]>common[prev]).sum(); worsened=(common[cur]<common[prev]).sum()
        agg=g.groupby('month').agg(amount=('recovered_amount','sum'),accounts=('account_id','nunique')); agg_growth=(agg.loc[cur,'amount']/agg.loc[prev,'amount']-1)*100 if agg.loc[prev,'amount'] else np.nan
        records.append({'prior_month':prev,'current_month':cur,'aggregate_amount_growth_pct':agg_growth,'risk_segments_compared':len(common),'risk_segments_improved_amount_per_account':int(improved),'risk_segments_declined_amount_per_account':int(worsened),'direction_disagreement_flag':bool((agg_growth>0 and worsened>improved) or (agg_growth<0 and improved>worsened)),'interpretation':'Diagnostic only; not a formal causal or significance test'})
    save(pd.DataFrame(records),'simpson_mix_direction_diagnostic.csv')
    return pd.DataFrame([{'metric':'mix_dimensions_audited','value':'risk_segment, loan_type, status, timezone'},{'metric':'month_pairs_with_direction_disagreement','value':int(pd.DataFrame(records).direction_disagreement_flag.sum()) if records else 0},{'metric':'warning','value':'Amount-per-account is descriptive; risk segment mix alone does not control all confounding'}])

def call_attempt_survivorship_audit():
    a=read('accounts'); at=read('call_attempts'); calls=read('calls'); payments=read('payments'); payments['payment_status']=payments.payment_status.astype(str).str.upper().str.strip()
    attempts=at.groupby('account_id').agg(attempt_rows=('attempt_id','count'),distinct_attempt_days=('event_at','nunique')).reset_index(); callcounts=calls.groupby('account_id').call_id.nunique().rename('call_count').reset_index(); paid=payments.loc[payments.payment_status.eq('SUCCESS')].groupby('account_id').payment_id.nunique().rename('raw_success_payment_rows').reset_index()
    x=a[['account_id','status','risk_segment','loan_type']].merge(attempts,on='account_id',how='left').merge(callcounts,on='account_id',how='left').merge(paid,on='account_id',how='left');
    for c in ['attempt_rows','distinct_attempt_days','call_count','raw_success_payment_rows']: x[c]=x[c].fillna(0)
    x['has_any_attempt']=x.attempt_rows.gt(0); x['has_any_call']=x.call_count.gt(0); x['has_raw_success_payment']=x.raw_success_payment_rows.gt(0); save(x,'account_contact_and_payment_coverage.csv')
    s=x.groupby(['status','has_any_attempt','has_any_call','has_raw_success_payment']).account_id.nunique().rename('accounts').reset_index(); save(s,'account_contact_payment_coverage_summary.csv')
    return pd.DataFrame([{'metric':'accounts_without_call_attempt','value':int((~x.has_any_attempt).sum())},{'metric':'accounts_without_call_event','value':int((~x.has_any_call).sum())},{'metric':'accounts_without_raw_success_payment','value':int((~x.has_raw_success_payment).sum())},{'metric':'warning','value':'Coverage gaps are visible; whether they are denominator exclusions depends on the business eligibility contract'}])

def attribution_window_audit():
    targets=read('daily_targeting'); targets['target_date']=pd.to_datetime(targets.target_date,errors='coerce'); targets=targets.drop_duplicates('target_id').dropna(subset=['target_date'])
    pay=pd.read_csv(OUT/'payments_canonical.csv',low_memory=False); pay['event_at']=pd.to_datetime(pay.event_at,errors='coerce'); pay=pay.loc[pd.to_numeric(pay.effective_recovered_amount,errors='coerce').fillna(0)>0,['account_id','event_at','effective_recovered_amount']].copy()
    targets['account_id']=targets.account_id.astype(str); pay['account_id']=pay.account_id.astype(str)
    # Candidate windows deliberately overlap and do not establish causal attribution.
    matched=targets[['target_id','account_id','target_date','recommended_channel','campaign_id']].merge(pay,on='account_id',how='left'); matched['days_after_target']=(matched.event_at-matched.target_date).dt.total_seconds()/86400
    rows=[]
    for days in [1,3,7,14,30]:
        w=matched.loc[matched.days_after_target.between(0,days)]
        outcomes=w.groupby('target_id').effective_recovered_amount.sum()
        t=targets[['target_id','recommended_channel','campaign_id']].copy(); t['amount']=t.target_id.map(outcomes).fillna(0); t['converted']=t.amount.gt(0)
        for channel,z in t.groupby('recommended_channel',dropna=False):
            rows.append({'window_days':days,'recommended_channel':channel,'targets':z.target_id.nunique(),'targets_with_payment':int(z.converted.sum()),'observed_conversion_pct':100*z.converted.mean(),'observed_payment_amount_inr':float(z.amount.sum()),'interpretation':'Window sensitivity only; accounts may pay without intervention and exposures overlap'})
    save(pd.DataFrame(rows),'attribution_window_sensitivity.csv')
    return pd.DataFrame([{'metric':'candidate_windows_days','value':'1, 3, 7, 14, 30'},{'metric':'interpretation','value':'Descriptive sensitivity only; not causal attribution'}])

def main():
    tables={'payment_deduplication_impact':payments_audit(),'timezone_sensitivity':timezone_audit(),'vendor_mapping_audit':vendor_mapping_audit(),'agent_identity_audit':agent_identity_audit(),'denominator_audit':denominator_audit(),'population_mix_audit':population_mix_audit(),'contact_survivorship_audit':call_attempt_survivorship_audit(),'attribution_window_audit':attribution_window_audit()}
    for name,df in tables.items(): df.to_csv(OUT/f'{name}.csv',index=False)
    summary={'generated_by':'src/forensic_analysis.py','scope':'reproducible forensic audit signals; no causal claims','outputs':{k:f'data/processed/{k}.csv' for k in tables},'limitations':['Timezone field semantics are undocumented; timezone audit is sensitivity analysis, not a correction.','Vendor disposition mapping effective dates and approved crosswalk are absent.','Identity conflicts require HR/vendor master-data adjudication.','Historical month-opening eligible balance and eligibility rules are absent, so true recovery rate and denominator manipulation cannot be conclusively tested.','No randomized assignment or holdout exists; targeting/campaign effects remain descriptive.','Attribution-window sensitivity is not causal attribution because payment may be unrelated to treatment and exposures overlap.']}
    (REPORTS/'forensic_audit_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    lines=['# Expanded forensic audit results','', 'Generated by `python src/forensic_analysis.py`. All results are audit signals, not automatic business-rule corrections.','']
    for name,df in tables.items():
        lines += [f'## {name.replace("_"," ").title()}','',df.to_markdown(index=False),'']
    lines += ['## Required human decisions','', '- **Timezone:** confirm whether each source timestamp is UTC or local wall time before changing timestamps. `timezone_sensitivity_audit.csv` quantifies the potential hour/day shift only.','- **Vendor codes:** approve a vendor/version/effective-date crosswalk before normalizing dispositions. The proposed aliases are a review queue only.','- **Agent identities:** adjudicate employee-code/agent-ID conflicts against HR and vendor rosters; do not auto-merge.','- **Denominator:** obtain dated eligible-account snapshots and a signed eligibility definition. Current account status and missing contacts do not establish historical exclusion.','- **Attribution windows:** compare `attribution_window_sensitivity.csv` across 1/3/7/14/30 days; select the window only after business validation. It remains descriptive.','- **Causality/ROI:** run a randomized holdout or credible quasi-experiment with intervention costs and guardrails; current associations do not estimate incremental lift.','']
    (REPORTS/'expanded_forensic_audit.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Expanded forensic audits built:', ', '.join(tables))
if __name__=='__main__': main()
