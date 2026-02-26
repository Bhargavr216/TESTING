-- Bootstrap script for Idea 1 validation project
-- Usage (from psql): \i idea1_project/db/setup_database.sql

-- 1) Create database if not present
SELECT 'CREATE DATABASE idea1_testing'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'idea1_testing')\gexec

\c idea1_testing;

-- 2) Drop existing tables (safe reset)
DROP TABLE IF EXISTS operations;
DROP TABLE IF EXISTS fulfilment;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS job_queue;

-- 3) Create tables
CREATE TABLE orders (
  order_id       TEXT PRIMARY KEY,
  status         TEXT NOT NULL,
  total_amount   NUMERIC(12,2) NOT NULL,
  order_metadata JSONB NOT NULL,
  created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE fulfilment (
  fulfilment_id       TEXT PRIMARY KEY,
  order_id            TEXT NOT NULL,
  status              TEXT NOT NULL,
  fulfilment_details  JSONB NOT NULL,
  created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE operations (
  order_id       TEXT NOT NULL,
  operation_type TEXT NOT NULL,
  status         TEXT NOT NULL,
  created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
  CONSTRAINT operations_uniq UNIQUE (order_id, operation_type)
);

CREATE TABLE audit_logs (
  order_id    TEXT NOT NULL,
  audit_id    TEXT,
  operation   TEXT NOT NULL,
  status      TEXT NOT NULL,
  exception   TEXT,
  created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE job_queue (
  order_id      TEXT NOT NULL,
  operation     TEXT NOT NULL,
  exception     TEXT,
  ordermetadata JSONB,
  retry_count   INTEGER NOT NULL DEFAULT 0,
  created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 4) Seed values

-- Happy path
INSERT INTO orders (order_id, status, total_amount, order_metadata) VALUES
('ORD123', 'CONFIRMED', 500, '{"customer":{"name":"Bhargav","city":"Hyderabad"},"payment":{"method":"CARD"}}');

INSERT INTO fulfilment (fulfilment_id, order_id, status, fulfilment_details) VALUES
('F001', 'ORD123', 'ALLOCATED', '{"deliverySlot":{"startTime":"10:00","endTime":"12:00"}}');

INSERT INTO operations (order_id, operation_type, status) VALUES
('ORD123', 'ORDER_CREATED', 'SUCCESS'),
('ORD123', 'ORDER_VALIDATED', 'SUCCESS');

INSERT INTO audit_logs (order_id, audit_id, operation, status, exception) VALUES
('ORD123', 'AUDIT_ORD123_001', 'ORDER_CREATED', 'SUCCESS', NULL),
('ORD123', 'AUDIT_ORD123_002', 'ORDER_VALIDATED', 'SUCCESS', NULL);

-- Negative routing to queue
INSERT INTO audit_logs (order_id, audit_id, operation, status, exception) VALUES
('ORD124', 'AUDIT_ORD124_001', 'CREATE', 'SUCCESS', NULL),
('ORD124', 'AUDIT_ORD124_002', 'VALIDATE', 'FAILED', 'INVALID_ORDER_DATA');

INSERT INTO job_queue (order_id, operation, exception, ordermetadata, retry_count) VALUES
('ORD124', 'ERROR', 'INVALID_ORDER_DATA', '{"customer":{"name":"Bhargav"}}', 0);

-- Retry scenario (validate fails 3 times)
INSERT INTO audit_logs (order_id, audit_id, operation, status, exception) VALUES
('ORD500', 'AUDIT_ORD500_001', 'CREATE', 'SUCCESS', NULL),
('ORD500', 'AUDIT_ORD500_002', 'VALIDATE', 'FAILED', 'VALIDATION_FAILED_RETRY'),
('ORD500', 'AUDIT_ORD500_003', 'VALIDATE', 'FAILED', 'VALIDATION_FAILED_RETRY'),
('ORD500', 'AUDIT_ORD500_004', 'VALIDATE', 'FAILED', 'VALIDATION_FAILED_RETRY');

INSERT INTO job_queue (order_id, operation, exception, ordermetadata, retry_count) VALUES
('ORD500', 'VALIDATE', 'VALIDATION_FAILED_RETRY', '{"customer":{"name":"RetryCustomer"}}', 3);

-- 5) Quick verification counts
SELECT 'orders' AS table_name, COUNT(*) AS total_rows FROM orders
UNION ALL
SELECT 'fulfilment', COUNT(*) FROM fulfilment
UNION ALL
SELECT 'operations', COUNT(*) FROM operations
UNION ALL
SELECT 'audit_logs', COUNT(*) FROM audit_logs
UNION ALL
SELECT 'job_queue', COUNT(*) FROM job_queue;
