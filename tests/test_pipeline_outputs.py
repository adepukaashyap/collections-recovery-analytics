from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def test_outputs_exist():
    for f in ['payments_canonical.csv','monthly_recovery_metrics.csv','golden_dataset_account_month.csv','data_quality_checks.csv']:
        assert (ROOT/'data/processed'/f).exists()
def test_payment_rule_and_metrics():
    p=pd.read_csv(ROOT/'data/processed/payments_canonical.csv')
    assert p.transaction_key.is_unique
    assert (p.loc[p.payment_status!='SUCCESS','effective_recovered_amount'].abs()<1e-8).all()
    m=pd.read_csv(ROOT/'data/processed/monthly_recovery_metrics.csv')
    assert len(m)>=6
    assert 'partial_month' in m.columns
def test_golden_denominator_caveat():
    g=pd.read_csv(ROOT/'data/processed/golden_dataset_account_month.csv')
    assert 'denominator_warning' in g.columns
    assert g.denominator_warning.str.contains('not historical').all()
def test_no_duplicate_account_month():
    g=pd.read_csv(ROOT/'data/processed/golden_dataset_account_month.csv')
    assert not g.duplicated(['account_id','month']).any()


def test_html_local_links_resolve():
    import re
    for html in ROOT.rglob('*.html'):
        source=html.read_text(encoding='utf-8', errors='ignore')
        for target in re.findall(r'(?:href|src)=[\"\']([^\"\']+)', source):
            if target.startswith(('http://','https://','mailto:','#','data:','javascript:')):
                continue
            local=(html.parent/target.split('#',1)[0].split('?',1)[0])
            assert local.exists(), f'Broken local link in {html.relative_to(ROOT)}: {target}'

def test_partial_month_excluded_from_completed_month_claim():
    m=pd.read_csv(ROOT/'data/processed/monthly_recovery_metrics.csv')
    assert m.iloc[-1]['partial_month'] == True
    complete=m.loc[~m['partial_month']].copy()
    july=complete.loc[complete['month'].astype(str).str.startswith('2026-07')].iloc[0]
    june=complete.loc[complete['month'].astype(str).str.startswith('2026-06')].iloc[0]
    expected=(july['recovered_amount']/june['recovered_amount']-1)*100
    assert abs(expected-float(july['mom_growth_pct'])) < 0.01
    assert abs(expected-11.334836) < 0.02


def test_extended_and_forensic_outputs_exist():
    expected=['targeting_descriptive_association.csv','campaign_descriptive_association.csv','account_vintage_metrics.csv','mix_adjusted_descriptive_metrics.csv','payment_deduplication_impact.csv','timezone_sensitivity_audit.csv','vendor_disposition_code_trends.csv','agent_employee_code_conflicts.csv','denominator_status_disappearance_audit.csv','population_mix_monthly.csv','simpson_mix_direction_diagnostic.csv','attribution_window_sensitivity.csv','monthly_anomaly_flags.csv']
    for name in expected:
        assert (ROOT/'data/processed'/name).exists(), name


def test_forensic_audits_keep_caveats():
    p=pd.read_csv(ROOT/'data/processed/payment_deduplication_impact.csv')
    assert {'raw_payment_rows','canonical_effective_success_amount_inr'} <= set(p.metric)
    t=pd.read_csv(ROOT/'data/processed/timezone_sensitivity.csv')
    assert t.interpretation.str.contains('Sensitivity only').all()
    a=pd.read_csv(ROOT/'data/processed/attribution_window_sensitivity.csv')
    assert set(a.window_days.unique()) == {1,3,7,14,30}
    assert a.interpretation.str.contains('accounts may pay without intervention').all()


def test_operational_artifacts_exist():
    for name in ['data_contracts.json','production_operating_model.md']:
        assert (ROOT/'docs'/name).exists()
    for name in ['lineage_manifest.json','forensic_audit_summary.json','expanded_forensic_audit.md']:
        assert (ROOT/'reports'/name).exists()


def test_canonical_payment_output_reconciliation_baseline():
    p=pd.read_csv(ROOT/'data/processed/payments_canonical.csv')
    assert len(p) == 21189
    assert p.transaction_key.is_unique
    assert abs(float(p.effective_recovered_amount.sum()) - 1112566691.46) < 0.01
    assert int((p.effective_recovered_amount > 0).sum()) == 14840


