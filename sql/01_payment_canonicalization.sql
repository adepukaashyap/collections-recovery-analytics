-- PostgreSQL-style template. Validate dialect and payment status semantics with Finance.
WITH ranked_payment_events AS (
  SELECT p.*,
         COALESCE(NULLIF(TRIM(payment_reference), ''), 'MISSING_REF:' || payment_id) AS transaction_key,
         ROW_NUMBER() OVER (
           PARTITION BY payment_id
           ORDER BY event_at DESC,
                    CASE WHEN NULLIF(TRIM(payment_reference), '') IS NOT NULL THEN 1 ELSE 0 END DESC,
                    payment_reference DESC NULLS LAST
         ) AS payment_id_rank
  FROM payments p
), dedup_payment_ids AS (
  SELECT * FROM ranked_payment_events WHERE payment_id_rank = 1
), ranked_transactions AS (
  SELECT p.*, ROW_NUMBER() OVER (PARTITION BY transaction_key ORDER BY event_at DESC, payment_id DESC) AS transaction_rank
  FROM dedup_payment_ids p
)
SELECT payment_id, account_id, borrower_id, event_at, transaction_key, amount, payment_status,
       CASE WHEN UPPER(payment_status) = 'SUCCESS' THEN amount ELSE 0 END AS effective_recovered_amount
FROM ranked_transactions WHERE transaction_rank = 1;
