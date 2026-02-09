from users.models import UserTypes, EmployeeTypes

def get_user_menus(user):
    menu = []

    # Orders menu
    if user.user_type == UserTypes.EMPLOYEE:
        emp = user.employee_user.first()
        if emp and emp.employee_type == EmployeeTypes.ADMIN:
            menu.append({"name": "Orders", "url": "/orders/", "icon": "fa-cubes"})
            menu.append({"name": "Order Requests", "url": "/orders/order-requests/", "icon": "fa-cart-plus"})
            menu.append({"name": "Merchants", "url": "/users/suppliers/", "icon": "fa-user-tie"})
            menu.append({"name": "Account Statement", "url": "/orders/reports/account-statement/", "icon": "fa-chart-line"})
            menu.append({"name": "General Report", "url": "/orders/reports/general/", "icon": "fa-table"})
            menu.append({"name": "Driver Statement", "url": "/orders/reports/driver-statement/", "icon": "fa-id-badge"})
            menu.append({"name": "Drivers Performance", "url": "/orders/reports/drivers-performance/", "icon": "fa-users"})
            menu.append({"name": "Warehouses", "url": "/warehouses", "icon": "fa-warehouse"})
            menu.append({"name": "Routing Rules", "url": "/routing-rules/", "icon": "fa-route"})
            menu.append({"name": "Stock Locations", "url": "/stock-locations", "icon": "fa-location-arrow"})
            menu.append({"name": "Package Types", "url": "/orders/package-types/", "icon": "fa-box-open"})
            menu.append({"name": "Package Requirements", "url": "/orders/package-requirements/", "icon": "fa-cube"})
            menu.append({"name": "Delivery Pricelists", "url": "/orders/delivery-pricelists/", "icon": "fa-list-alt"})
            menu.append({"name": "Internal Employees", "url": "/users/employees/", "icon": "fa-user-friends"})
            menu.append({"name": "Drivers", "url": "/users/drivers/", "icon": "fa-truck"})
            menu.append({"name": "Customers", "url": "/users/customers/", "icon": "fa-user-tag"})
            menu.append({"name": "Currencies", "url": "/currencies", "icon": "fa-dollar-sign"})
            menu.append({"name": "Accounts", "url": "/accounts", "icon": "fa-money-bill"})
            menu.append({"name": "Company Profile", "url": "/company-profile", "icon": "fa-cog"})
            
        if emp and emp.employee_type == EmployeeTypes.WAREHOUSE_MANAGER:
            menu.append({"name": "Orders", "url": "/orders/", "icon": "fa-cubes"})
            menu.append({"name": "Order Requests", "url": "/orders/order-requests/", "icon": "fa-cart-plus"})
            menu.append({"name": "Merchants", "url": "/users/suppliers/", "icon": "fa-user-tie"})
            menu.append({"name": "Account Statement", "url": "/orders/reports/account-statement/", "icon": "fa-chart-line"})
            menu.append({"name": "General Report", "url": "/orders/reports/general/", "icon": "fa-table"})
            menu.append({"name": "Driver Statement", "url": "/orders/reports/driver-statement/", "icon": "fa-id-badge"})
            menu.append({"name": "Drivers Performance", "url": "/orders/reports/drivers-performance/", "icon": "fa-users"})
            menu.append({"name": "Package Types", "url": "/orders/package-types/", "icon": "fa-box-open"})
            menu.append({"name": "Package Requirements", "url": "/orders/package-requirements/", "icon": "fa-cube"})
            menu.append({"name": "Delivery Pricelists", "url": "/orders/delivery-pricelists/", "icon": "fa-list-alt"})
            menu.append({"name": "Internal Employees", "url": "/users/employees/", "icon": "fa-user-friends"})
            menu.append({"name": "Drivers", "url": "/users/drivers/", "icon": "fa-truck"})
            menu.append({"name": "Customers", "url": "/users/customers/", "icon": "fa-user-tag"})
            
        elif emp and emp.employee_type == EmployeeTypes.INTERNAL_USER:
            menu.append({"name": "Orders", "url": "/orders/", "icon": "fa-cubes"})
            menu.append({"name": "Order Requests", "url": "/orders/order-requests/", "icon": "fa-cart-plus"})
            menu.append({"name": "Merchants", "url": "/users/suppliers/", "icon": "fa-user-tie"})
            menu.append({"name": "Account Statement", "url": "/orders/reports/account-statement/", "icon": "fa-chart-line"})
            menu.append({"name": "General Report", "url": "/orders/reports/general/", "icon": "fa-table"})
            menu.append({"name": "Driver Statement", "url": "/orders/reports/driver-statement/", "icon": "fa-id-badge"})
            menu.append({"name": "Employees Performance", "url": "/orders/reports/employees-performance/", "icon": "fa-users"})
            menu.append({"name": "Customers", "url": "/users/customers/", "icon": "fa-user-tag"})
            
        elif emp and emp.employee_type == EmployeeTypes.DRIVER:
            menu.append({"name": "My Orders", "url": "/orders/", "icon": "fa-truck"})
            menu.append({"name": "My Order Requests", "url": "/orders/order-requests/", "icon": "fa-cart-plus"})

    if user.user_type == UserTypes.SUPPLIER:
        menu.append({"name": "My Orders", "url": "/orders/", "icon": "fa-cubes"})
        menu.append({"name": "My Order Requests", "url": "/orders/order-requests/", "icon": "fa-cart-plus"})

    if user.user_type == UserTypes.CUSTOMER:
        menu.append({"name": "My Orders", "url": "/orders/", "icon": "fa-cubes"})

    return menu
