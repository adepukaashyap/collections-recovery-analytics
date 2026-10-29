# Collections Recovery Analytics — expanded audited project

This repository uses the supplied **Synthetic Collections Analytics Dataset**. It contains raw data, canonicalization pipeline, descriptive analysis, expanded forensic audits, data contracts, lineage/run manifest, anomaly flags, SQL templates, an executed notebook, tests, dashboard, architecture diagram and executive memo.

## Key result

The files contain **30,000 raw account rows** and payment events from **2026-01-01 to 2026-08-08**, not 12 complete months. The project does **not** certify the “11% month-on-month recovery” claim. July recovered cash rose 11.33% versus June, but that is an amount trend, not a recovery-rate improvement. Historical month-opening eligible balance is absent.

## Quick start

Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python src/run_all.py
pytest -q
```

`run_all.py` runs canonicalization, Golden Dataset generation, counterfactual pilot template preparation, extended descriptive analysis, forensic audits, cross-output reconciliation, operational controls, investment scenarios and the causal estimator status gate in order. Open `dashboard/index.html` for the executive dashboard. Open `reports/expanded_forensic_audit.html` for the styled forensic audit report (or `reports/expanded_forensic_audit.md` for the source text), `reports/executive_memo.html` for the styled memo, and `notebooks/collections_analysis.ipynb` for the executed analysis notebook.

## New forensic outputs

- `data/processed/payment_deduplication_impact.csv` and `payment_reference_conflicts.csv` — before/after canonicalization amounts and conflicting reference groups.
- `timezone_sensitivity_audit.csv` — counts of call hour/date changes under a clearly labeled timezone interpretation sensitivity; it does not assume source timestamps are local or UTC.
- `vendor_disposition_code_trends.csv` and `vendor_disposition_mapping_review.csv` — code/version/vendor/month patterns and candidate aliases for human approval.
- `agent_employee_code_conflicts.csv` and `agent_id_conflicts.csv` — cross-ID conflict queues; no unsafe automatic identity merges.
- `denominator_status_disappearance_audit.csv`, `denominator_status_summary.csv`, and `account_contact_payment_coverage.csv` — snapshot/history disagreement and missing contact/payment coverage signals. These do not prove historical denominator manipulation.
- `population_mix_monthly.csv`, `simpson_mix_direction_diagnostic.csv`, `mix_adjusted_descriptive_metrics.csv`, `account_vintage_metrics.csv` — population composition, direction disagreement and descriptive fixed-mix/cohort checks.
- `attribution_window_sensitivity.csv` — 1/3/7/14/30-day payment-window sensitivity by channel; descriptive, not causal.
- `monthly_anomaly_flags.csv` — exploratory anomaly flags, not production alerting.
- `docs/data_contracts.json`, `reports/lineage_manifest.json`, `docs/production_operating_model.md` — contracts, hashes/row counts, lineage, incremental/backfill design and monitoring requirements.

## Definitions and caveats

- **Effective recovered cash:** latest event per payment reference (or payment-ID surrogate if blank), counted only when final status is `SUCCESS`. Same-timestamp conflicting updates require a source event sequence or business-approved tie-breaker.
- **Month-on-month growth:** percentage change in completed calendar-month recovered amount. This is not a recovery rate.
- **Recovery rate:** cannot be calculated reliably without monthly opening eligible balance and a documented eligibility/write-off policy.
- **Attribution:** channel and targeting cuts are descriptive, not causal. Use a randomized holdout or defensible quasi-experiment before allocating the ₹10 Cr budget.
- **Timezone:** timestamps are preserved as recorded; source timezone semantics need owner validation before UTC conversion.
- **Vendor/agent conflicts:** audit queues are generated, but business owners must approve crosswalks and identity resolution.

## Project map

- `data/raw/` — original supplied CSVs (do not edit)
- `data/processed/` — canonical tables, descriptive metrics and audit outputs
- `src/run_all.py` — one-command orchestrator
- `src/run_pipeline.py` — canonical entities/payments/account-month Golden Dataset
- `src/extended_analysis.py` — targeting, campaign, vintage and mix-standardized analysis
- `src/forensic_analysis.py` — payment, timezone, vendor, agent, denominator, mix, survivorship and attribution-window audits
- `src/operational_controls.py` — data contracts, lineage manifest and exploratory anomaly flags
- `sql/` — PostgreSQL-style SQL templates; see validation boundary below
- `notebooks/collections_analysis.ipynb` — executed exploratory notebook with saved outputs
- `reports/` — findings, data quality, forensic results and executive memo
- `dashboard/index.html` — executive dashboard
- `diagrams/` — editable draw.io and SVG architecture

## Validation boundary

The Python pipeline and tests run locally. SQL files remain **PostgreSQL-style templates and have not been executed against a PostgreSQL instance** in this environment. Before production, run them against a disposable PostgreSQL database with source-compatible schemas, reconcile SQL totals to Python outputs, and reconcile effective cash to Finance's ledger. This repository also specifies—but does not deploy—persistent watermarks, transactional incremental upserts, alert delivery, approved identity/vendor crosswalks, and randomized experimentation. These require infrastructure or source contracts not supplied in the synthetic dataset.
### Dashboard and QA review
- Open `dashboard/index.html` in a browser.
- Browser screenshot QA remains pending because browser navigation was blocked in the build environment.

## Updated assignment closure artifacts
- **Golden Dataset / cleaning impact:** `data/processed/golden_dataset_account_month.csv`, `data/processed/cleaning_impact_summary.csv`, `reports/data_quality_report.html`.
- **₹10 Cr investment model:** `reports/investment_business_case.html` and `data/processed/investment_roi_scenarios.csv`.
- **Regenerate everything:** `python src/run_all.py`; then run `pytest -q`.
- **Investment caveat:** better borrower targeting is the recommended area to test first, but its ROI figures are assumption-based planning scenarios. Actual causal lift requires the randomized holdout described in `docs/counterfactual_design.md`.


## Final hardening additions

- `data/processed/data_quality_acceptance_checks.csv` records check IDs, severity, observed value, threshold, status, business impact and action. `REVIEW` means a source-policy decision remains; it is not silently passed.
- `data/processed/cross_output_reconciliation.csv` checks that main canonical payments, forensic canonical payments and monthly totals agree. The current internal Python reconciliation must pass before packaging; it is not an external Finance ledger reconciliation.
- `data/processed/cleaning_impact_summary.csv` quantifies 25,500 raw payment rows vs 21,189 canonical events (16.91% net row reduction) and ₹134.15 Cr raw SUCCESS-row amount vs ₹111.26 Cr canonical effective cash (₹22.89 Cr difference). This is an audit impact, not proof that every removed row/amount is invalid; Finance sign-off is still required.
- `data/experiment/pilot_assignment_and_outcome_template.csv` contains the account-level design frame and blank outcome/exposure fields. Eligibility is marked `REVIEW_REQUIRED`; no treatment assignment is made before approved eligibility rules.
- `data/templates/pilot_results_template.csv` defines the outcome schema. `src/analyze_counterfactual_pilot.py` intentionally reports `NOT_RUN` until real randomized outcomes are supplied; it does not manufacture causal lift.
- The ROI scenarios remain planning assumptions, not measured causal ROI. Better borrower targeting is the recommended first hypothesis to test, with staged capital release only after the pilot passes its confidence-bound, cost and customer-protection gates.
