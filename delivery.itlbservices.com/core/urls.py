from django.urls import path
from django.shortcuts import render
from . import views, api

# URLConf
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("companies", views.companies, name="companies"),
    path("company-profile", views.update_company_profile, name="company_profile"),
    path("warehouses", views.warehouses, name="warehouses"),
    path("api/warehouses/", api.api_warehouse_list, name="api_warehouse_list"),
    path("warehouses/create", views.create_warehouse, name="create_warehouse"),
    path("warehouses/<int:pk>/edit/", views.update_warehouse, name="update_warehouse"),
    path("warehouses/archive", views.archive_warehouses, name="archive_warehouses"),
    path("warehouses/delete", views.delete_warehouses, name="delete_warehouses"),
    path("warehouses/unarchive", views.unarchive_warehouses, name="unarchive_warehouses"),
    path("currencies", views.currencies, name="currencies"),
    path("currencies/create", views.create_currency, name="create_currency"),
    path("currencies/<int:pk>/delete", views.delete_currency, name="delete_currency"),
    path("stock-locations", views.get_stock_locations, name="stock_locations"),
    path("stock-locations/create", views.stock_location_form_view, name="create_stock_location"),
    path("stock-locations/<int:pk>/edit/", views.stock_location_form_view, name="update_stock_location"),
    path("stock-locations/archive", views.archive_stock_locations, name="archive_stock_locations"),
    path("stock-locations/unarchive", views.unarchive_stock_locations, name="unarchive_stock_locations"),
    path("stock-locations/delete", views.delete_stock_locations, name="delete_stock_locations"),
    path("accounts", views.accounts_list, name="accounts"),
    path("accounts/create", views.account_form_view, name="create_account"),
    path("accounts/<int:pk>/edit/", views.account_form_view, name="update_account"),
    path("accounts/<int:pk>/delete", views.delete_account, name="delete_account"),
    
    path('routing-rules/', views.routing_rule_list, name='routing_rules'),
    path('routing-rules/add/', views.routing_rule_form_view, name='add_routing_rule'),
    path('routing-rules/<int:pk>/edit/', views.routing_rule_form_view, name='edit_routing_rule'),
]
