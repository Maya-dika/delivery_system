from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, Sum, F, ExpressionWrapper, FloatField

from orders.models import Order, OrderTracking, OrderPackages, PackageRequirments, DeliveryPriceListItem, DeliveryPriceList, OrderStatuses, OrderTrackingStatuses
from orders.forms import OrderForm
from orders.services import services
from rest_framework.decorators import api_view
from core.decorators import role_required
from core.models import StockLocation
from orders.permissions import get_orders_for_user
from .templatetags.order_tags import format_currency, display_order_price

from datetime import date, datetime
import re

def _apply_direct_to_warehouse(order: Order, driver, user):
    try:
        supplier_loc = StockLocation.objects.filter(location_type='supplier').first()
        if not order.pickup_warehouse:
            return
        wh_loc = StockLocation.objects.filter(location_type='warehouse', warehouse=order.pickup_warehouse).first()
        if not supplier_loc or not wh_loc:
            return
        now = datetime.now()
        OrderTracking.objects.create(
            order=order,
            sender=supplier_loc,
            receiver=wh_loc,
            sender_address=order.supplier_address,
            receiver_address=(order.pickup_warehouse.address if order.pickup_warehouse else None),
            driver=driver,
            tracking_status=OrderTrackingStatuses.done,
            created_by=user,
            created_at=now,
            effective_date=now,
            confirmed_by_driver=True,
            confirmed_by_other=True,
        )
        order.order_status = OrderStatuses.in_warehouse
        order.tracking_number = services.generate_order_tracking_number(order)
            
        order.save(update_fields=['order_status', 'tracking_number'])
    except Exception:
        # Don't break the save if tracking creation fails; let validation guard it primarily
        pass


@api_view(["POST"])
def api_save_order(request, pk=None):
    try:
        data = request.data
        
        # clean amounts fields
        data['order_price'] = clean_amount(data.get('order_price', 0))
        data['total_delivery_fees'] = clean_amount(data.get('total_delivery_fees', 0))
        data['order_price_secondary'] = clean_amount(data.get('order_price_secondary', ''))
        
        old_sender_address, old_receiver_address = None, None
        if pk:
            order = get_object_or_404(Order, pk=pk)
            old_sender_address = order.supplier_address
            old_receiver_address = order.customer_address
            form = OrderForm(data, instance=order)
        else:
            form = OrderForm(data)

        if not form.is_valid():
            # Flatten Django form errors into a concise human-readable string
            try:
                non_field = form.non_field_errors()
                if non_field:
                    message = ' '.join([str(m) for m in non_field])
                else:
                    parts = []
                    for _, errors in form.errors.items():
                        for err in errors:
                            parts.append(str(err))
                    message = ' '.join(parts) if parts else 'Invalid input.'
            except Exception:
                message = 'Invalid input.'
            return JsonResponse({'success': False, 'error': message}, status=400)

        # Track direct-to-warehouse transition
        original_direct = False
        if pk:
            try:
                original_direct = bool(order.is_direct_to_warehouse)
            except Exception:
                original_direct = False

        order = form.save(commit=False)
        if pk:
            order.company = request.user.company
            order.updated_by = request.user
            
            # After save, check if addresses changed
            new_sender_address = form.cleaned_data.get('supplier_address')
            new_receiver_address = form.cleaned_data.get('customer_address')

            if old_sender_address != new_sender_address:
                OrderTracking.objects.filter(order=order, sender__location_type='supplier', tracking_status__in=['draft', 'pending']).update(
                    sender_address=new_sender_address
                )

            if old_receiver_address != new_receiver_address:
                OrderTracking.objects.filter(order=order, receiver__location_type='customer', tracking_status__in=['draft', 'pending']).update(
                    receiver_address=new_receiver_address
                )
            
        else:
            order.company = request.user.company
            order.created_by = request.user
            order.order_date = datetime.now()
        
        # Recompute planned route
        order.update_planned_route()            
        
        order = form.save()

        # Apply direct-to-warehouse side effects if transitioning to True
        try:
            will_direct = bool(form.cleaned_data.get('is_direct_to_warehouse'))
        except Exception:
            will_direct = False
        if will_direct and not original_direct:
            _apply_direct_to_warehouse(order, form.cleaned_data.get('received_by_driver'), request.user)
        
        # save packages
        existing_ids = set(OrderPackages.objects.filter(order=order).values_list('id', flat=True))
        sent_ids = set()

        for pkg in data.get('packages', []):
            pkg_id = int(pkg.get('id', 0))
            if pkg.get('DELETE'):
                if pkg_id:
                    OrderPackages.objects.filter(id=pkg_id, order=order).delete()
                continue

            if pkg_id and pkg_id in existing_ids:
                op = OrderPackages.objects.get(id=pkg_id, order=order)
            else:
                op = OrderPackages(order=order)

            op.description = pkg['description']
            op.delivery_fees = pkg['delivery_fees']
            
            if pkg.get('package_type'):
                op.package_type = DeliveryPriceListItem.objects.get(pk=pkg['package_type'])

            if pkg.get('package_requirment'):
                op.package_requirment = PackageRequirments.objects.get(pk=pkg['package_requirment'])

            op.save()
            sent_ids.add(op.id)

        to_delete = existing_ids - sent_ids
        OrderPackages.objects.filter(id__in=to_delete, order=order).delete()
        
        # handle save and next: find next order in the same page
        if data.get("save_and_next") and order.order_request:
            # All orders for this request, sorted consistently
            order_ids = list(
                Order.objects.filter(order_request=order.order_request)
                .order_by("order_date", "id")  # fallback to id to break ties
                .values_list("id", flat=True)
            )

            if order.id in order_ids:
                current_index = order_ids.index(order.id)
                next_index = (current_index + 1) % len(order_ids)  # wrap around
                next_order_id = order_ids[next_index]
            
                return JsonResponse({'success': True, 'message': 'Order successfully updated', 'order_id': order.id, 'next_order_id': next_order_id})

        return JsonResponse({'success': True, 'message': 'Order successfully updated', 'order_id': order.id})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def clean_amount(value):
    if isinstance(value, str):
        # Remove non-numeric characters
        value = re.sub(r'[^0-9.\-]', '', value)
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


