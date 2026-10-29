# SQL repository guide

## Dialect and execution contract
These are **PostgreSQL-style templates**, not yet validated against a production warehouse. Confirm the source table/column names and payment lifecycle semantics with data engineering and Finance before execution. They assume source tables named `payments` and `accounts`, and a canonical `payments_canonical` relation built from the pipeline.

## Run order
1. `01_payment_canonicalization.sql` — inspect latest event per `payment_id`, then latest event per transaction reference. Blank references use a payment-ID surrogate. For same-timestamp duplicate `payment_id` rows, the SQL deterministically prefers a populated reference; conflicting source values still require a source event ID or an agreed upstream rule.
2. Materialize the result as `payments_canonical` only after reviewing conflicts/reversals and reconciling to the finance ledger. The file is a SELECT template and does not create/replace a table by itself.
3. `02_monthly_metrics.sql` — monthly recovered amount and unique payers. This is an amount trend, **not a recovery rate**.
4. `03_data_quality.sql` — inspect repeated references and orphan account IDs. Adapt the denominator audit only after a historical balance table exists.

## Production hardening before deployment
- Add a stable source event ID and deterministic tie-breakers for same-timestamp events.
- Define reversals/refunds, partial payments, chargebacks, currency and negative amounts with Finance.
- Add schema contracts, run metadata, incremental watermarks, idempotent upserts, late-arrival backfills and reconciliation tolerances.
- Add tests for null/blank references, duplicate IDs, status transitions, orphan FKs, amount bounds and total ledger reconciliation.
- Pin database dialect/version and execute integration tests in a disposable database before production use.

## Interpretation warning
No historical month-opening eligible balance is present in the supplied data. Do not infer recovery rate, causal channel lift, ROI or break-even from these queries alone.
