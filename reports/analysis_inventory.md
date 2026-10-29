# Analysis inventory

| Artifact | Purpose | Interpretation boundary |
|---|---|---|
| `monthly_recovery_metrics.csv` | Monthly effective successful payment amount, transaction counts, amount MoM change | Not recovery rate; partial month flagged |
| `golden_dataset_account_month.csv` | Account-month fact with snapshot balance caveat | Snapshot balance is not historical opening balance |
| `segment_monthly_metrics.csv` | Risk-segment amount and payer counts | Descriptive; mix and eligibility can differ |
| `loan_type_monthly_metrics.csv` | Loan-type amount and payer counts | Descriptive |
| `targeting_descriptive_association.csv` | Payment within seven days of targeting by recommended channel | Temporal association, not attribution or causal lift |
| `campaign_descriptive_association.csv` | Campaign/channel associations | Overlap and confounding possible |
| `account_vintage_metrics.csv` | Observed payment activity by opening vintage, risk and loan type | Unequal observation windows; not mature vintage recovery rate |
| `mix_adjusted_descriptive_metrics.csv` | Risk-weight-standardized amount per account | Not a recovery rate or causal estimate |
| `data_quality_checks.csv` | Raw row, duplicate and missing-cell checks | Findings require source-owner signoff before production |
