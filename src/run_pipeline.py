#!/usr/bin/env python3
"""Rebuild canonical payment and monthly account-month metrics from data/raw."""
from pathlib import Path
import pandas as pd, numpy as np, json
ROOT=Path(__file__).resolve().parents[1]; RAW=ROOT/'data/raw'; OUT=ROOT/'data/processed'; REPORTS=ROOT/'reports'
OUT.mkdir(parents=True,exist_ok=True); REPORTS.mkdir(parents=True,exist_ok=True)
def read(name): return pd.read_csv(RAW/f'{name}.csv',low_memory=False)
def latest(df,key,updated=None,event=None):
    cols=[c for c in [updated,event] if c and c in df.columns]
    if cols: df=df.sort_values(cols,na_position='first')
    return df.drop_duplicates(key,keep='last').copy()
accounts=latest(read('accounts'),'account_id',event='opened_at')
borrowers=latest(read('borrowers'),'borrower_id','updated_at','created_at')
agents=latest(read('agents'),'agent_id','updated_at','joined_at')
for name,df in [('accounts',accounts),('borrowers',borrowers),('agents',agents),('campaigns',latest(read('campaigns'),'campaign_id')),('vendors',latest(read('vendor_telephony'),'vendor_id'))]: df.to_csv(OUT/f'{name}_canonical.csv',index=False)
p=read('payments'); p['event_at']=pd.to_datetime(p.event_at,errors='coerce'); p['amount']=pd.to_numeric(p.amount,errors='coerce'); p['payment_status']=p.payment_status.astype('string').str.upper().str.strip()
# Deterministic tie-break: for duplicate payment IDs at the same timestamp, prefer
# the row with a populated transaction reference. This resolves synthetic duplicate
# rows where the reference is missing in one copy; conflicting business values still
# require a source event ID / upstream rule.
p['_reference_present']=p.payment_reference.notna() & p.payment_reference.astype('string').str.strip().ne('')
p=p.sort_values(['event_at','_reference_present','payment_reference'],na_position='first').drop_duplicates('payment_id',keep='last')
p['transaction_key']=p.payment_reference.where(p.payment_reference.notna() & p.payment_reference.astype('string').str.strip().ne(''),'MISSING_REF:'+p.payment_id.astype(str))
p=p.drop(columns=['_reference_present'])
p=p.sort_values('event_at').drop_duplicates('transaction_key',keep='last')
p['month']=p.event_at.dt.to_period('M').astype(str); p['effective_recovered_amount']=np.where(p.payment_status.eq('SUCCESS'),p.amount.fillna(0),0.0); p['missing_reference']=p.payment_reference.isna() | p.payment_reference.astype('string').str.strip().eq('')
p.to_csv(OUT/'payments_canonical.csv',index=False)
monthly=p.groupby('month').agg(recovered_amount=('effective_recovered_amount','sum'),successful_transactions=('effective_recovered_amount',lambda s:int((s>0).sum())),transactions=('payment_id','count')).reset_index()
unique_payers=p.loc[p.effective_recovered_amount>0].groupby('month').account_id.nunique().rename('unique_payers').reset_index()
monthly=monthly.merge(unique_payers,on='month',how='left').fillna({'unique_payers':0})
monthly['mom_growth_pct']=monthly.recovered_amount.pct_change()*100
max_date=p.event_at.max(); monthly['partial_month']=monthly.month.eq(str(max_date.to_period('M'))) & (max_date.day < max_date.days_in_month)
monthly.to_csv(OUT/'monthly_recovery_metrics.csv',index=False)
base=accounts[['account_id','borrower_id','loan_type','principal_amount','outstanding_amount','dpd','risk_segment','status','opened_at','timezone','schema_version']].copy()
months=sorted(p.month.dropna().unique()); spine=pd.MultiIndex.from_product([base.account_id.astype(str),months],names=['account_id','month']).to_frame(index=False)
pm=p.groupby(['account_id','month']).agg(recovered_amount=('effective_recovered_amount','sum'),successful_payment_count=('effective_recovered_amount',lambda s:int((s>0).sum())),payment_event_count=('payment_id','count')).reset_index()
g=spine.merge(base,on='account_id',how='left').merge(pm,on=['account_id','month'],how='left')
for c in ['recovered_amount','successful_payment_count','payment_event_count']: g[c]=g[c].fillna(0)
g['paid_any']=g.successful_payment_count.gt(0).astype(int); g['current_snapshot_outstanding']=pd.to_numeric(g.outstanding_amount,errors='coerce'); g['recovery_to_current_snapshot_pct']=np.where(g.current_snapshot_outstanding>0,100*g.recovered_amount/g.current_snapshot_outstanding,np.nan); g['denominator_warning']='Current account snapshot; not historical month-opening balance'; g.to_csv(OUT/'golden_dataset_account_month.csv',index=False)
for col,name in [('risk_segment','segment_monthly_metrics'),('loan_type','loan_type_monthly_metrics')]:
    x=g.groupby(['month',col]).agg(accounts=('account_id','nunique'),recovered_amount=('recovered_amount','sum'),accounts_with_payment=('paid_any','sum')).reset_index(); x.to_csv(OUT/f'{name}.csv',index=False)
