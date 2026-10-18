-- =====================================================================
-- MASTER REDSHIFT INITIALIZATION & INGESTION SCRIPT
-- NOTE: In Amazon Redshift, "raw" is a reserved keyword, so it is
-- enclosed in double quotes ("raw") to prevent syntax errors.
-- Target Bucket: s3://urbanmeal/RAW/
-- Target Role:   arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. SCHEMAS
-- ---------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS "raw";
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS ai;
CREATE SCHEMA IF NOT EXISTS snapshots;

-- ---------------------------------------------------------------------
-- 2. RAW TABLES DDL
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS "raw".restaurants;
CREATE TABLE "raw".restaurants (
    _idx          VARCHAR(64),
    id            VARCHAR(64),
    name          VARCHAR(512),
    city          VARCHAR(256),
    rating        VARCHAR(64),
    rating_count  VARCHAR(64),
    cost          VARCHAR(64),
    cuisine       VARCHAR(256),
    lic_no        VARCHAR(256),
    link          VARCHAR(1024),
    address       VARCHAR(2048),
    menu          VARCHAR(65535)
);

DROP TABLE IF EXISTS "raw".users;
CREATE TABLE "raw".users (
    _idx            VARCHAR(64),
    user_id         VARCHAR(64),
    name            VARCHAR(256),
    email           VARCHAR(256),
    password        VARCHAR(256),
    age             VARCHAR(64),
    gender          VARCHAR(64),
    marital_status  VARCHAR(64),
    occupation      VARCHAR(128),
    monthly_income  VARCHAR(128),
    education       VARCHAR(128),
    family_size     VARCHAR(64)
);

DROP TABLE IF EXISTS "raw".food;
CREATE TABLE "raw".food (
    _idx            VARCHAR(64),
    f_id            VARCHAR(64),
    item            VARCHAR(256),
    veg_or_non_veg  VARCHAR(64)
);

DROP TABLE IF EXISTS "raw".menu;
CREATE TABLE "raw".menu (
    _idx      VARCHAR(64),
    menu_id   VARCHAR(64),
    r_id      VARCHAR(64),
    f_id      VARCHAR(64),
    cuisine   VARCHAR(256),
    price     VARCHAR(64)
);

DROP TABLE IF EXISTS "raw".orders;
CREATE TABLE "raw".orders (
    order_id          BIGINT,
    order_timestamp   TIMESTAMP,
    order_date        DATE,
    user_id           BIGINT,
    r_id              BIGINT,
    restaurant_city   VARCHAR(256),
    cuisine           VARCHAR(256),
    items_count       INTEGER,
    sales_qty         INTEGER,
    subtotal          DECIMAL(12,2),
    discount          DECIMAL(12,2),
    delivery_fee      DECIMAL(12,2),
    gst               DECIMAL(12,2),
    sales_amount      DECIMAL(12,2),
    currency          VARCHAR(16),
    payment_method    VARCHAR(64),
    order_status      VARCHAR(64),
    customer_rating   DECIMAL(3,1),
    delivery_time_min DECIMAL(8,2)
);

DROP TABLE IF EXISTS "raw".order_items;
CREATE TABLE "raw".order_items (
    order_item_id BIGINT,
    order_id      BIGINT,
    r_id          BIGINT,
    f_id          VARCHAR(64),
    price         DECIMAL(12,2),
    quantity      INTEGER,
    line_amount   DECIMAL(12,2)
);

DROP TABLE IF EXISTS "raw".reviews;
CREATE TABLE "raw".reviews (
    review_id     BIGINT,
    order_id      BIGINT,
    user_id       BIGINT,
    restaurant_id BIGINT,
    rating        DECIMAL(3,1),
    comment       VARCHAR(65535),
    review_date   DATE
);

-- ---------------------------------------------------------------------
-- 3. LOAD DATA VIA S3 COPY
-- ---------------------------------------------------------------------
-- Restaurants
COPY "raw".restaurants
FROM 's3://urbanmeal/RAW/restaurant.csv'
IAM_ROLE 'arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role'
FORMAT AS CSV
IGNOREHEADER 1
ACCEPTINVCHARS
BLANKSASNULL
EMPTYASNULL
MAXERROR 500;

-- Users
COPY "raw".users
FROM 's3://urbanmeal/RAW/users.csv'
IAM_ROLE 'arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role'
FORMAT AS CSV
IGNOREHEADER 1
ACCEPTINVCHARS
BLANKSASNULL
EMPTYASNULL
MAXERROR 500;

-- Food
COPY "raw".food
FROM 's3://urbanmeal/RAW/food.csv'
IAM_ROLE 'arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role'
FORMAT AS CSV
IGNOREHEADER 1
ACCEPTINVCHARS
BLANKSASNULL
EMPTYASNULL
MAXERROR 500;

-- Menu
COPY "raw".menu
FROM 's3://urbanmeal/RAW/menu (1).csv'
IAM_ROLE 'arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role'
FORMAT AS CSV
IGNOREHEADER 1
ACCEPTINVCHARS
BLANKSASNULL
EMPTYASNULL
MAXERROR 500;

-- Orders (~10M rows)
COPY "raw".orders
FROM 's3://urbanmeal/RAW/orders.csv'
IAM_ROLE 'arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role'
FORMAT AS CSV
IGNOREHEADER 1
TIMEFORMAT 'auto'
DATEFORMAT 'auto';

-- Order Items (~23M rows)
COPY "raw".order_items
FROM 's3://urbanmeal/RAW/order_items.csv'
IAM_ROLE 'arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role'
FORMAT AS CSV
IGNOREHEADER 1;

-- Reviews (~300K rows)
COPY "raw".reviews
FROM 's3://urbanmeal/RAW/reviews.csv'
IAM_ROLE 'arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role'
FORMAT AS CSV
IGNOREHEADER 1
DATEFORMAT 'auto'
ACCEPTINVCHARS;

-- ---------------------------------------------------------------------
-- 4. VERIFY COUNTS
-- ---------------------------------------------------------------------
SELECT 'restaurants' AS tbl, count(*) AS cnt FROM "raw".restaurants
UNION ALL SELECT 'users',       count(*) FROM "raw".users
UNION ALL SELECT 'food',        count(*) FROM "raw".food
UNION ALL SELECT 'menu',        count(*) FROM "raw".menu
UNION ALL SELECT 'orders',      count(*) FROM "raw".orders
UNION ALL SELECT 'order_items', count(*) FROM "raw".order_items
UNION ALL SELECT 'reviews',     count(*) FROM "raw".reviews
ORDER BY tbl;
