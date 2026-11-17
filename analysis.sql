-- Customer & Transaction Analysis
-- SQL dialect: SQLite. All records are fictional sample data.

-- 1. Row counts
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions;

-- 2. Transaction volume and value by status
SELECT status, COUNT(*) AS transaction_count,
       SUM(CAST(amount_inr AS REAL)) AS total_amount_inr,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM transactions), 2) AS pct_of_transactions
FROM transactions
GROUP BY status
ORDER BY transaction_count DESC;

-- 3. Completed spend by customer (JOIN + GROUP BY)
SELECT c.customer_id, c.customer_name, c.city,
       COUNT(t.transaction_id) AS completed_transactions,
       SUM(CAST(t.amount_inr AS REAL)) AS completed_spend_inr
FROM customers c
JOIN transactions t ON t.customer_id = c.customer_id
WHERE t.status = 'Completed'
GROUP BY c.customer_id, c.customer_name, c.city
ORDER BY completed_spend_inr DESC;

-- 4. Payment channel performance (CASE WHEN)
SELECT channel, COUNT(*) AS total_transactions,
       SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed_transactions,
       ROUND(100.0 * SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS completion_rate_pct
FROM transactions
GROUP BY channel
ORDER BY completion_rate_pct DESC;

-- 5. Customers above average completed spend (CTE + subquery)
WITH customer_spend AS (
    SELECT customer_id, SUM(CAST(amount_inr AS REAL)) AS completed_spend_inr
    FROM transactions
    WHERE status = 'Completed'
    GROUP BY customer_id
)
SELECT customer_id, completed_spend_inr
FROM customer_spend
WHERE completed_spend_inr > (SELECT AVG(completed_spend_inr) FROM customer_spend)
ORDER BY completed_spend_inr DESC;

-- 6. Monthly transaction trend
SELECT substr(transaction_date, 1, 7) AS transaction_month,
       COUNT(*) AS transaction_count,
       SUM(CAST(amount_inr AS REAL)) AS total_amount_inr
FROM transactions
GROUP BY transaction_month
ORDER BY transaction_month;

-- 7. Data quality: transactions without a matching customer
SELECT t.*
FROM transactions t
LEFT JOIN customers c ON c.customer_id = t.customer_id
WHERE c.customer_id IS NULL;

-- 8. Data quality: duplicate transaction IDs
SELECT transaction_id, COUNT(*) AS occurrences
FROM transactions
GROUP BY transaction_id
HAVING COUNT(*) > 1;
