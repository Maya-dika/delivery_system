# 🚚 Delivery App

A Django-based delivery management system that handles suppliers, orders, packages, drivers, and warehouses.

---

## 📦 Features

- Multi-role user support: Employees, Suppliers, Customers
- Order creation and tracking
- Warehouse and address management
- Admin dashboard and configuration settings

---

## ⚙️ Prerequisites

Make sure the following are installed on your system:

- Python 3.9+
- pip (Python package manager)
- MySQL Server
- Node.js + npm (for frontend dependencies)
- Git

---

## 🧰 Project Setup

### 1. Clone the Repository

```
git clone git@github.com:your-username/delivery-app.git
cd delivery-app
```

### 2. Create a Virtual Environment

```
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 3. Install Python Dependencies

```
pip install -r requirements.txt
```

### 4. Setup the MySQL Database


```
CREATE DATABASE delivery_db CHARACTER SET UTF8MB4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'delivery_user'@'localhost' IDENTIFIED BY 'admin';
GRANT ALL PRIVILEGES ON delivery_db.* TO 'delivery_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 5. Django settings.py Database Configuration

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'delivery_db',
        'USER': 'delivery_user',
        'PASSWORD': 'admin',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 6. Run Migrations

```
python manage.py makemigrations
python manage.py migrate
```

### 7. Create a Superuser
```
python manage.py createsuperuser
```

### 8. Collect Static Files
```
python manage.py collectstatic
```

### Cache Setup
```
in settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'default_cache_table',
    },
    'select2': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache', 
        'LOCATION': 'select2_cache_table',
    }
}
SELECT2_CACHE_BACKEND = "select2"


Create cache tables
python manage.py createcachetable default_cache_table
python manage.py createcachetable select2_cache_table

```

### 🚀 Run the App Locally
```
python manage.py runserver
```
Then open your browser at: http://localhost:8000

🛠 Admin Panel
Admin URL: http://localhost:8000/admin/

Login using the superuser credentials you created.

