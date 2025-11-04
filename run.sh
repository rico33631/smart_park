#!/bin/bash

# Smart Parking System - Quick Start Script

echo "======================================"
echo "Smart Parking System - Quick Start"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Check if database exists
if [ ! -f "parking.db" ]; then
    echo ""
    echo "Database not found. Generating sample data..."
    python generate_sample_data.py
fi

# Start the application
echo ""
echo "======================================"
echo "Starting Smart Parking System..."
echo "======================================"
echo "Dashboard: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo "======================================"
echo ""

python app.py
