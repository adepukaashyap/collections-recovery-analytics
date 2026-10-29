# Assignment gap-closure pack

This pack maps the assignment requirements to implemented evidence and separates code-completable work from data-dependent work. It does not claim missing source facts or causal results.

## Added/verified work
- Repaired production operating model → forensic report link.
- Polished dashboard responsiveness, keyboard focus, reduced-motion behavior, print styles and table accessibility; checked 35 local links, unique IDs and JavaScript syntax. Browser screenshot/viewport sign-off remains pending because the runtime blocks Chromium navigation.
- One-command runner executes Python pipeline, extended analysis, forensic audits and operational controls.
- Automated checks cover generated outputs, key uniqueness, successful-payment amount rules, denominator warnings, partial-month handling, audit artifacts and local HTML links.
- Forensic outputs include payment deduplication impact, reference conflicts, timezone sensitivity, vendor code trends, agent identity conflicts, status-disappearance/denominator diagnostics, population mix, Simpson-direction diagnostics and attribution-window sensitivity.
- Production guidance documents contracts, keys, metric definitions, lineage, incremental design, late arrivals, backfills, DQ checks, monitoring and anomaly flags.

## Requirements still blocked by evidence or environment
| Requirement | Why it cannot honestly be marked complete | Evidence needed to close it |
|---|---|---|
| Validate 11% recovery-rate claim | Only recovered cash trends are available; historical eligible opening balance is absent | Dated opening eligible balance by account/month and approved eligibility rules |
| Prove incremental causal lift | Randomized pilot design and intent-to-treat analysis plan are documented; no experiment has run in the supplied dataset | Run stratified holdout, capture exposure/cost, estimate 95% CI and guardrails |
| Estimate ₹10 Cr ROI/break-even | Added explicit assumption-based downside/base/upside planning scenarios and break-even; actual causal ROI remains unmeasured | Replace planning assumptions with Finance-approved costs and randomized pilot estimates before final capital release |
| Confirm timezone interpretation | Source timezone/clock semantics are undocumented | System-owner contract and representative event timestamps |
| Approve vendor disposition mapping | No authoritative effective-dated crosswalk | Vendor codebook/version history and business sign-off |
| Resolve agent identity | Conflicting identifiers cannot safely be merged from repeated IDs alone | HR/vendor roster and effective dates |
| Run SQL integration validation | No confirmed PostgreSQL execution/reconciliation recorded in this package | PostgreSQL instance, loaded tables, executed scripts and reconciliation evidence |
| Production scheduler/alerts | Local code and design docs are not a deployed service | Runtime environment, scheduler, durable watermark store, alert destination and operational owner |
| Dashboard one-screen/browser QA | Responsive CSS and static checks are improved, but browser rendering/viewport fit could not be visually verified in this runtime | Browser screenshot/viewport test and stakeholder review |
| Two-page memo guarantee | Verified with a PDF export in this environment; renderer differences may still affect other systems | Re-export from target browser/printer before final submission if its pagination differs |

## Added closure artifacts
- `data/processed/cleaning_impact_summary.csv` quantifies raw-to-canonical row and amount impact and Golden key checks.
- `reports/data_quality_report.html` now has styled, quantified cleaning-impact tables and explicit denominator caveats.
- `data/processed/investment_roi_scenarios.csv` and `reports/investment_business_case.html` show the recommended area (better borrower targeting), budget envelope, downside/base/upside assumptions, planning ROI, break-even and randomized causal validation plan.
- `src/investment_business_case.py` regenerates both outputs from pipeline metrics and documented assumptions.
- `data/processed/data_quality_acceptance_checks.csv` gives explicit pass/review/fail statuses and actions; `cross_output_reconciliation.csv` verifies main, forensic and monthly cash totals agree.
- `src/reconcile_outputs.py` now prevents the forensic canonical event count/cash from silently diverging from the primary pipeline.
- `data/experiment/pilot_assignment_and_outcome_template.csv`, `data/templates/pilot_results_template.csv`, `reports/counterfactual_readiness.html` and `reports/counterfactual_pilot_estimate.html` make the pilot design executable/operational. Eligibility is not inferred and causal estimates remain NOT_RUN until actual randomized outcome data are supplied.
- Notebook now includes cleaning impact, DQ acceptance checks, scenario ROI, and counterfactual decision-rule sections; it was re-executed end-to-end.

## Statistical reporting rules
- Report amount growth separately from recovery-rate change.
- Label attribution-window and timezone comparisons as sensitivity analyses.
- Treat Simpson-style output as a direction diagnostic unless segment-level rate reversals are explicitly demonstrated and adequately powered.
- Do not label associations as causal effects.
- Preserve missingness and rejected-row reasons; never drop unsuccessful accounts merely because they lack a payment.

## Suggested closeout order
1. Run `python src/run_all.py` and `pytest -q`.
2. Execute SQL in PostgreSQL after loading and validating the source schema; reconcile counts and amounts to Python.
3. Obtain historical denominator and source-system definitions.
4. Design a randomized targeting pilot with pre-registered outcomes and cost capture.
5. Test dashboard at 1366×768 and 1920×1080; print the memo to PDF and check pagination.
