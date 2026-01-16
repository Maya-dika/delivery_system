#!/bin/bash

# Start script for Django Delivery Management System

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Create symlink for MAMP MySQL socket (if MAMP is being used)
if [ -f "/Applications/MAMP/tmp/mysql/mysql.sock" ] && [ ! -L "/tmp/mysql.sock" ]; then
    ln -sf /Applications/MAMP/tmp/mysql/mysql.sock /tmp/mysql.sock
    echo "✓ Created MySQL socket symlink for MAMP"
fi

# Activate virtual environment
source venv/bin/activate

# Check if MySQL is running (optional check)
if ! /Applications/MAMP/Library/bin/mysql -u root -proot -e "SELECT 1" > /dev/null 2>&1; then
    echo "⚠️  Warning: Could not connect to MySQL. Make sure MAMP MySQL is running."
    echo "   You can continue anyway if using SQLite..."
fi

# Start the server
echo "🚀 Starting Django server on port 7001..."
echo "📍 Access the application at: http://localhost:7001/users/login/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python manage.py runserver 7001