# Machine-readable QA inventory and checks
checks=[]
for f in sorted(RAW.glob('*.csv')):
    d=pd.read_csv(f,low_memory=False); checks += [{'dataset':f.stem,'metric':'raw_rows','value':len(d)},{'dataset':f.stem,'metric':'duplicate_full_rows','value':int(d.duplicated().sum())},{'dataset':f.stem,'metric':'missing_cells','value':int(d.isna().sum().sum())}]
checks += [{'dataset':'agents','metric':'duplicate_agent_id_rows_raw','value':int(read('agents').agent_id.duplicated().sum())},{'dataset':'borrowers','metric':'duplicate_borrower_id_rows_raw','value':int(read('borrowers').borrower_id.duplicated().sum())},{'dataset':'payments','metric':'duplicate_payment_id_rows_raw','value':int(read('payments').payment_id.duplicated().sum())},{'dataset':'payments','metric':'duplicate_payment_reference_rows_raw','value':int(read('payments').payment_reference.dropna().duplicated(keep=False).sum())},{'dataset':'payments','metric':'missing_payment_reference_rows_raw','value':int(read('payments').payment_reference.isna().sum())},{'dataset':'payments','metric':'canonical_payment_events','value':int(len(p))},{'dataset':'payments','metric':'effective_success_amount_inr','value':float(p.effective_recovered_amount.sum())},{'dataset':'accounts','metric':'canonical_account_ids','value':int(accounts.account_id.nunique())},{'dataset':'agents','metric':'canonical_agent_ids','value':int(agents.agent_id.nunique())}]
for table in ['payments','calls','call_attempts','promises_to_pay','field_visits']:
    raw_table=read(table)
    checks.append({'dataset':table,'metric':'orphan_account_ids','value':int((~raw_table.account_id.astype('string').isin(accounts.account_id.astype('string'))).sum())})
