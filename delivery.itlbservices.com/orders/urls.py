from django.urls import path
from . import views, api, reporting

app_name = 'orders'

urlpatterns = [
    path('', views.orders_list_view, name='orders_list'),
    path('api/orders/', views.get_filtered_orders, name='orders_data'),
    
    path('new/', views.order_form_view, name='order_create'),
    path('<int:order_id>/edit', views.order_form_view, name='order_update'),
    path('api/save/', api.api_save_order, name='order_api_create'),
    path('api/save/<int:pk>/', api.api_save_order, name='order_api_update'),
    
    path('<int:order_id>/trackings/', views.get_order_trackings, name='order_trackings'),

    path('<int:pk>/confirm/', views.confirm_order, name='confirm_order'),    
    path('confirm-orders/', views.confirm_orders_bulk_api, name='confirm_orders_bulk'),
    
    path('assign-driver/<str:type>/', views.assign_driver_form_view, name='assign_driver_form'),
    path('assign-driver/', views.assign_driver, name='assign_driver'),
    path('arrived-to-warehouse/', views.mark_as_arrived_to_warehouse, name='orders_arrived_to_warehouse'),
    path('out-for-delivery/', views.out_for_delivery_api, name='orders_out_for_delivery'),
    
    
    path('confirm-pickup/driver/', views.confirm_pickup_driver, name='confirm_pickup_driver'),
    path('confirm-delivery/driver/', views.confirm_delivery_driver, name='confirm_delivery_driver'),
    path('send-to-next-warehouse-form/', views.send_to_next_warehouse_form, name='send_to_next_warehouse_form'),
    path('send-to-transit-warehouse/', views.send_to_next_warehouse, name='send_to_next_warehouse'),
    path('send-to-supplier/<int:order_id>/', views.send_to_supplier_api, name='send_to_supplier'),

    path('cancel-order/<int:order_id>/', views.cancel_order_api, name="cancel_order"),
    path('return-and-cancel/<int:order_id>/', views.return_and_cancel_order_api, name="return_and_cancel_order"),
    path('return-and-exchange/<int:order_id>/', views.return_and_exchange_order_api, name="return_and_exchange_order"),

    path('mark-returned/<int:order_id>/', views.mark_returned_to_supplier, name='mark_returned_to_supplier'),
    path('order-delivered/', views.mark_as_delivered, name='orders_delivered'),

    path('order-requests/', views.order_request_list_view, name='order_request_list'),
    path('api/order-requests/', api.api_order_request_list, name='api_order_request_list'),
    path('order-requests/new/', views.order_request_form_view, name='order_request_new'),
    path('order-requests/<int:pk>/edit/', views.order_request_form_view, name='order_request_edit'),
    path('api/order-requests/save', views.order_request_save_api, name='order_request_create_api'),
    path('api/order-requests/<int:pk>/', views.order_request_save_api, name='order_request_update_api'),
    path('order-requests/confirm/', views.confirm_order_requests, name='confirm_order_requests'),
    path('order-requests/cancel/', views.cancel_order_requests, name='cancel_order_requests'),

    
    path("<int:pk>/print-labels/", views.download_order_labels, name="print_labels"),
    path("multi-print-labels/", views.multi_download_order_labels, name="multi_print_labels"),
          
    # Public tracking (no auth)
    path('track/', views.public_track_lookup, name='public_track_lookup'),
    path('track/<str:tracking_number>/', views.public_track_detail, name='public_track_detail'),
    
    # package types, requirements & delivery pricelists
    path('package-types/', views.package_types, name='package_types'),
    path('package-types/create/', views.package_type_create, name='package_type_create'),
    path('package-types/<int:pk>/edit/', views.package_type_update, name='package_type_update'),
    path('package-types/<int:pk>/delete/', views.package_type_delete, name='package_type_delete'),
    
    path('get-package-types/', views.get_package_types_for_pricelist, name='get_package_types_for_pricelist'),
    path('get-supplier-pricelist/', views.get_supplier_pricelist, name='get_supplier_pricelist'),
    path('api/get-supplier-pricelist/', views.get_supplier_pricelist, name='api_get_supplier_pricelist'),
    path('delivery-pricelists/', views.delivery_pricelist_list, name='delivery_pricelist_list'),
    path('api/delivery-pricelists/', api.api_delivery_pricelist_list, name='api_delivery_pricelist_list'),
    path('delivery-pricelists/create/', views.delivery_pricelist_create, name='delivery_pricelist_create'),
    path('delivery-pricelists/<int:pk>/edit/', views.delivery_pricelist_update, name='delivery_pricelist_update'),

    path('package-requirements/', views.package_requirements, name='package_requirements'),
    path('package-requirements/create/', views.package_requirement_create, name='package_requirement_create'),
    path('package-requirements/<int:pk>/edit/', views.package_requirement_update, name='package_requirement_update'),
    path('package-requirements/<int:pk>/delete/', views.package_requirement_delete, name='package_requirement_delete'),
    
    # reporting
    path('reports/account-statement/', reporting.account_statement_view, name='account_statement'),
    path('api/reports/account-statement/', api.api_account_statement, name='api_account_statement'),
    path('reports/general/', reporting.general_report_view, name='general_report'),
    path('api/reports/general/', api.api_general_report, name='api_general_report'),
    path('reports/general/print/', reporting.general_report_print, name='general_report_print'),
    
    # Driver Statement
    path('reports/driver-statement/', reporting.driver_statement_view, name='driver_statement'),
    path('api/reports/driver-statement/', api.api_driver_statement, name='api_driver_statement'),
    path('reports/driver-statement/print/', reporting.driver_statement_print, name='driver_statement_print'),

    # Employees Performance
    path('reports/drivers-performance/', reporting.employees_performance_view, name='employees_performance'),
    path('api/reports/drivers-performance/', api.api_employees_performance, name='api_employees_performance'),
    path('reports/drivers-performance/print/', reporting.employees_performance_print, name='employees_performance_print'),
]
