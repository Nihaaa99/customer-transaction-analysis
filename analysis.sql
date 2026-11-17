-- Synthetic portfolio dataset; not real customer or payment data.
-- 1. Transaction counts and values by status
SELECT status, COUNT(*) AS txn_count, SUM(amount_inr) AS total_value
FROM transactions GROUP BY status;

-- 2. Customer spend
SELECT c.customer_id, c.customer_name, c.city,
       COUNT(t.transaction_id) AS txn_count, SUM(t.amount_inr) AS spend
FROM customers c JOIN transactions t ON c.customer_id=t.customer_id
WHERE t.status='Completed'
GROUP BY c.customer_id,c.customer_name,c.city
ORDER BY spend DESC;

-- 3. Payment channel completion rate
SELECT channel, COUNT(*) AS total_txns,
       SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) AS completed_txns
FROM transactions GROUP BY channel;

-- 4. Average spend by customer using a CTE
WITH spend AS (
 SELECT customer_id, SUM(amount_inr) AS total_spend
 FROM transactions WHERE status='Completed' GROUP BY customer_id
)
SELECT * FROM spend WHERE total_spend > (SELECT AVG(total_spend) FROM spend);
