# Quick Setup Guide

## First Time Setup

1. **Make sure MySQL is running:**
   ```bash
   mysql -u root -proot -e "SELECT 1;"
   ```

2. **Create the database:**
   ```bash
   mysql -u root -proot -e "CREATE DATABASE IF NOT EXISTS delivery CHARACTER SET UTF8MB4 COLLATE utf8mb4_unicode_ci;"
   ```

3. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create cache tables:**
   ```bash
   python manage.py createcachetable default_cache_table
   python manage.py createcachetable select2_cache_table
   ```

6. **Seed dummy data:**
   ```bash
   python manage.py seed_dummy_data
   ```

7. **Collect static files:**
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

```bash
./start.sh
```

Or manually:
```bash
source venv/bin/activate
python manage.py runserver 7001
```

## Stopping the Server

```bash
./stop.sh
```

Or press `Ctrl+C` if running in foreground.




