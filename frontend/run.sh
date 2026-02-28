#!/bin/bash
# Frontend startup script

echo "Starting CatchUp Frontend..."

# Check for .env.local file
if [ ! -f ".env.local" ]; then
    echo "Warning: .env.local file not found!"
    echo "Using default API URL: http://localhost:8000"
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Run the dev server
npm run dev
