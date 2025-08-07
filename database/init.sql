-- Fantasy Football Database Initialization Script
-- This script creates the database and runs the schema

-- Create the database if it doesn't exist
SELECT 'CREATE DATABASE fantasy_football'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'fantasy_football')\gexec

-- Connect to the fantasy_football database
\c fantasy_football;

-- Run the schema
\i schema.sql; 