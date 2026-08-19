# Olist E-Commerce Database Schema Reference

> Based on the **Olist Brazilian E-Commerce Public Dataset** (Kaggle).
> All data inspected and loaded in Module 3. This document reflects the **actual** schema in `data/olist.db`.

---

## Overview

The database contains **9 tables** covering orders placed on the Olist marketplace between **September 2016 and October 2018**. Orders flow through several statuses and link customers, products, sellers, payments, and reviews.

**Total rows across all tables:** ~1,547,851

---

## Entity-Relationship Diagram

```
customers ──(1:N)──► orders ──(1:N)──► order_items ──(N:1)──► products ──(N:1)──► product_category_name_translation
                         │                   │
                         │                   └──(N:1)──► sellers
                         │
                         ├──(1:N)──► order_payments
                         │
                         └──(1:N)──► order_reviews

geolocation (standalone, joins via zip_code_prefix to customers or sellers)
```

---

## Table Details

### 1. `orders` (99,441 rows)
The central fact table. One row per order.

| Column | Type | Description |
|--------|------|-------------|
| `order_id` | TEXT (PK) | Unique order identifier |
| `customer_id` | TEXT (FK → customers) | References `customers.customer_id` |
| `order_status` | TEXT | One of: `delivered` (96,478), `shipped` (1,107), `canceled` (625), `unavailable` (609), `invoiced` (314), `processing` (301), `created` (5), `approved` (2) |
| `order_purchase_timestamp` | TEXT | When the order was placed (ISO format, range: 2016-09-04 to 2018-10-17) |
| `order_approved_at` | TEXT | Payment approval timestamp (nullable) |
| `order_delivered_carrier_date` | TEXT | When the order was handed to the carrier (nullable) |
| `order_delivered_customer_date` | TEXT | Actual delivery date to customer (nullable) |
| `order_estimated_delivery_date` | TEXT | Estimated delivery date shown to customer |

---

### 2. `customers` (99,441 rows)
One row per order-customer pair. A single real customer (`customer_unique_id`) may appear multiple times with different `customer_id` values across orders.

| Column | Type | Description |
|--------|------|-------------|
| `customer_id` | TEXT (PK) | Unique per order (matches `orders.customer_id`) |
| `customer_unique_id` | TEXT | De-duplicated customer identifier |
| `customer_zip_code_prefix` | INTEGER | First 5 digits of customer zip code |
| `customer_city` | TEXT | Customer city name |
| `customer_state` | TEXT | Customer state abbreviation (2 letters, e.g., SP, RJ) |

---

### 3. `order_items` (112,650 rows)
One row per item within an order. An order can have multiple items.

| Column | Type | Description |
|--------|------|-------------|
| `order_id` | TEXT (FK → orders) | References `orders.order_id` |
| `order_item_id` | INTEGER | Sequential item number within the order (1, 2, 3…) |
| `product_id` | TEXT (FK → products) | References `products.product_id` |
| `seller_id` | TEXT (FK → sellers) | References `sellers.seller_id` |
| `shipping_limit_date` | TEXT | Deadline for seller to ship |
| `price` | REAL | Item price in BRL |
| `freight_value` | REAL | Freight cost for this item in BRL |

**Composite key:** (`order_id`, `order_item_id`)

---

### 4. `order_payments` (103,886 rows)
One row per payment installment/method per order. An order can have multiple payment rows (e.g., part credit card, part voucher).

| Column | Type | Description |
|--------|------|-------------|
| `order_id` | TEXT (FK → orders) | References `orders.order_id` |
| `payment_sequential` | INTEGER | Sequential payment number within the order |
| `payment_type` | TEXT | One of: `credit_card` (76,795), `boleto` (19,784), `voucher` (5,775), `debit_card` (1,529), `not_defined` (3) |
| `payment_installments` | INTEGER | Number of installments chosen |
| `payment_value` | REAL | Payment amount in BRL |

---

### 5. `order_reviews` (99,224 rows)
One row per review. Most orders have exactly one review.

