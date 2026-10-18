-- =====================================================================
-- Phase 2 · Step 4 — Load RAW Tables from S3 using Redshift COPY
-- Pre-configured for your S3 bucket: s3://urbanmeal/RAW/
-- Configured with your IAM Role ARN: arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role
-- NOTE: "raw" is a Redshift reserved word, so it is double-quoted ("raw").
-- =====================================================================

-- 1. Restaurants
COPY "raw".restaurants
FROM 's3://urbanmeal/RAW/restaurant.csv'
IAM_ROLE 'arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role'
FORMAT AS CSV
IGNOREHEADER 1
ACCEPTINVCHARS
BLANKSASNULL
EMPTYASNULL
MAXERROR 500;

-- 2. Users
COPY "raw".users
FROM 's3://urbanmeal/RAW/users.csv'
IAM_ROLE 'arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role'
FORMAT AS CSV
IGNOREHEADER 1
ACCEPTINVCHARS
BLANKSASNULL
EMPTYASNULL
MAXERROR 500;

-- 3. Food
COPY "raw".food
FROM 's3://urbanmeal/RAW/food.csv'
IAM_ROLE 'arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role'
FORMAT AS CSV
IGNOREHEADER 1
ACCEPTINVCHARS
BLANKSASNULL
EMPTYASNULL
MAXERROR 500;

-- 4. Menu
COPY "raw".menu
FROM 's3://urbanmeal/RAW/menu (1).csv'
IAM_ROLE 'arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role'
FORMAT AS CSV
IGNOREHEADER 1
ACCEPTINVCHARS
BLANKSASNULL
EMPTYASNULL
MAXERROR 500;

-- 5. Orders (~10M rows)
COPY "raw".orders
FROM 's3://urbanmeal/RAW/orders.csv'
IAM_ROLE 'arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role'
FORMAT AS CSV
IGNOREHEADER 1
TIMEFORMAT 'auto'
DATEFORMAT 'auto';

-- 6. Order Items (~23M rows)
COPY "raw".order_items
FROM 's3://urbanmeal/RAW/order_items.csv'
IAM_ROLE 'arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role'
FORMAT AS CSV
IGNOREHEADER 1;

-- 7. Reviews (~300K rows)
COPY "raw".reviews
FROM 's3://urbanmeal/RAW/reviews.csv'
IAM_ROLE 'arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role'
FORMAT AS CSV
IGNOREHEADER 1
DATEFORMAT 'auto'
ACCEPTINVCHARS;

-- =====================================================================
-- Sanity Check: Verify Row Counts
-- =====================================================================
SELECT 'restaurants' AS tbl, count(*) AS cnt FROM "raw".restaurants
UNION ALL SELECT 'users',       count(*) FROM "raw".users
UNION ALL SELECT 'food',        count(*) FROM "raw".food
UNION ALL SELECT 'menu',        count(*) FROM "raw".menu
UNION ALL SELECT 'orders',      count(*) FROM "raw".orders
UNION ALL SELECT 'order_items', count(*) FROM "raw".order_items
UNION ALL SELECT 'reviews',     count(*) FROM "raw".reviews
ORDER BY tbl;
