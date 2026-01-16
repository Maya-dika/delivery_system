from django.db import transaction
from django.http import JsonResponse

from orders.models import Order, OrderTracking, OrderStatuses, OrderTrackingStatuses
from orders.models.order_request import OrderRequestStatuses
from users.models import Employee
from orders.permissions import get_order_requests_for_user
from core.models import StockLocation, NumberSequence
from core import utils
from .whatsapp import send_verification_code, send_order_scheduled

import datetime

def _format_with_prefix(prefix: str, number: int, length: int) -> str:
    return f"{prefix}{str(number).zfill(length)}"


def _next_sequence(company, key: str) -> int:
    return NumberSequence.next(company, key)

def generate_order_tracking_number(order: Order) -> str:
    company = order.company
    seq_num = _next_sequence(company, 'order')
    prefix = getattr(company, 'order_prefix', '') or ''
    length = getattr(company, 'order_seq_length', 6) or 6
    return _format_with_prefix(prefix, seq_num, length)

def set_orders_out_for_delivery(order_ids, user, driver_id):
    failed = []

    try:
        with transaction.atomic():
            # Bulk fetch orders in one query
            orders = {order.id: order for order in Order.objects.select_for_update().filter(id__in=order_ids)}
            # Validate driver if provided
            driver = Employee.objects.filter(pk=driver_id, employee_type='driver', active=True).first()
            if not driver:
                return {'success': False, 'error': 'Driver not found (or inactive)'}

            emp = getattr(user, 'employee_user', None)
            emp = emp.first() if emp else None
            user_warehouse_id = getattr(emp, 'warehouse_id', None)

            for order_id in order_ids:
                order = orders.get(order_id)
                if not order:
                    failed.append({'order_id': order_id, 'reason': 'Order not found'})
                    continue
                    
                if order.order_status not in [OrderStatuses.in_warehouse, OrderStatuses.in_warehouse_transit]:
                    failed.append({'order_id': order.tracking_number, 'reason': 'Order should be In Warehouse to go out for delivery!'})
                    continue

                # Determine current location (last completed warehouse transaction)
                last_tracking = (OrderTracking.objects
                    .filter(order=order, receiver__location_type='warehouse', tracking_status='done')
                    .order_by('-effective_date', '-created_at')
                    .first())

                if not last_tracking:
                    failed.append({'order_id': order.tracking_number, 'reason': 'Failed to determine order location'})
                    continue
                
                # Enforce: user can only send orders from their warehouse
                current_wh_id = getattr(last_tracking.receiver, 'warehouse_id', None)
                if not user_warehouse_id or current_wh_id != user_warehouse_id:
                    failed.append({'order_id': order.tracking_number, 'reason': 'You can only send orders from your warehouse'})
                    continue

                sender_location = last_tracking.receiver
                customer_location = StockLocation.objects.filter(location_type='customer').first()
                if not customer_location:
                    failed.append({'order_id': order.tracking_number, 'reason': 'Customer stock location not configured'})
                    # if not customer_location then block the whole process
                    break

                # Find or create delivery tracking from current warehouse to customer
                delivery_tracking = OrderTracking.objects.filter(
                    order_id=order_id,
                    # sender=sender_location,
                    receiver=customer_location,
                    tracking_status__in=['draft', 'pending']
                ).first()

                if not delivery_tracking:
                    delivery_tracking = OrderTracking.objects.create(
                        order=order,
                        sender=sender_location,
                        receiver=customer_location,
                        sender_address=sender_location.warehouse.address if sender_location and sender_location.warehouse else None,
                        receiver_address=order.customer_address,
                        driver=driver,
                        tracking_status=OrderTrackingStatuses.pending,
                        created_by=user,
                        created_at=datetime.datetime.now()
                    )
                else:
                    delivery_tracking.sender = sender_location
                    delivery_tracking.sender_address = sender_location.warehouse.address if sender_location and sender_location.warehouse else None
                    delivery_tracking.receiver_address = order.customer_address
                    delivery_tracking.tracking_status = OrderTrackingStatuses.pending
                    delivery_tracking.driver = driver
                    delivery_tracking.updated_by = user
                    delivery_tracking.save()

                order.order_status = OrderStatuses.out_for_delivery
                # Update driver commission from driver profile (USD)
                try:
                    order.driver_commission = getattr(driver, 'commission', 0) or 0
                except Exception:
                    order.driver_commission = 0
                order.save(update_fields=['order_status', 'driver_commission'])

                # send phone verification code to customer via WhatsApp
                send_verification_code(order)
                            
            return {'success': True,  'failed_orders': failed}

    except Exception as e:
        failed.append({'order_id': order_id, 'error': str(e)})
        return {'success': False, 'error': str(e), 'failed_orders': failed}