| Column | Type | Description |
|--------|------|-------------|
| `review_id` | TEXT | Unique review identifier |
| `order_id` | TEXT (FK → orders) | References `orders.order_id` |
| `review_score` | INTEGER | Rating from 1 (worst) to 5 (best) |
| `review_comment_title` | TEXT | Optional review title (often NULL) |
| `review_comment_message` | TEXT | Optional review text (often NULL) |
| `review_creation_date` | TEXT | When the review was created |
| `review_answer_timestamp` | TEXT | When the review was answered/posted |

---

### 6. `products` (32,951 rows)
One row per product.

| Column | Type | Description |
|--------|------|-------------|
| `product_id` | TEXT (PK) | Unique product identifier |
| `product_category_name` | TEXT | Category in Portuguese (nullable — 610 NULLs). FK → `product_category_name_translation` |
| `product_name_lenght` | REAL | Character count of product name (nullable — 610 NULLs). Note: "lenght" is a typo in the original dataset |
| `product_description_lenght` | REAL | Character count of product description (nullable) |
| `product_photos_qty` | REAL | Number of product photos (nullable) |
| `product_weight_g` | REAL | Product weight in grams (nullable — 2 NULLs) |
| `product_length_cm` | REAL | Product length in cm (nullable) |
| `product_height_cm` | REAL | Product height in cm (nullable) |
| `product_width_cm` | REAL | Product width in cm (nullable) |

---

### 7. `sellers` (3,095 rows)
One row per seller.

| Column | Type | Description |
|--------|------|-------------|
| `seller_id` | TEXT (PK) | Unique seller identifier |
| `seller_zip_code_prefix` | INTEGER | First 5 digits of seller zip code |
| `seller_city` | TEXT | Seller city name |
| `seller_state` | TEXT | Seller state abbreviation (2 letters) |

---

### 8. `product_category_name_translation` (71 rows)
Lookup table mapping Portuguese category names to English.

| Column | Type | Description |
|--------|------|-------------|
| `product_category_name` | TEXT (PK) | Category name in Portuguese |
| `product_category_name_english` | TEXT | Category name in English |

**Note:** 13 products have category names not present in this translation table.

---

### 9. `geolocation` (1,000,163 rows)
Latitude/longitude data by zip code prefix. Many-to-one relationship (multiple lat/lng entries per zip code). Joins to `customers` or `sellers` via `zip_code_prefix`.

| Column | Type | Description |
|--------|------|-------------|
| `geolocation_zip_code_prefix` | INTEGER | Zip code prefix (joins to `customer_zip_code_prefix` or `seller_zip_code_prefix`) |
| `geolocation_lat` | REAL | Latitude |
| `geolocation_lng` | REAL | Longitude |
| `geolocation_city` | TEXT | City name |
| `geolocation_state` | TEXT | State abbreviation |

---

## Key Relationships (all verified — 0 orphans)

| From | Column | To | Column | Relationship |
|------|--------|----|--------|-------------|
| `orders` | `customer_id` | `customers` | `customer_id` | N:1 (every order has a customer) |
| `order_items` | `order_id` | `orders` | `order_id` | N:1 (every item belongs to an order) |
| `order_items` | `product_id` | `products` | `product_id` | N:1 (every item references a product) |
| `order_items` | `seller_id` | `sellers` | `seller_id` | N:1 (every item is sold by a seller) |
| `order_payments` | `order_id` | `orders` | `order_id` | N:1 (every payment belongs to an order) |
| `order_reviews` | `order_id` | `orders` | `order_id` | N:1 (every review belongs to an order) |
| `products` | `product_category_name` | `product_category_name_translation` | `product_category_name` | N:1 (13 products have untranslated categories) |
| `geolocation` | `geolocation_zip_code_prefix` | `customers` / `sellers` | `*_zip_code_prefix` | Loose join (many geolocations per zip) |

---

## Common Query Patterns

- **Revenue:** `SUM(price)` or `SUM(price + freight_value)` from `order_items`, typically filtered to `orders.order_status = 'delivered'`
- **By category:** JOIN `order_items` → `products` → `product_category_name_translation`
- **By time:** Filter/group on `orders.order_purchase_timestamp` (stored as TEXT in ISO format — use `strftime()` or `substr()` for date extraction in SQLite)
- **Delivery time:** `julianday(order_delivered_customer_date) - julianday(order_purchase_timestamp)` from `orders`
- **By geography:** JOIN `orders` → `customers` and use `customer_state` or `customer_city`
