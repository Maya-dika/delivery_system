# Quick Setup Guide

## Prerequisites

- Python 3.8+ installed
- MySQL server running (XAMPP, WAMP, or standalone MySQL)
- Virtual environment created and activated

## First Time Setup

### 1. Configure Environment Variables

A `.env` file has been created with default settings. Update it if needed:
- `MYSQL_DATABASE=delivery_db` (database name)
- `MYSQL_USER=root` (your MySQL username)
- `MYSQL_PASSWORD=` (your MySQL password - leave empty if no password)
- `MYSQL_HOST=127.0.0.1` (localhost)
- `MYSQL_PORT=3306` (default MySQL port)

### 2. Create the Database

**Windows (Command Prompt or PowerShell):**
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS delivery_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

**Or using phpMyAdmin:**
- Open phpMyAdmin (usually at http://localhost/phpmyadmin)
- Click "New" to create a database
- Name it `delivery_db`
- Select collation: `utf8mb4_unicode_ci`
- Click "Create"

### 3. Activate Virtual Environment

**Windows:**
```bash
venv_windows\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Cache Tables

```bash
python manage.py createcachetable default_cache_table
python manage.py createcachetable select2_cache_table
```

### 7. Seed Dummy Data (Optional)

```bash
python manage.py seed_dummy_data
```

### 8. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

## Default Login Credentials (After Seeding)

- **Super Admin:** admin / admin123
- **Warehouse Manager:** wh_manager / manager123
- **Driver:** driver1 / driver123
- **Internal User:** internal_user / user123
- **Supplier:** supplier1 / supplier123
- **Customer:** customer1 / customer123

## Running the Server

**Windows:**
```bash
# Make sure virtual environment is activated
venv_windows\Scripts\activate
python manage.py runserver
```

**Linux/Mac:**
```bash
./start.sh
```

Or manually:
```bash
source venv/bin/activate
python manage.py runserver
```

The server will run on `http://127.0.0.1:8000/` by default.

To run on a specific port:
```bash
python manage.py runserver 8000
```

## Stopping the Server

```bash
./stop.sh
```

Or press `Ctrl+C` if running in foreground.




