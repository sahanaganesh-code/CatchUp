#!/bin/bash
# Backend startup script

echo "Starting CatchUp Backend..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and add your Gemini API key"
    exit 1
fi

# Run the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
