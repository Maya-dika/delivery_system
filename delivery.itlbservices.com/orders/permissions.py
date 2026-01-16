from users.models import EmployeeTypes, UserTypes
from orders.models import Order, OrderRequest, OrderStatuses

ALLOWED_ACTIONS_BY_PERMISSIONS = {
    (UserTypes.EMPLOYEE, EmployeeTypes.ADMIN): [
        "view", "edit", "assign_driver", "cancel_tracking", "delete_tracking", "confirm_order",
        "arrived_to_warehouse", "generate_routes", "send_to_next_warehouse",
        "transfer_to_warehouse", "out_for_delivery", "delivered_to_customer", "cancel_order",
        "return_and_cancel", "return_and_exchange", "returned_to_supplier", "return_to_supplier",
    ],
    (UserTypes.EMPLOYEE, EmployeeTypes.WAREHOUSE_MANAGER): [
        "view", "edit", "assign_driver", "cancel_tracking", "delete_tracking", "confirm_order",
        "arrived_to_warehouse", "generate_routes", "send_to_next_warehouse",
        "transfer_to_warehouse", "out_for_delivery", "delivered_to_customer",
        "cancel_order", "return_and_cancel",  "return_and_exchange", "returned_to_supplier", "return_to_supplier",
    ],
    (UserTypes.EMPLOYEE, EmployeeTypes.INTERNAL_USER): [
        "view", "edit", "assign_driver", "cancel_tracking", "delete_tracking", "confirm_order",
        "arrived_to_warehouse", "generate_routes", "send_to_next_warehouse",
        "out_for_delivery", "delivered_to_customer", 
        "cancel_order", "return_and_cancel",  "return_and_exchange", "returned_to_supplier", "return_to_supplier",
    ],
    (UserTypes.EMPLOYEE, EmployeeTypes.DRIVER): [
        "view", "confirm_pickup", "returned_to_supplier", "delivered_to_customer"
    ],
    (UserTypes.SUPPLIER, None): ["view"],
    (UserTypes.CUSTOMER, None): ["view"],
}

def get_allowed_order_actions(user):
    """Return allowed actions for this user."""
    if user.user_type == UserTypes.EMPLOYEE:
        emp = user.employee_user.first()
        if not emp:
            return []
        return ALLOWED_ACTIONS_BY_PERMISSIONS.get(
            (user.user_type, emp.employee_type),
            []
        )
    return ALLOWED_ACTIONS_BY_PERMISSIONS.get((user.user_type, None), [])


# Define allowed actions for each status
ALLOWED_ACTIONS_BY_STATUS = {
    OrderStatuses.draft: [
        'edit',
        'confirm_order',
        'cancel_order',
    ],
    OrderStatuses.confirmed: [
        'edit',
        'assign_driver',
        'arrived_to_warehouse',
        # 'generate_routes',
        'cancel_order',
        'confirm_pickup'
    ],
    OrderStatuses.pending_pickup: [
        'edit',
        'assign_driver',
        'arrived_to_warehouse',
        # 'generate_routes',
        'cancel_order',
        'confirm_pickup'
    ],
    OrderStatuses.pickup_confirmed: [
        'edit',
        'assign_driver',
        'arrived_to_warehouse',
        # 'generate_routes',
        'return_and_cancel'
    ],
    OrderStatuses.in_warehouse: [
        'edit',
        'assign_driver',
        # 'arrived_to_warehouse',
        # 'generate_routes',
        'send_to_next_warehouse',
        'transfer_to_warehouse',
        'out_for_delivery',
        'return_and_cancel',
        'return_to_supplier'
    ],
    OrderStatuses.in_warehouse_transit: [
        'edit',
        'assign_driver',
        'arrived_to_warehouse',
        # 'generate_routes',
        'send_to_next_warehouse',
        'transfer_to_warehouse',
        'return_and_cancel',
        'return_to_supplier',
    ],
    OrderStatuses.out_for_delivery: [
        'edit',
        'assign_driver',
        'delivered_to_customer',
        'send_to_next_warehouse', # if delivery failed
        'return_and_cancel',
        'return_to_supplier'
    ],
    OrderStatuses.delivered: [
        'return_and_cancel',  # in case of error and no exchange needed
        'return_and_exchange',  # if exchange needed
    ],
    OrderStatuses.cancelled: [],
    OrderStatuses.returned: [],
    OrderStatuses.out_for_supplier: [
        'returned_to_supplier'
    ]
}


def get_orders_for_user(user):
    # ADMIN / WAREHOUSE_MANAGER / INTERNAL_USER → see all orders
    if user.user_type == UserTypes.EMPLOYEE:
        emp = user.employee_user.first()
        if emp and emp.employee_type in [
            EmployeeTypes.ADMIN,
            EmployeeTypes.WAREHOUSE_MANAGER,
            EmployeeTypes.INTERNAL_USER
        ]:
            return Order.objects.all()

        # DRIVER → only assigned orders via OrderTracking
        if emp and emp.employee_type == EmployeeTypes.DRIVER:
            return Order.objects.filter(
                order_tracking__driver=emp
            ).distinct()

    # SUPPLIER → only their orders
    if user.user_type == UserTypes.SUPPLIER:
        return Order.objects.filter(supplier__user=user)

    # CUSTOMER → only their orders
    if user.user_type == UserTypes.CUSTOMER:
        return Order.objects.filter(customer__user=user)

    # Default: no access
    return Order.objects.none()


def get_order_requests_for_user(user):
    # ADMIN / WAREHOUSE_MANAGER / INTERNAL_USER → see all order requests
    if user.user_type == UserTypes.EMPLOYEE:
        emp = user.employee_user.first()
        if emp and emp.employee_type in [
            EmployeeTypes.ADMIN,
            EmployeeTypes.WAREHOUSE_MANAGER,
            EmployeeTypes.INTERNAL_USER
        ]:
            return OrderRequest.objects.all()

        # DRIVER → only assigned orders via OrderTracking
        if emp and emp.employee_type == EmployeeTypes.DRIVER:
            return OrderRequest.objects.filter(
                driver=emp
            ).distinct()

    # SUPPLIER → only their orders
    if user.user_type == UserTypes.SUPPLIER:
        return OrderRequest.objects.filter(supplier__user=user)

    # Default: no access
    return OrderRequest.objects.none()