@api_view(["GET"])
@role_required(allowed_roles=['employee', 'supplier'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def api_order_request_list(request):
    params = request.GET

    # DataTables parameters
    search = params.get('search[value]', '')
    start = int(params.get('start', 0))
    length = int(params.get('length', 20))
    draw = int(params.get('draw', 1))

    order_column_index = params.get('order[0][column]')
    order_column_name = params.get(f'columns[{order_column_index}][data]', 'created_at')
    order_direction = params.get('order[0][dir]', 'desc')

    # Base filtered queryset (filters from form)
    base_qs = services.get_filtered_order_requests(params, request.user)

    # Apply search across key fields
    if search:
        from django.db.models import Q
        base_qs = base_qs.filter(
            Q(reference__icontains=search) |
            Q(supplier__name__icontains=search) |
            Q(driver__name__icontains=search)
        )

    total_records = base_qs.count()

    # Secure ordering
    allowed_order_fields = ['created_at', 'nb_orders', 'nb_packages', 'reference']
    if order_column_name not in allowed_order_fields:
        order_column_name = 'created_at'
    ordering = order_column_name if order_direction == 'asc' else f'-{order_column_name}'

    qs = base_qs.order_by(ordering)[start:start + length]

    data = [{
        "id": req.id,
        "reference": req.reference,
        "supplier": req.supplier.name if req.supplier else '',
        "warehouse": req.warehouse.name if req.warehouse else '',
        "driver": req.driver.name if req.driver else '',
        "nb_orders": req.nb_orders,
        "nb_packages": req.nb_packages,
        "created_at": req.created_at.strftime('%Y-%m-%d %I:%M:%S %p') if req.created_at else '',
        "status": req.get_status_display(),
    } for req in qs]

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data,
    })


