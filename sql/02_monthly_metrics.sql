-- `payments_canonical` is produced by the Python pipeline using the same documented rules.
SELECT DATE_TRUNC('month', event_at)::date AS month,
       SUM(effective_recovered_amount) AS recovered_amount,
       COUNT(*) FILTER (WHERE effective_recovered_amount > 0) AS successful_events,
       COUNT(DISTINCT account_id) FILTER (WHERE effective_recovered_amount > 0) AS unique_payers
FROM payments_canonical
GROUP BY 1 ORDER BY 1;
-- This is amount trend, not recovery rate. A valid rate requires historical eligible opening balance.
