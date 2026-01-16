#!/bin/bash

# Stop script for Django Delivery Management System

echo "🛑 Stopping Django server..."

# Find and kill processes running on port 7001
PID=$(lsof -ti:7001)
if [ -z "$PID" ]; then
    echo "ℹ️  No server found running on port 7001"
else
    kill $PID
    echo "✓ Stopped server (PID: $PID)"
fi

# Also kill any manage.py runserver processes
pkill -f "manage.py runserver" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Stopped all Django server processes"
fi

echo "✅ Done"




