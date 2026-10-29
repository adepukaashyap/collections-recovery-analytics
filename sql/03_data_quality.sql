-- Duplicate business keys (inspect before deleting)
SELECT payment_reference, COUNT(*) AS event_rows, COUNT(DISTINCT payment_status) AS status_count
FROM payments WHERE payment_reference IS NOT NULL AND TRIM(payment_reference) <> ''
GROUP BY payment_reference HAVING COUNT(*) > 1 ORDER BY event_rows DESC;

-- Orphan account references
SELECT 'payments' AS source_table, COUNT(*) AS orphan_rows
FROM payments p LEFT JOIN accounts a USING (account_id) WHERE a.account_id IS NULL;

-- Required denominator audit: this query should return zero only when historical balances exist.
-- Do not substitute the latest accounts.outstanding_amount snapshot for month-opening balances.