pd.DataFrame(checks).to_csv(OUT/'data_quality_checks.csv',index=False)
# Explicit acceptance checks with severity, measured value, threshold, status and action.
raw_payments=read('payments'); raw_calls=read('calls'); raw_attempts=read('call_attempts')
valid_statuses={'SUCCESS','FAILED','PENDING','REVERSED'}
acceptance=[
 {'check_id':'PAY-001','area':'payments','severity':'CRITICAL','check':'Canonical transaction key unique','observed':int(p.transaction_key.duplicated().sum()),'threshold':'0 duplicates','status':'PASS' if p.transaction_key.is_unique else 'FAIL','business_impact':'Prevents double-counting transaction references','action':'Block release if failed'},
 {'check_id':'PAY-002','area':'payments','severity':'CRITICAL','check':'Non-success cash excluded','observed':float(p.loc[p.payment_status.ne('SUCCESS'),'effective_recovered_amount'].abs().sum()),'threshold':'₹0','status':'PASS' if np.isclose(p.loc[p.payment_status.ne('SUCCESS'),'effective_recovered_amount'].abs().sum(),0) else 'FAIL','business_impact':'Avoids counting failed, pending or reversed events as recovered cash','action':'Block release if failed'},
 {'check_id':'PAY-003','area':'payments','severity':'HIGH','check':'Raw payment ID missing count','observed':int(raw_payments.payment_id.isna().sum()),'threshold':'0','status':'PASS' if raw_payments.payment_id.notna().all() else 'FAIL','business_impact':'Missing IDs prevent reliable event deduplication','action':'Quarantine rows with missing IDs'},
 {'check_id':'PAY-004','area':'payments','severity':'HIGH','check':'Unrecognized raw payment statuses','observed':int((~raw_payments.payment_status.astype('string').str.upper().str.strip().isin(valid_statuses)).sum()),'threshold':'0 or approved mapping','status':'PASS' if raw_payments.payment_status.astype('string').str.upper().str.strip().isin(valid_statuses).all() else 'REVIEW','business_impact':'Unknown status could be misclassified in recovered cash','action':'Map or quarantine unknown statuses'},
 {'check_id':'PAY-005','area':'payments','severity':'HIGH','check':'Negative or unparseable raw payment amounts','observed':int((pd.to_numeric(raw_payments.amount,errors='coerce').isna() | pd.to_numeric(raw_payments.amount,errors='coerce').lt(0)).sum()),'threshold':'0 or approved reversal policy','status':'PASS' if (pd.to_numeric(raw_payments.amount,errors='coerce').notna() & pd.to_numeric(raw_payments.amount,errors='coerce').ge(0)).all() else 'REVIEW','business_impact':'Amount quality changes cash totals','action':'Reconcile to payment ledger'},
 {'check_id':'GOLD-001','area':'golden_dataset','severity':'CRITICAL','check':'Unique account-month key','observed':int(g.duplicated(['account_id','month']).sum()),'threshold':'0 duplicates','status':'PASS' if not g.duplicated(['account_id','month']).any() else 'FAIL','business_impact':'Prevents duplicate account-month aggregation','action':'Block release if failed'},
 {'check_id':'GOLD-002','area':'golden_dataset','severity':'HIGH','check':'Golden account coverage vs canonical accounts','observed':int(g.account_id.nunique()),'threshold':f'{accounts.account_id.nunique()} canonical accounts','status':'PASS' if g.account_id.nunique()==accounts.account_id.nunique() else 'FAIL','business_impact':'Coverage loss can bias population rates','action':'Investigate missing accounts'},
 {'check_id':'GOLD-003','area':'golden_dataset','severity':'HIGH','check':'Historical denominator clearly flagged','observed':int(g.denominator_warning.isna().sum()),'threshold':'0 missing warnings','status':'PASS' if g.denominator_warning.notna().all() else 'FAIL','business_impact':'Prevents current snapshot balance being mistaken for historical eligible balance','action':'Keep rate claims blocked until historical balances supplied'},
 {'check_id':'DQ-001','area':'referential_integrity','severity':'HIGH','check':'Payment account IDs resolve to canonical accounts','observed':int((~raw_payments.account_id.astype('string').isin(accounts.account_id.astype('string'))).sum()),'threshold':'0 or documented exception','status':'PASS' if raw_payments.account_id.astype('string').isin(accounts.account_id.astype('string')).all() else 'REVIEW','business_impact':'Orphan payments may not join to portfolio metrics','action':'Resolve or quarantine orphan rows'},
 {'check_id':'DQ-002','area':'metrics','severity':'CRITICAL','check':'Monthly recovered cash reconciles to canonical payment output','observed':float(abs(monthly.recovered_amount.sum()-p.effective_recovered_amount.sum())),'threshold':'₹0 difference','status':'PASS' if np.isclose(monthly.recovered_amount.sum(),p.effective_recovered_amount.sum(),atol=0.01) else 'FAIL','business_impact':'Ensures headline cash agrees to canonical payment events','action':'Block release if failed'},
 {'check_id':'DQ-003','area':'metrics','severity':'CRITICAL','check':'Forensic canonical count matches main pipeline','observed':int(len(p)),'threshold':'Must match payments_audit after forensic stage','status':'PENDING_FORENSIC_RECONCILIATION','business_impact':'Prevents conflicting canonical totals across reports','action':'Compare after forensic stage in run_all.py'},
]
pd.DataFrame(acceptance).to_csv(OUT/'data_quality_acceptance_checks.csv',index=False)
print(f'Built outputs: {len(p):,} canonical payment events; {len(g):,} account-month rows; observed through {max_date.date()}')