def confirm_orders_bulk(order_ids, user):
    """Confirm multiple orders by delegating to confirm_order_result per order.

    Handles string/int IDs robustly and aggregates failed orders.
    """
    failed = []
    try:
        # Normalize IDs to integers for queryset and mapping
        try:
            ids_int = [int(x) for x in order_ids]
        except Exception:
            # If conversion fails, fall back to empty (all will be reported as not found)
            ids_int = []

        with transaction.atomic():
            orders = {o.id: o for o in Order.objects.select_for_update().filter(id__in=ids_int)}
            for oid in ids_int:
                order = orders.get(oid)
                if not order:
                    failed.append({'order_id': oid, 'reason': 'Order not found'})
                    continue

                res = confirm_order(order, user=user)
                if not res.get('success'):
                    display_id = order.tracking_number if order.tracking_number and order.tracking_number != 'DRAFT' else oid
                    failed.append({'order_id': display_id, 'reason': res.get('error', 'Unknown error')})

            return {'success': True, 'failed_orders': failed}
    except Exception as e:
        failed.append({'order_id': None, 'reason': str(e)})
        return {'success': False, 'error': str(e), 'failed_orders': failed}


def confirm_action(user, order_id, role, confirmation_type):
    """
    Generic confirmation logic for pickup/delivery by role (driver, customer, etc.).
    :param order_id: The order to confirm for.
    :param role: 'driver' or 'other' (supplier/customer)
    :param confirmation_type: 'pickup' or 'delivery'
    :return: success dict or error.
    """
    try:
        with transaction.atomic():
            # Fetch the order with row lock
            order = Order.objects.select_for_update().get(pk=order_id)

            # Determine locations and target status
            if confirmation_type == 'pickup':
                sender = 'supplier'
                receiver = 'warehouse'
                new_status = OrderStatuses.pickup_confirmed
                allowed_statuses = [OrderStatuses.confirmed, OrderStatuses.pending_pickup]
            
            elif confirmation_type == 'delivery':
                sender = 'warehouse'
                receiver = 'customer'
                new_status = OrderStatuses.delivered
                allowed_statuses = [OrderStatuses.in_warehouse, OrderStatuses.out_for_delivery]
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid confirmation type'})

            # Validate order status
            if order.order_status not in allowed_statuses:
                return JsonResponse({'success': False, 'error': f"Order status '{order.order_status}' does not allow {confirmation_type} confirmation"})

            # Find tracking with lock
            tracking = OrderTracking.objects.filter(
                order=order,
                sender__location_type=sender,
                receiver__location_type=receiver,
                tracking_status__in=['draft', 'pending']
            ).select_for_update().first()

            if not tracking:
                return JsonResponse({'success': False, 'error': f"Tracking for {confirmation_type} not found or already completed"})

            # same supplier must confirm pickup of his order
            if role == 'supplier' and user.supplier != order.supplier:
                return JsonResponse({'success': False, 'error': 'Confirmation failed, you are not the merchant of this order'}, status=403)
            
            elif role == 'driver' and tracking.driver.user != user:
                return JsonResponse({'success': False, 'error': 'Confirmation failed, you are not the assigned driver'}, status=403)

            # Check if already confirmed by user role
            if role == 'driver' and tracking.confirmed_by_driver:
                return JsonResponse({'success': False, 'error': f"{confirmation_type.capitalize()} already confirmed by driver"})
            
            elif role == 'supplier' and tracking.confirmed_by_other:
                return JsonResponse({'success': False, 'error': f"{confirmation_type.capitalize()} already confirmed by {role}"})

            # Perform confirmation
            if role == 'driver':
                tracking.confirmed_by_driver = True
            else:
                tracking.confirmed_by_other = True

            # Update tracking status if its still draft
            tracking.tracking_status = 'pending'

            # if driver confirmed a delivery, then the tracking can be closed immediately
            if confirmation_type == 'delivery' and tracking.confirmed_by_driver:
                tracking.tracking_status = 'done'
                tracking.effective_date = datetime.datetime.now()
                order.effective_date = datetime.datetime.now()

            tracking.save(update_fields=['confirmed_by_driver', 'confirmed_by_other', 'tracking_status', 'effective_date'])

            order.order_status = new_status
            order.save(update_fields=['order_status', 'effective_date'])

            return JsonResponse({'success': True, 'message': f"{confirmation_type.capitalize()} confirmed by {role}"})

    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': f"Order {order_id} does not exist"})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def get_filtered_order_requests(params, user):
    queryset = get_order_requests_for_user(user)

    if 'supplier' in params and params['supplier']:
        queryset = queryset.filter(supplier_id=params['supplier'])

    if 'warehouse' in params and params['warehouse']:
        queryset = queryset.filter(warehouse_id=params['warehouse'])

    if 'driver' in params and params['driver']:
        queryset = queryset.filter(driver_id=params['driver'])

    if 'status' in params and params['status']:
        queryset = queryset.filter(status=params['status'])

    if 'created_at' in params and params['created_at']:
        queryset = queryset.filter(created_at__date=params['created_at'])

    if 'exclude_cancelled' in params:
        queryset = queryset.exclude(status=OrderRequestStatuses.cancelled)

    return queryset.order_by("-created_at")


