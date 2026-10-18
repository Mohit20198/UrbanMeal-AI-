-- =====================================================================
-- Phase 2 · Step 3 — Amazon Redshift RAW Tables
-- Creates tables in the `"raw"` schema corresponding to the CSV datasets.
-- NOTE: In Amazon Redshift, "raw" is a reserved keyword, so it is
-- enclosed in double quotes ("raw") to avoid syntax errors.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS "raw";

-- 1. Restaurants (raw/restaurants/restaurant.csv)
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

-- 2. Users (raw/users/users.csv)
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

-- 3. Food (raw/food/food.csv)
DROP TABLE IF EXISTS "raw".food;
CREATE TABLE "raw".food (
    _idx            VARCHAR(64),
    f_id            VARCHAR(64),
    item            VARCHAR(256),
    veg_or_non_veg  VARCHAR(64)
);

-- 4. Menu (raw/menu/menu.csv)
DROP TABLE IF EXISTS "raw".menu;
CREATE TABLE "raw".menu (
    _idx      VARCHAR(64),
    menu_id   VARCHAR(64),
    r_id      VARCHAR(64),
    f_id      VARCHAR(64),
    cuisine   VARCHAR(256),
    price     VARCHAR(64)
);

-- 5. Orders (raw/orders/orders.csv)
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

-- 6. Order Items (raw/order_items/order_items.csv)
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

-- 7. Reviews (raw/reviews/reviews.csv)
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

SELECT 'Raw tables created successfully' AS status;
