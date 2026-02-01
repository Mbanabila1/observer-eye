#!/bin/bash

# Start Django Backend Server
echo "🔧 Starting Django Backend Server..."

cd backend
source venv1/bin/activate
cd observer

echo "Starting Django development server on http://localhost:8000"
python manage.py runserver 8000