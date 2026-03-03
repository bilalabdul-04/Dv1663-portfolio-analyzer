-- ============================================================
-- Personal Investment Portfolio Analyzer — Report-Ready Queries
-- ============================================================
-- These are the 5 main queries required for the report.
-- Each query demonstrates specific SQL features.
-- ============================================================


-- ============================================================
-- QUERY 1: Portfolio Summary per User
-- ============================================================
-- WHAT IT DOES:
--   Shows each user's total invested amount, current portfolio
--   value (based on latest prices), and profit/loss.
--
-- SQL FEATURES USED:
--   ✅ Multi-table JOIN (Users, Transactions, Assets, PriceHistory)
--   ✅ Aggregation (SUM)
--   ✅ Subquery (to get latest price)
--
-- HOW IT WORKS:
--   1. For each user, sum up all BUY transactions (= total invested)
--   2. Subtract all SELL transactions
--   3. Calculate current value using the latest price from PriceHistory
--   4. Profit/Loss = current value - net invested
-- ============================================================
SELECT
    u.user_id,
    u.username,
    -- Total money spent on BUYs
    COALESCE(SUM(CASE WHEN t.type = 'BUY' THEN t.total_amount ELSE 0 END), 0)
        AS total_bought,
    -- Total money received from SELLs
    COALESCE(SUM(CASE WHEN t.type = 'SELL' THEN t.total_amount ELSE 0 END), 0)
        AS total_sold,
    -- Net invested = bought - sold
    COALESCE(SUM(CASE WHEN t.type = 'BUY' THEN t.total_amount ELSE 0 END), 0)
    - COALESCE(SUM(CASE WHEN t.type = 'SELL' THEN t.total_amount ELSE 0 END), 0)
        AS net_invested,
    -- Current value of holdings (quantity owned × latest price)
    COALESCE(SUM(
        CASE WHEN t.type = 'BUY' THEN t.quantity ELSE -t.quantity END
    ) * (
        SELECT ph.close_price
        FROM PriceHistory ph
        WHERE ph.asset_id = t.asset_id
        ORDER BY ph.price_date DESC
        LIMIT 1
    ), 0) AS current_value
FROM Users u
LEFT JOIN Transactions t ON u.user_id = t.user_id
LEFT JOIN Assets a ON t.asset_id = a.asset_id
GROUP BY u.user_id, u.username;


-- ============================================================
-- QUERY 2: Portfolio Allocation by Sector
-- ============================================================
-- WHAT IT DOES:
--   Shows what percentage of a user's investment is in each
--   sector (e.g., 40% Technology, 30% Healthcare, etc.)
--
-- SQL FEATURES USED:
--   ✅ Multi-table JOIN (Transactions, Assets, Sectors)
--   ✅ Aggregation (SUM)
--   ✅ GROUP BY
--   ✅ Subquery (for percentage calculation)
-- ============================================================
SELECT
    s.sector_name,
    SUM(CASE WHEN t.type = 'BUY' THEN t.total_amount ELSE -t.total_amount END)
        AS sector_investment,
    ROUND(
        SUM(CASE WHEN t.type = 'BUY' THEN t.total_amount ELSE -t.total_amount END) * 100.0 /
        (SELECT SUM(CASE WHEN t2.type = 'BUY' THEN t2.total_amount ELSE -t2.total_amount END)
         FROM Transactions t2
         WHERE t2.user_id = t.user_id),
        2
    ) AS percentage
FROM Transactions t
JOIN Assets a ON t.asset_id = a.asset_id
JOIN Sectors s ON a.sector_id = s.sector_id
WHERE t.user_id = ?   -- Replace ? with user_id parameter
GROUP BY s.sector_name
ORDER BY sector_investment DESC;


-- ============================================================
-- QUERY 3: Top Performing Assets by Return %
-- ============================================================
-- WHAT IT DOES:
--   Ranks assets by their return percentage.
--   Return % = ((current price - avg buy price) / avg buy price) × 100
--
-- SQL FEATURES USED:
--   ✅ JOIN (Assets, Transactions, PriceHistory)
--   ✅ Aggregation (AVG, SUM)
--   ✅ ORDER BY
-- ============================================================
SELECT
    a.symbol,
    a.name,
    ROUND(AVG(t.price_per_unit), 2) AS avg_buy_price,
    (SELECT ph.close_price
     FROM PriceHistory ph
     WHERE ph.asset_id = a.asset_id
     ORDER BY ph.price_date DESC
     LIMIT 1
    ) AS current_price,
    ROUND(
        ((SELECT ph.close_price
          FROM PriceHistory ph
          WHERE ph.asset_id = a.asset_id
          ORDER BY ph.price_date DESC
          LIMIT 1
        ) - AVG(t.price_per_unit)) / AVG(t.price_per_unit) * 100,
        2
    ) AS return_pct
FROM Assets a
JOIN Transactions t ON a.asset_id = t.asset_id
WHERE t.type = 'BUY' AND t.user_id = ?   -- Replace ? with user_id
GROUP BY a.asset_id, a.symbol, a.name
ORDER BY return_pct DESC;


-- ============================================================
-- QUERY 4: Transaction History with Asset & Sector Details
-- ============================================================
-- WHAT IT DOES:
--   Lists all transactions for a user, enriched with the
--   asset name, symbol, type, and sector name.
--
-- SQL FEATURES USED:
--   ✅ Multi-table JOIN (Transactions, Assets, Sectors)
--   ✅ ORDER BY
-- ============================================================
SELECT
    t.transaction_id,
    t.transaction_date,
    t.type,
    a.symbol,
    a.name AS asset_name,
    s.sector_name,
    t.quantity,
    t.price_per_unit,
    t.total_amount
FROM Transactions t
JOIN Assets a ON t.asset_id = a.asset_id
JOIN Sectors s ON a.sector_id = s.sector_id
WHERE t.user_id = ?   -- Replace ? with user_id
ORDER BY t.transaction_date DESC;


-- ============================================================
-- QUERY 5: Monthly Investment Trend
-- ============================================================
-- WHAT IT DOES:
--   Shows how much a user invested each month.
--   Useful for spotting investment patterns over time.
--
-- SQL FEATURES USED:
--   ✅ Aggregation (SUM, COUNT)
--   ✅ GROUP BY (with strftime for date grouping)
--   ✅ ORDER BY
-- ============================================================
SELECT
    strftime('%Y-%m', t.transaction_date) AS month,
    COUNT(*) AS num_transactions,
    SUM(CASE WHEN t.type = 'BUY' THEN t.total_amount ELSE 0 END)  AS total_bought,
    SUM(CASE WHEN t.type = 'SELL' THEN t.total_amount ELSE 0 END) AS total_sold,
    SUM(CASE WHEN t.type = 'BUY' THEN t.total_amount ELSE -t.total_amount END) AS net_investment
FROM Transactions t
WHERE t.user_id = ?   -- Replace ? with user_id
GROUP BY strftime('%Y-%m', t.transaction_date)
ORDER BY month;
