from django.http import HttpResponseForbidden

from .permissions import get_allowed_order_actions, get_orders_for_user, ALLOWED_ACTIONS_BY_STATUS
from core.utils import render_not_found

from functools import wraps

def order_access_required(required_action=None):
    """
    Decorator for any order view.
    - Filters orders based on user permissions
    - Optionally checks for a specific required action
    - Passes `order`, `allowed_actions`, and `can_edit` to the view
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, order_id=None, *args, **kwargs):
            # Step 1: Get orders user can see
            orders = get_orders_for_user(request.user)

            try:
                order = orders.prefetch_related('exchange_children').get(id=order_id) if order_id else None
            except orders.model.DoesNotExist:
                return render_not_found(request, "You do not have access to this order.")

            # Step 2: Get allowed actions (role-based), then intersect with status-based
            role_allowed = get_allowed_order_actions(request.user)
            allowed_actions = role_allowed

            if order:
                allowed_actions_by_status = ALLOWED_ACTIONS_BY_STATUS.get(order.order_status, [])
                allowed_actions = list(set(role_allowed) & set(allowed_actions_by_status))

                # Dynamic tweaks based on flags
                # If order is cancelled or exchanged, allow returning to supplier (if role permits)
                if order.is_cancelled or order.is_exchanged:
                    # Remove actions that no longer make sense after cancel/exchange
                    for a in [
                        'confirm_order',
                        'out_for_delivery',
                        'delivered_to_customer',
                        'return_and_cancel', 
                        'return_and_exchange'
                    ]:
                        if a in allowed_actions:
                            allowed_actions.remove(a)
                
                if not order.is_cancelled and not order.is_exchanged:
                    # Remove actions that doesn't make sense if not cancelled/exchanged
                    for a in [
                        'returned_to_supplier',
                        'return_to_supplier'
                    ]:
                        if a in allowed_actions:
                            allowed_actions.remove(a)

            # Step 3: If specific action required, enforce it
            if required_action and required_action not in allowed_actions:
                return HttpResponseForbidden("You do not have permission to perform this action.")

            # Step 4: Call the view
            return view_func(
                request,
                order,
                allowed_actions,
                *args, **kwargs
            )
        return wrapper
    return decorator