@api_view(["GET"])
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def api_account_statement(request):
    try:

        qs = get_orders_for_user(request.user)

        # Parse date range
        from_str = request.GET.get("from")
        to_str = request.GET.get("to")

        today = date.today()
        start_of_month = date(today.year, today.month, 1)

        if from_str:
            try:
                dfrom = datetime.strptime(from_str, "%Y-%m-%d").date()
            except Exception:
                dfrom = start_of_month
        else:
            dfrom = start_of_month

        if to_str:
            try:
                dto = datetime.strptime(to_str, "%Y-%m-%d").date()
            except Exception:
                dto = today
        else:
            dto = today

        # Delivered or returned orders only
        qs = qs.filter(
            order_date__date__range=[dfrom, dto], order_status__in=[OrderStatuses.delivered, OrderStatuses.returned])


        total_orders = qs.count()

        # --- Profit calculation (delivery_fees - driver_commission) ---
        # For USD
        usd_orders = qs.annotate(
            profit=ExpressionWrapper(F("total_delivery_fees") - F("driver_commission"), output_field=FloatField())
        )
        profit_usd = usd_orders.aggregate(total=Sum("profit"))["total"] or 0

        # ---- Group by delivery fees ----
        by_fees_qs = (
            qs.values("total_delivery_fees", "currency")
              .annotate(
                  nb_orders=Count("id"),
                  total_commission=Sum("driver_commission"),
                  profit=Sum(F("total_delivery_fees") - F("driver_commission"), output_field=FloatField())
              )
              .order_by("total_delivery_fees")
        )

        rows = []
        for row in by_fees_qs:
            rows.append({
                "currency": row["currency"],
                "delivery_fees": format_currency(float(row["total_delivery_fees"] or 0)),
                "nb_orders": int(row["nb_orders"] or 0),
                "total_commission": format_currency(float(row["total_commission"] or 0)),
                "profit": format_currency(float(row["profit"] or 0)),
            })

        return JsonResponse({
            "success": True,
            "summary": {
                "from": dfrom.isoformat(),
                "to": dto.isoformat(),
                "total_orders": total_orders,
                "profit_usd": format_currency(float(profit_usd)),
            },
            "by_fees": rows,
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@api_view(["GET"])
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def api_general_report(request):
    try:
        from django.db.models import OuterRef, Subquery
        from decimal import Decimal

        qs = get_orders_for_user(request.user).select_related('supplier', 'customer')

        # Date range
        from_str = request.GET.get('from')
        to_str = request.GET.get('to')
        today = date.today()
        start_of_month = date(today.year, today.month, 1)
        if from_str:
            try:
                dfrom = datetime.strptime(from_str, '%Y-%m-%d').date()
            except Exception:
                dfrom = start_of_month
        else:
            dfrom = start_of_month
        if to_str:
            try:
                dto = datetime.strptime(to_str, '%Y-%m-%d').date()
            except Exception:
                dto = today
        else:
            dto = today
        qs = qs.filter(order_date__date__range=[dfrom, dto])

        # Status filter
        st = (request.GET.get('status') or '').strip()
        if st:
            qs = qs.filter(order_status=st)

        # Driver annotation: latest delivery tracking driver
        trk_sub = (OrderTracking.objects
                   .filter(order=OuterRef('pk'), receiver__location_type='customer')
                   .order_by('-id'))
        qs = qs.annotate(
            delivery_driver_id=Subquery(trk_sub.values('driver_id')[:1]),
            delivery_driver_name=Subquery(trk_sub.values('driver__name')[:1])
        )

        driver_id = request.GET.get('driver')
        if driver_id:
            qs = qs.filter(delivery_driver_id=driver_id)

        # Float equals filters
        fees = (request.GET.get('delivery_fees') or '').strip()
        if fees:
            try:
                qs = qs.filter(total_delivery_fees=Decimal(fees))
            except Exception:
                pass
        comm = (request.GET.get('driver_commission') or '').strip()
        if comm:
            try:
                qs = qs.filter(driver_commission=Decimal(comm))
            except Exception:
                pass

        data = []
        total_fees, total_comm, total_profit = 0.0, 0.0, 0.0
        for o in qs.order_by('-order_date')[:2000]:
            profit = (o.total_delivery_fees or Decimal(0)) - (o.driver_commission or Decimal(0))
            total_fees += float(o.total_delivery_fees or 0)
            total_comm += float(o.driver_commission or 0)
            total_profit += float(profit or 0)
            data.append({
                'id': o.id,
                'date': o.order_date.strftime('%Y-%m-%d') if o.order_date else '',
                'tracking_number': o.tracking_number,
                'supplier': o.supplier.name if o.supplier else '',
                'customer': o.customer.name if o.customer else '',
                'driver': getattr(o, 'delivery_driver_name', '') or '',
                'order_price': display_order_price(o),
                'total_delivery_fees': format_currency(float(o.total_delivery_fees or 0)),
                'driver_commission': format_currency(float(o.driver_commission or 0)),
                'profit': format_currency(float(profit)),
                'order_status': o.get_order_status_display(),
                'invoice_status': 'Paid',
                'payment_method': 'Cash',
            })

        totals = {'total_fees': format_currency(total_fees), 'total_commissions': format_currency(total_comm), 'total_profit': format_currency(total_profit)}
        return JsonResponse({'success': True, 'data': data, 'totals': totals})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(["GET"])
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user', 'driver'])
def api_driver_statement(request):
    try:
        from django.db.models import OuterRef, Subquery
        from decimal import Decimal

        qs = get_orders_for_user(request.user)

        # Date range defaults
        from_str = request.GET.get('from')
        to_str = request.GET.get('to')
        today = date.today()
        start_of_month = date(today.year, today.month, 1)
        if from_str:
            try:
                dfrom = datetime.strptime(from_str, '%Y-%m-%d').date()
            except Exception:
                dfrom = start_of_month
        else:
            dfrom = start_of_month
        if to_str:
            try:
                dto = datetime.strptime(to_str, '%Y-%m-%d').date()
            except Exception:
                dto = today
        else:
            dto = today
        qs = qs.filter(order_date__date__range=[dfrom, dto])

        # Only delivered/returned
        qs = qs.filter(order_status__in=[OrderStatuses.delivered, OrderStatuses.returned])

        # Driver annotation and filter
        trk_sub = (OrderTracking.objects
                   .filter(order=OuterRef('pk'), receiver__location_type='customer')
                   .order_by('-id'))
        qs = qs.annotate(
            delivery_driver_id=Subquery(trk_sub.values('driver_id')[:1])
        )
        driver_id = request.GET.get('driver')
        if driver_id:
            qs = qs.filter(delivery_driver_id=driver_id)

        # Extra equals filters
        fees = (request.GET.get('delivery_fees') or '').strip()
        if fees:
            try:
                qs = qs.filter(total_delivery_fees=Decimal(fees))
            except Exception:
                pass
        comm = (request.GET.get('driver_commission') or '').strip()
        if comm:
            try:
                qs = qs.filter(driver_commission=Decimal(comm))
            except Exception:
                pass

        # Group by date
        from django.db.models import Count, Sum, F, FloatField
        from django.db.models import ExpressionWrapper
        agg = (qs.values('order_date__date')
                 .annotate(
                     nb_orders=Count('id'),
                     total_fees=Sum('total_delivery_fees'),
                     total_commission=Sum('driver_commission'),
                     profit=Sum(ExpressionWrapper(F('total_delivery_fees') - F('driver_commission'), output_field=FloatField())),
                 )
                 .order_by('order_date__date'))

        data = []
        t_orders = 0
        t_fees = 0.0
        t_comm = 0.0
        t_profit = 0.0
        for row in agg:
            t_orders += int(row['nb_orders'] or 0)
            t_fees += float(row['total_fees'] or 0)
            t_comm += float(row['total_commission'] or 0)
            t_profit += float(row['profit'] or 0)
            data.append({
                'date': row['order_date__date'].isoformat() if row['order_date__date'] else '',
                'nb_orders': int(row['nb_orders'] or 0),
                'total_fees': format_currency(float(row['total_fees'] or 0)),
                'total_commission': format_currency(float(row['total_commission'] or 0)),
                'profit': format_currency(float(row['profit'] or 0)),
            })

        return JsonResponse({
            'success': True,
            'data': data,
            'totals': {
                'nb_orders': t_orders,
                'total_fees': format_currency(round(t_fees, 2)),
                'total_commission': format_currency(round(t_comm, 2)),
                'profit': format_currency(round(t_profit, 2)),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(["GET"])
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user', 'driver'])
def api_employees_performance(request):
    try:
        from django.db.models import OuterRef, Subquery
        from decimal import Decimal
        from django.db.models import Count, Sum, F, FloatField, ExpressionWrapper

        qs = get_orders_for_user(request.user)

        # Date range defaults
        from_str = request.GET.get('from')
        to_str = request.GET.get('to')
        today = date.today()
        start_of_month = date(today.year, today.month, 1)
        if from_str:
            try:
                dfrom = datetime.strptime(from_str, '%Y-%m-%d').date()
            except Exception:
                dfrom = start_of_month
        else:
            dfrom = start_of_month
        if to_str:
            try:
                dto = datetime.strptime(to_str, '%Y-%m-%d').date()
            except Exception:
                dto = today
        else:
            dto = today
        qs = qs.filter(order_date__date__range=[dfrom, dto])

        # Only delivered/returned for performance
        qs = qs.filter(order_status__in=[OrderStatuses.delivered, OrderStatuses.returned])

        # Annotate delivery driver
        trk_sub = (OrderTracking.objects
                   .filter(order=OuterRef('pk'), receiver__location_type='customer')
                   .order_by('-id'))
        qs = qs.annotate(
            delivery_driver_id=Subquery(trk_sub.values('driver_id')[:1]),
            delivery_driver_name=Subquery(trk_sub.values('driver__name')[:1])
        ).filter(delivery_driver_id__isnull=False)

        # Extra equals filters
        fees = (request.GET.get('delivery_fees') or '').strip()
        if fees:
            try:
                qs = qs.filter(total_delivery_fees=Decimal(fees))
            except Exception:
                pass
        comm = (request.GET.get('driver_commission') or '').strip()
        if comm:
            try:
                qs = qs.filter(driver_commission=Decimal(comm))
            except Exception:
                pass

        # Group by driver
        agg = (qs.values('delivery_driver_id', 'delivery_driver_name')
                 .annotate(
                     nb_orders=Count('id'),
                     total_fees=Sum('total_delivery_fees'),
                     total_commission=Sum('driver_commission'),
                     profit=Sum(ExpressionWrapper(F('total_delivery_fees') - F('driver_commission'), output_field=FloatField())),
                 )
                 .order_by('delivery_driver_name'))

        data = []
        t_orders = 0
        t_fees = 0.0
        t_comm = 0.0
        t_profit = 0.0
        for row in agg:
            t_orders += int(row['nb_orders'] or 0)
            fees_v = float(row['total_fees'] or 0)
            comm_v = float(row['total_commission'] or 0)
            profit_v = float(row['profit'] or 0)
            t_fees += fees_v
            t_comm += comm_v
            t_profit += profit_v
            data.append({
                'employee': row['delivery_driver_name'] or '—',
                'nb_orders': int(row['nb_orders'] or 0),
                'total_fees': format_currency(fees_v),
                'total_commission': format_currency(comm_v),
                'profit': format_currency(profit_v),
            })

        return JsonResponse({
            'success': True,
            'data': data,
            'totals': {
                'nb_orders': t_orders,
                'total_fees': format_currency(round(t_fees, 2)),
                'total_commission': format_currency(round(t_comm, 2)),
                'profit': format_currency(round(t_profit, 2)),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(["GET"])
@role_required(allowed_roles=['employee', 'supplier'], employee_types=['admin', 'warehouse_manager'])
def api_delivery_pricelist_list(request):
    params = request.GET

    # DataTables parameters
    search = params.get('search[value]', '')
    start = int(params.get('start', 0))
    length = int(params.get('length', 20))
    draw = int(params.get('draw', 1))

    order_column_index = params.get('order[0][column]')
    order_column_name = params.get(f'columns[{order_column_index}][data]', 'name')
    order_direction = params.get('order[0][dir]', 'asc')

    # Base queryset
    base_qs = DeliveryPriceList.objects.annotate(
        items_count=Count('pricelist_items')
    )

    # Apply search
    if search:
        from django.db.models import Q
        base_qs = base_qs.filter(Q(name__icontains=search))

    total_records = base_qs.count()

    # Secure ordering
    allowed_order_fields = ['name', 'default', 'items_count']
    if order_column_name not in allowed_order_fields:
        order_column_name = 'name'
    ordering = order_column_name if order_direction == 'asc' else f'-{order_column_name}'
    
    # Default ordering: default first, then by specified field
    if order_column_name == 'name':
        base_qs = base_qs.order_by('-default', ordering)
    else:
        base_qs = base_qs.order_by(ordering)

    qs = base_qs[start:start + length]

    data = [{
        "id": pl.id,
        "name": pl.name,
        "default": pl.default,
        "items_count": pl.items_count,
    } for pl in qs]

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data,
    })

