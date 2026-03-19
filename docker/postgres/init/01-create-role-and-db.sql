-- Create developer role and database for SUAP (executed at container init)
-- This script is executed by the official Postgres image on first initialization

-- Create role
CREATE ROLE suap_dev WITH LOGIN PASSWORD 'suap_dev';

-- Create database owned by role
CREATE DATABASE suap_idep_dev OWNER suap_dev;

-- Ensure privileges (connect/usage are implicit for owner)
