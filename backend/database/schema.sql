-- EcoGreen PostgreSQL Database Schema Initialization Script
-- Usage: psql -U postgres -d ecogreen_db -f backend/database/schema.sql

-- Drop existing tables if re-initializing
DROP TABLE IF EXISTS "notification" CASCADE;
DROP TABLE IF EXISTS "notification_log" CASCADE;
DROP TABLE IF EXISTS "transaction" CASCADE;
DROP TABLE IF EXISTS "reviews" CASCADE;
DROP TABLE IF EXISTS "search" CASCADE;
DROP TABLE IF EXISTS "order" CASCADE;
DROP TABLE IF EXISTS "product" CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;

-- 1. User Table
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(50),
    password VARCHAR(200),
    email VARCHAR(200) UNIQUE,
    user_type VARCHAR(50), -- farmer, consumer, admin
    status VARCHAR(50),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    phone VARCHAR(50),
    whatsapp_opt_in BOOLEAN DEFAULT FALSE,
    last_inbound_whatsapp_at TIMESTAMP WITHOUT TIME ZONE,
    notification_language VARCHAR(10) DEFAULT 'en'
);

-- 2. Product Table
CREATE TABLE "product" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id) ON DELETE SET NULL,
    name VARCHAR(150) NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    description TEXT,
    image TEXT,
    location VARCHAR(150),
    quantity INTEGER NOT NULL,
    category VARCHAR(100) DEFAULT 'Vegetables',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Order Table
CREATE TABLE "order" (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES "product"(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    amount DOUBLE PRECISION NOT NULL,
    mpesa_receipt_number VARCHAR(255) DEFAULT 'N/A',
    merchant_request_id VARCHAR(255) DEFAULT 'N/A',
    checkout_request_id VARCHAR(255) DEFAULT 'N/A',
    result_code INTEGER DEFAULT 0,
    result_desc VARCHAR(255) DEFAULT 'Pending',
    order_status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    payment_status VARCHAR(50) NOT NULL DEFAULT 'Unpaid',
    phone_number VARCHAR(50) NOT NULL,
    transaction_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP WITHOUT TIME ZONE,
    cancelled_at TIMESTAMP WITHOUT TIME ZONE,
    delivered_at TIMESTAMP WITHOUT TIME ZONE
);

-- 4. Transaction Table (Razorpay Payments)
CREATE TABLE "transaction" (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES "order"(id) ON DELETE CASCADE,
    razorpay_order_id VARCHAR(255),
    razorpay_payment_id VARCHAR(255),
    razorpay_signature VARCHAR(255),
    amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    status VARCHAR(50) NOT NULL DEFAULT 'Created', -- Created, Success, Failed
    payment_method VARCHAR(50) DEFAULT 'upi',      -- upi, card, netbanking, wallet
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Reviews Table
CREATE TABLE "reviews" (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES "product"(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    comment TEXT,
    rating INTEGER
);

-- 6. Search History Table
CREATE TABLE "search" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    keyword VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. NotificationLog Table
CREATE TABLE "notification_log" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id) ON DELETE SET NULL,
    channel VARCHAR(50) DEFAULT 'whatsapp',
    event_type VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'queued',
    provider_message_id VARCHAR(255),
    error TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Notification (In-App) Table
CREATE TABLE "notification" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_user_type ON "user"(user_type);
CREATE INDEX idx_product_category ON "product"(category);
CREATE INDEX idx_order_status ON "order"(order_status);
CREATE INDEX idx_order_date ON "order"(transaction_date);
CREATE INDEX idx_transaction_order ON "transaction"(order_id);
CREATE INDEX idx_notif_user ON "notification_log"(user_id);
