# Production operating model (implementation contract)

## Layering and ownership
- **Raw/immutable:** retain source payload, ingestion timestamp, source file/object ID, source schema version and checksum. Never overwrite raw data.
- **Staging:** parse types, normalize whitespace/status casing, preserve source values alongside normalized values, quarantine parse failures.
- **Clean/canonical:** enforce approved keys, latest-event rules and crosswalks. For same-timestamp conflicts, quarantine until a source sequence/event ID is available; do not assume arbitrary ordering is authoritative.
- **Golden:** one row per account × reporting month, with explicit snapshot/effective dates and lineage to source event IDs. A historical recovery-rate denominator requires dated month-opening eligible balances; the current snapshot is not a substitute.
- **Metrics/features:** version metric definitions, cohort rules, attribution windows and exclusion policies. Keep amount trend distinct from recovery rate.
- **Serving:** dashboard reads versioned metric outputs and displays observation cutoff, partial-month state, freshness, quality status and definition.

## Incremental processing, late arrivals and backfills
1. Persist a per-source watermark and run ID. Ingest by source update timestamp plus a configurable lookback window.
2. Upsert idempotently using source primary key + source event/version; retain prior versions in raw history.
3. When a late event arrives, recompute its affected payment reference, account, and all impacted reporting months; recompute derived account-month rows for affected accounts/months.
4. Support `--from-date`/`--to-date` backfills in a warehouse implementation; record who requested it, reason, row counts and before/after metric deltas.
5. Reconcile raw → canonical counts and amounts; fail the run on unexplained variance above a Finance-approved tolerance.

## Monitoring and response
- Freshness: latest event time vs expected SLA; alert on stale sources.
- Volume: source rows and canonical rows vs rolling baseline; investigate sudden drops/spikes.
- Quality: null keys, duplicate keys, orphan foreign keys, invalid statuses, negative/implausible amounts, unresolved conflicts, and canonicalization deltas.
- Metrics: robust monthly amount anomaly flags in `data/processed/monthly_anomaly_flags.csv` are exploratory only; add seasonality and partial-month handling before paging.
- Ownership: data engineering owns pipeline/lineage, Finance owns payment lifecycle and ledger reconciliation, Operations owns vendor-code crosswalk, HR/vendor management owns agent identity, Analytics owns metric definitions and experiments.

## Current implementation boundary
This repository generates reproducible local CSV outputs, SHA-256 input/output lineage metadata, JSON data contracts and exploratory anomaly flags. It is **not** a deployed scheduler/warehouse: persistent watermarks, transactional upserts, alert delivery, approval workflow and a true historical balance snapshot require infrastructure and source contracts not included in the supplied synthetic files.
