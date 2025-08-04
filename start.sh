#!/bin/bash

echo "Starting Credit Approval System..."

echo "Step 1: Setting up database and running migrations..."
python app.py setup

echo "Step 2: Ingesting data from Excel files..."
python app.py ingest

echo "Step 3: Starting development server..."
python app.py runserver 