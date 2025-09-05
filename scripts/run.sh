#!/bin/bash
# Script to run the ToVéCo Voting Platform

set -e

# Change to project root directory
cd "$(dirname "$0")/.."

# Activate virtual environment and run the application
echo "Starting ToVéCo Voting Platform..."
echo "Syncing dependencies..."
uv sync

echo "Running application on http://0.0.0.0:8000"
uv run uvicorn src.toveco_voting.main:app --host 0.0.0.0 --port 8000 --reload
