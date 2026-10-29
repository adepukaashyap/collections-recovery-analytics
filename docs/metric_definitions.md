# Metric definitions

- **Effective recovered amount:** sum of amount only for transactions whose latest observed event is `SUCCESS`.
- **Canonical transaction:** latest event per `payment_reference`; if reference is null/blank, use `MISSING_REF:<payment_id>`. First deduplicate repeated `payment_id` by latest `event_at`.
- **MoM amount growth:** (current completed-month amount / prior completed-month amount − 1) × 100. A partial final month is excluded from completed-month comparisons.
- **Recovery rate:** not calculated. Requires approved numerator and historical month-opening eligible balance/denominator.
- **Unique payers:** unique account IDs among successful payment events; not unique borrowers.
- **Channel/campaign association:** descriptive only; not causal without treatment assignment, holdout, or defensible quasi-experimental design.
