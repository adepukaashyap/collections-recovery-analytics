# Data quality and lineage report

## Scope and controls

Input: supplied synthetic challenge dataset (seed 42). Files are retained unchanged under `data/raw/`. Canonical outputs are generated into `data/processed/`. Entity dimensions with repeated IDs are reduced to the latest `updated_at` (tie-breaker event/creation timestamp where available). Payment events are deduplicated by `payment_id`, then collapsed to the latest event per transaction reference; blank references use a payment-ID surrogate. Only the final `SUCCESS` state contributes to recovered cash. This is a transparent analytical rule, not a substitute for finance-led reconciliation.

## Known limitations

- Observed payments run only from 2026-01-01 to 2026-08-08; the final month is incomplete, and the input does not meet the assignment’s approximately 12-month requirement.
- Historical month-opening outstanding balance is absent. The `current_snapshot_outstanding` column is deliberately labeled and must not be interpreted as a historical denominator.
- Multiple timezone fields and vendor mappings exist. The main payment analysis uses supplied `event_at` values as recorded and does not silently convert ambiguous naive timestamps. Timezone normalization should be completed after the owner confirms each source field’s semantics.
- Channel/targeting association is descriptive; no randomized holdout or reliable causal attribution key is supplied.
- Synthetic records may include deliberately implausible values; inspect outliers before production use.

## Machine-readable checks

See `data/processed/data_quality_checks.csv` for row counts, missing cells, duplicate full rows, foreign-key checks and canonicalization counts.


## Cleaning impact (regenerated output)

See `data/processed/cleaning_impact_summary.csv` and the styled `data_quality_report.html`. The report compares raw payment rows, payment-ID de-duplication, canonical reference events, raw SUCCESS amount versus canonical effective cash, and Golden account-month key uniqueness. The raw-to-canonical cash difference is an audit signal—not a claim that all removed rows are invalid. Finance must reconcile the canonical output to the source ledger.

Golden Dataset grain is one row per `account_id × month`, with `(account_id, month)` as the unique key. The current-snapshot outstanding amount is explicitly not a historical opening denominator.