def confirm_order(order, driver=None, user=None):
    """
    Confirmation logic for an order:
    - creates a draft tracking:
        From Supplier to Warehouse (pick up route)
    - changes status to confirmed
    
    :param order: The order object to be confirmed.
    :param user: the requested user
    :return: success dict or error.
    """
    try:
        with transaction.atomic():
            if order.order_status != 'draft':
                return {'error': 'Order already confirmed', 'success': False}
        
            if not order.supplier_address:
                return {'error': 'Missing supplier address', 'success': False}
            
            if not order.pickup_warehouse:
                return {'error': 'Please select a pickup warehouse', 'success': False}
        
            supplier_location = StockLocation.objects.filter(location_type='supplier').first()
            warehouse_location = StockLocation.objects.filter(location_type='warehouse', warehouse=order.pickup_warehouse).first()
            customer_location = StockLocation.objects.filter(location_type='customer').first()
            
            if not supplier_location or not customer_location or not warehouse_location:
                return {'error': 'Missing some Location Configurations for Warehouses (Contact admin to fix)', 'success': False}
            
            # create pickup trackings
            OrderTracking.objects.create(
                order=order,
                sender=supplier_location,
                receiver=warehouse_location,
                sender_address=order.supplier_address,
                receiver_address=warehouse_location.warehouse.address,
                driver=driver,
                tracking_status=OrderTrackingStatuses.pending,
                created_by=user,
                created_at=datetime.datetime.now()
            )
            
            order.order_status = OrderStatuses.pending_pickup
            order.tracking_number = generate_order_tracking_number(order)
            order.save()

            # Try to send tracking link to customer (non-fatal if fails)
            try:
                send_order_scheduled(order)
            except Exception:
                pass
            
            return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def return_and_cancel(order: Order, user, return_warehouse, driver: Employee):
    try:
        with transaction.atomic():
            # Mark order cancelled if not already
            order.is_cancelled = True
            # order.order_status = OrderStatuses.cancelled
            order.cancelled_at = datetime.datetime.now()
            order.cancelled_by = user
            order.save(update_fields=['order_status', 'is_cancelled', 'cancelled_at', 'cancelled_by'])

            # Cancel any ongoing non-return tracks to avoid conflicts
            order.order_tracking.filter(
                tracking_status__in=[OrderTrackingStatuses.draft, OrderTrackingStatuses.pending]
            ).exclude(receiver__location_type='supplier').update(
                tracking_status=OrderTrackingStatuses.cancelled,
                updated_by=user,
                effective_date=datetime.datetime.now()
            )

            # Determine current location (last completed tracking)
            last_tracking = (OrderTracking.objects
                .filter(order=order, tracking_status=OrderTrackingStatuses.done)
                .order_by('-effective_date', '-created_at')
                .first())

            if order.order_status == 'delivered' and last_tracking and last_tracking.receiver and last_tracking.receiver.location_type == 'customer':
                # if order is delivered, create a tracking from customer to warehouse
                new_trk = OrderTracking.objects.create(
                    order=order,
                    sender=last_tracking.receiver,
                    receiver=last_tracking.sender,
                    sender_address=last_tracking.receiver_address,
                    receiver_address=last_tracking.sender_address,
                    driver=driver,
                    tracking_status=OrderTrackingStatuses.pending,
                    created_by=user,
                    created_at=datetime.datetime.now()
                )
                order.order_status = OrderStatuses.pending_pickup
                order.save(update_fields=['order_status'])
                return {'success': True, 'message': 'Order cancelled. Return from customer to last warehouse is created and pending.'}
            
            if not last_tracking or not last_tracking.receiver or last_tracking.receiver.location_type != 'warehouse':
                return {
                    'success': True,
                    'message': 'Order cancelled. Current location not in a warehouse. Transfer to target warehouse, then mark as returned.'
                }

            # Validate that current warehouse matches requested return warehouse
            current_wh = last_tracking.receiver.warehouse
            if not current_wh or current_wh != return_warehouse:
                return {
                    'success': True,
                    'message': f'Order cancelled. But not found in {return_warehouse}. Please Send it first, then use "Send to Merchant".'
                }

            # Build or update return-to-supplier tracking from current warehouse
            supplier_location = StockLocation.objects.filter(location_type='supplier').first()
            if not supplier_location:
                return {'success': False, 'error': 'Supplier stock location not configured', 'status': 500}

            sender_location = last_tracking.receiver
            existing_return = (OrderTracking.objects
                               .filter(order=order,
                                       sender=sender_location,
                                       receiver__location_type='supplier',
                                       tracking_status__in=[OrderTrackingStatuses.draft, OrderTrackingStatuses.pending])
                               .first())

            if existing_return:
                existing_return.driver = driver
                existing_return.sender = sender_location
                existing_return.receiver = supplier_location
                existing_return.sender_address = (sender_location.warehouse.address if sender_location and sender_location.warehouse else None)
                existing_return.receiver_address = order.supplier_address
                existing_return.tracking_status = OrderTrackingStatuses.pending
                existing_return.updated_by = user
                existing_return.save()
                created_id = existing_return.id
            else:
                new_trk = OrderTracking.objects.create(
                    order=order,
                    sender=sender_location,
                    receiver=supplier_location,
                    sender_address=(sender_location.warehouse.address if sender_location and sender_location.warehouse else None),
                    receiver_address=order.supplier_address,
                    driver=driver,
                    tracking_status=OrderTrackingStatuses.pending,
                    created_by=user,
                    created_at=datetime.datetime.now()
                )
                created_id = new_trk.id
            
            order.order_status = OrderStatuses.out_for_supplier
            order.save(update_fields=['order_status'])

            return {'success': True, 'message': 'Order cancelled and return tracking created', 'tracking_id': created_id}

    except Exception as e:
        return {'success': False, 'error': str(e), 'status': 500}
    
