from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'users'

# URLConf
urlpatterns = [
    path("", views.all_system_users, name="users"),
    
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('api/login/', views.login_api, name='login_api'),
    path('logout/', views.user_logout_view, name='logout'),
    path('api/logout/', views.logout_api, name='logout_api'),
    path('password-reset/', views.UserPasswordResetView.as_view(), name='password_reset'),
    path('password-change/', views.UserPasswordChangeView.as_view(), name='password_change'),
    path('password-change-done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),
    
        # users routes
    # path("create/", views.user_create, name='create_user'),
    path("save/<int:pk>/", views.save_user, name='save_user'),
    # path("delete/<int:pk>/", views.user_delete, name='delete_user'),
    
    path("employees/", views.employees, name="employees"),
    path("drivers/", views.drivers, name="drivers"),
    # path("employee/create/", views.employee_create, name='create_employee'),
    path("employee/save/<int:pk>/", views.save_employee, name='save_employee'),
    
    path("suppliers/", views.suppliers, name="suppliers"),
    path("supplier/create/", views.supplier_create, name='create_supplier'),
    path("supplier/update/<int:pk>/", views.supplier_update, name='update_supplier'),
    
    path("customers/", views.customers, name="customers"),
    path("cusotmer/create/", views.customer_create, name='create_customer'),
    path("customer/update/<int:pk>/", views.customer_update, name='update_customer'),
    
    # called from orders app
    path('orders/suppliers/create/', views.create_supplier_modal_view, name='create_supplier_modal'),
    path('orders/customers/create/', views.create_customer_modal_view, name='create_customer_modal'),
    
    path('create-address/<str:entity_type>/<int:entity_id>/', views.create_address, name='create_address'),
        
    path('api/supplier/<int:supplier_id>/addresses/', views.get_supplier_addresses, name='supplier_addresses'),
    path('api/supplier/<int:supplier_id>/warehouse/', views.get_supplier_warehouse, name='supplier_warehouse'),
    path('api/customer/<int:customer_id>/addresses/', views.get_customer_addresses, name='customer_addresses'),
]
