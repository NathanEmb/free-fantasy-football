#!/bin/bash

# Initialize SQLite database
echo "Initializing SQLite database..."
sqlite3 /app/data/fantasy_football.db < /app/database/schema.sql

# Start FastAPI
echo "Starting FastAPI..."
uv run app/backend/main.py 