def test_duplicate_payment_id_tie_prefers_populated_reference():
    raw=pd.read_csv(ROOT/'data/raw/payments.csv', low_memory=False)
    dup=raw[raw.payment_id.duplicated(keep=False)]
    mixed=dup.groupby('payment_id').filter(
        lambda g: g.payment_reference.notna().any() and g.payment_reference.isna().any()
    )
    canonical=pd.read_csv(ROOT/'data/processed/payments_canonical.csv', low_memory=False)
    mixed_ids=set(mixed.payment_id)
    chosen=canonical[canonical.payment_id.isin(mixed_ids)]
    assert chosen.payment_reference.notna().all()


def test_cleaning_impact_and_investment_scenarios_exist():
    impact=pd.read_csv(ROOT/'data/processed/cleaning_impact_summary.csv')
    assert {'Raw payment rows','Canonical transaction-reference events','Golden account-month duplicate keys'} <= set(impact.measure)
    assert float(impact.loc[impact.measure=='Golden account-month duplicate keys','value'].iloc[0]) == 0
    scenarios=pd.read_csv(ROOT/'data/processed/investment_roi_scenarios.csv')
    assert set(scenarios.scenario) == {'Downside','Base case','Upside'}
    base=scenarios.loc[scenarios.scenario=='Base case'].iloc[0]
    assert abs(float(base.planning_roi_pct)-8.68) < 0.02
    assert 'NOT MEASURED CAUSAL LIFT' in base.classification
    assert (ROOT/'reports/investment_business_case.html').exists()
    assert (ROOT/'reports/data_quality_report.css').exists()

def test_forensic_and_main_canonical_outputs_reconcile():
    main=pd.read_csv(ROOT/'data/processed/payments_canonical.csv')
    forensic=pd.read_csv(ROOT/'data/processed/payments_canonical_forensic.csv')
    monthly=pd.read_csv(ROOT/'data/processed/monthly_recovery_metrics.csv')
    assert len(main)==len(forensic)
    assert abs(main.effective_recovered_amount.sum()-forensic.effective_amount.sum()) < 0.01
    assert abs(main.effective_recovered_amount.sum()-monthly.recovered_amount.sum()) < 0.01
    reconciliation=pd.read_csv(ROOT/'data/processed/cross_output_reconciliation.csv')
    assert reconciliation.status.eq('PASS').all()

def test_data_quality_acceptance_checks_are_explicit():
    qa=pd.read_csv(ROOT/'data/processed/data_quality_acceptance_checks.csv')
    required={'check_id','severity','check','observed','threshold','status','business_impact','action'}
    assert required <= set(qa.columns)
    assert qa.check_id.is_unique
    assert {'PAY-001','PAY-002','GOLD-001','DQ-002','RECON-001','RECON-002'} <= set(qa.check_id)
    assert qa.loc[qa.check_id.isin(['PAY-001','PAY-002','GOLD-001','DQ-002','RECON-001','RECON-002']),'status'].eq('PASS').all()

def test_counterfactual_and_investment_limits_are_documented():
    plan=(ROOT/'docs/counterfactual_design.md').read_text(encoding='utf-8')
    assert 'sample-size' in plan.lower()
    assert 'intent-to-treat' in plan.lower()
    assert 'not yet measured' in plan.lower()
    report=(ROOT/'reports/investment_business_case.html').read_text(encoding='utf-8')
    assert 'Not measured causal ROI' in report
    assert 'Downside' in report and 'Base case' in report and 'Upside' in report
    assert 'randomized' in report.lower()

def test_counterfactual_pilot_is_prepared_without_fabricated_effect():
    frame=pd.read_csv(ROOT/'data/experiment/pilot_assignment_and_outcome_template.csv',low_memory=False)
    assert len(frame)==30000
    assert frame.eligibility_status.eq('REVIEW_REQUIRED').all()
    assert frame.assigned_arm.fillna('').eq('').all()
    estimate=pd.read_csv(ROOT/'data/processed/counterfactual_pilot_estimate.csv')
    assert estimate.iloc[0].status=='NOT_RUN'
    assert pd.isna(estimate.iloc[0].cash_lift_per_eligible_inr)
    assert (ROOT/'reports/counterfactual_readiness.html').exists()
    assert (ROOT/'reports/counterfactual_pilot_estimate.html').exists()
