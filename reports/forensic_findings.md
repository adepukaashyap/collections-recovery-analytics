# Forensic findings

## Key identity and payment risks

| Table | Raw rows | Distinct primary key | Repeated-key rows after first |
|---|---:|---:|---:|
| `accounts` | 30,000 | 30,000 | 0 |
| `agents` | 30,000 | 1,000 | 29,000 |
| `borrowers` | 30,600 | 11,015 | 19,585 |
| `payments` | 25,500 | 25,000 | 500 |
| `calls` | 91,350 | 90,000 | 1,350 |
| `call_attempts` | 120,000 | 120,000 | 0 |
| `daily_targeting` | 45,000 | 45,000 | 0 |
| `campaigns` | 120 | 120 | 0 |

## Payment handling

- Raw payments have repeated `payment_id` values, repeated non-null `payment_reference` values, and missing references.
- The pipeline first keeps the latest event per `payment_id`, then the latest event per transaction reference. Missing references use a `MISSING_REF:<payment_id>` surrogate so unrelated missing-reference rows are not collapsed.
- Only the final `SUCCESS` status contributes to effective recovered cash; latest `FAILED`, `PENDING` or `REVERSED` rows contribute zero. This is an explicit analysis rule and must be reconciled with Finance’s transaction ledger semantics before production.

## Coverage and denominator

- Payment event coverage is **2026-01-01 through 2026-08-08**, with August incomplete. It does not meet the approximately 12-month assignment expectation.
- `accounts.csv` contains current snapshot fields, not historical monthly opening balances. The project therefore avoids calling recovered-amount growth a recovery-rate improvement.

## Agent and borrower identity

- Agent and borrower tables contain many repeated IDs. The pipeline keeps the latest `updated_at` row (with timestamp tie-breakers where available) as a practical canonicalization rule. Validate this against source-system history semantics before relying on identity-level performance.
- Calls, dispositions, agent sessions and vendor records should be reconciled for stable agent IDs and vendor timezone semantics before production attribution.

## Causal and reporting risks

- Channel, campaign and targeting outcomes are labeled descriptive; a seven-day payment association is not causal attribution.
- Account vintage groups have unequal observation windows, so observed payer shares are not comparable mature-vintage recovery rates.
- Mix-standardized amount per account is a sensitivity view only; it is not a balance-denominator recovery rate.
