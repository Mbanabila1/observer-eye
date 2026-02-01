#!/bin/bash

# Start FastAPI Middleware Server
echo "⚡ Starting FastAPI Middleware Server..."

cd middleware
source venv0/bin/activate

echo "Starting FastAPI development server on http://localhost:8400"
python main.py