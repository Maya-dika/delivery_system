from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models.query_utils import Q
from django.db.models import OuterRef, Subquery
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

from .models import Order, OrderPackages, OrderTracking, PackageType, PackageRequirments, OrderRequest, DeliveryPriceList, DeliveryPriceListItem
from .models.order import OrderStatuses, OrderTrackingStatuses
from .models.order_request import OrderRequestStatuses
from core.utility.pdf import render_template_to_pdf, pdf_download
from core.models import NumberSequence
from core.utility.barcodes import barcode_data_uri
from core.models import StockLocation, Warehouse
from core.decorators import role_required
from users.models import Employee, Supplier
from .forms import PackageFormSet, PackageTypeForm, PackageRequirementForm, OrderForm, AssignDriverForm, OrderRequestForm, DeliveryPriceListForm, DeliveryPriceListItemFormSet
from .templatetags.order_tags import format_currency, display_order_price

from .services.serializers import OutForDeliverySerializer, OrderConfirmationSerializer
from .services import services
from .services.whatsapp import verify_code as verify_phone_code
from .services import exchange as exchange_services

from .decorators import order_access_required
from .permissions import get_allowed_order_actions, get_orders_for_user

import datetime
import logging

logger = logging.getLogger(__name__)


@login_required
def orders_list_view(request):
    allowed_actions = get_allowed_order_actions(request.user)
    view_only = "edit" not in allowed_actions
    order_request_id = request.GET.get("order_request_id")

    context = {
        "stock_locations": StockLocation.objects.all(),
        "drivers": Employee.objects.filter(employee_type="driver", active=True),
        "statuses": OrderStatuses.choices,
        "view_only": view_only,
        "order_request_id": order_request_id,
    }
    return render(request, 'lists/orders_list.html', context)

@api_view(["GET"])
def get_filtered_orders(request):
    search = request.GET.get('search[value]', '')
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 20))
    draw = int(request.GET.get('draw', 1))

    status = request.GET.get('status')
    order_date = request.GET.get('order_date')
    driver_id = request.GET.get('driver')
    current_location = request.GET.get('current_location')
    next_destination = request.GET.get('next_destination')

    order_column_index = request.GET.get('order[0][column]')
    order_column_name = request.GET.get(f'columns[{order_column_index}][data]', 'order_date')
    order_direction = request.GET.get('order[0][dir]', 'desc')
    
    order_request_id = request.GET.get("order_request_id")


    # Safe allowed ordering fields
    allowed_order_fields = [
        'order_date'
    ]
    if order_column_name not in allowed_order_fields:
        order_column_name = 'order_date'
    ordering = order_column_name if order_direction == 'asc' else f'-{order_column_name}'
    
    qs = get_orders_for_user(request.user)
    
    # last completed tracking (for current location)
    last_completed = OrderTracking.objects.filter(
        order=OuterRef('pk'),
        tracking_status='done'
    ).order_by('-id')

    # In-progress tracking (priority)  
    in_progress_tracking = OrderTracking.objects.filter(
        order=OuterRef('pk'),
        tracking_status__in=['draft', 'pending']
    ).order_by('id')

    qs = qs.annotate(
        current_location_id=Subquery(last_completed.values('receiver_id')[:1]),
        next_destination_id=Subquery(in_progress_tracking.values('receiver_id')[:1])
    )
    
    if order_request_id:
        qs = qs.filter(order_request_id=order_request_id)
    
    # Exclude cancelled and delivered by default
    if not status and not search and not order_request_id:
        qs = qs.exclude(order_status__in=['cancelled', 'delivered', 'returned'])
    

    if status:
        if status == "cancelled":
            qs = qs.filter(Q(order_status='cancelled') | Q(is_cancelled=True))
        elif status == "all_statuses":
            qs = qs  # No filtering, show all statuses
        elif status == "for_exchange":
            qs = qs.filter(is_exchanged=True)
        else:
            qs = qs.filter(order_status=status)
    if order_date:
        qs = qs.filter(order_date__date=order_date)

    if driver_id:
        qs = qs.filter(order_tracking__driver_id=driver_id, order_tracking__tracking_status__in=['pending', 'draft'])

    if current_location:
        qs = qs.filter(current_location_id=current_location)

    # next_destination filter using computed planned route next step
    if next_destination:
        # Direct matches (in-progress tracking)
        direct_matches = qs.filter(next_destination_id=next_destination)
        
        # Orders needing computation (no in-progress tracking)
        orders_to_compute = qs.filter(next_destination_id__isnull=True)
        
        # Compute matches (only when filtering)
        computed_order_ids = []
        for order in orders_to_compute:
            if order.get_next_destination_id() == int(next_destination):
                computed_order_ids.append(order.id)
        
        # Combine results
        if computed_order_ids:
            qs = direct_matches.union(qs.filter(id__in=computed_order_ids))
        else:
            qs = direct_matches

    if search:
        qs = qs.filter(
            Q(tracking_number__icontains=search) |
            Q(supplier__name__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(order_request__reference__icontains=search)
        )

    total_records = qs.count()

    qs = qs.order_by(ordering)[start:start + length]

    data = [{
        'id': order.id,
        'tracking_number': order.tracking_number,
        'supplier': order.supplier.name if order.supplier else '',
        'supplier_address': order.supplier_address.__str__() if order.supplier_address else '',
        'customer': order.customer.name if order.customer else '',
        'customer_address': order.customer_address.__str__() if order.customer_address else '',
        'order_status': order.get_order_status_display(),
        'order_date': order.order_date.strftime('%Y-%m-%d %I:%M:%S %p') if order.order_date else '',
        'order_request': order.order_request.__str__() if order.order_request else '',
        'order_price': display_order_price(order),
        'total_delivery_fees': format_currency(order.total_delivery_fees),
        'is_cancelled': order.is_cancelled,
        'is_exchanged': order.is_exchanged,
    } for order in qs]

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    })


def build_order_form_context(order=None, allowed_actions=[], user=None):
    form = OrderForm(instance=order, user=user)
    supplier_addresses, customer_addresses = [],[]
    view_only = "edit" not in allowed_actions
    
    if order:
        title = 'Update ' + order.tracking_number
        order_id = order.id
        package_formset = PackageFormSet(
            queryset=order.order_packages.all(),
            form_kwargs={
                'allowed_package_types': get_allowed_pricelist_items(order.delivery_pricelist, order.pickup_warehouse, order.delivery_warehouse)
            }
        )

        is_update = True
        if order.supplier and order.supplier.address:
            supplier_addresses = order.supplier.address
        if order.customer and order.customer.addresses: 
            customer_addresses = order.customer.addresses.all()
        
        view_only = view_only or order.order_status in ["out_for_delivery", "delivered", "cancelled", "returned"] or order.is_cancelled or order.is_exchanged
    
    else:
        title = 'Create New Order'
        order_id = None
        package_formset = PackageFormSet(queryset=OrderPackages.objects.none())
        is_update = False
    
    
    # If view_only is True, make all fields in the package_formset readonly
    if view_only:
        for pkg_form in package_formset:
            for _, field in pkg_form.fields.items():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['disabled'] = True  # Disable the fields to prevent accidental submission


    planned_route_str = ''
    next_expected_str = ''
    if order:
        try:
            planned_route_str = order.get_planned_route_text()
        except Exception:
            pass
        try:
            nd = order.get_next_destination()
            next_expected_str = nd.get('name') if nd else ''
        except Exception:
            pass

    return {
        'form_title': title,
        'order_form': form,
        'order_id': order_id,
        'package_formset': package_formset,
        'is_update': is_update,
        'supplier_addresses': supplier_addresses,
        'customer_addresses': customer_addresses,
        'allowed_actions': allowed_actions,
        'view_only': view_only,
        'planned_route_str': planned_route_str,
        'next_expected_str': next_expected_str,
        'drivers': Employee.objects.filter(employee_type='driver', active=True),
        'warehouses': Warehouse.objects.filter(active=True),
    }

@order_access_required()
def order_form_view(request, order, allowed_actions):
    from_request = request.GET.get("from_order_request")
    
    context = build_order_form_context(order, allowed_actions, user=request.user)
    context["from_order_request"] = from_request
    return render(request, 'forms/order_form.html', context)


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def package_types(request):
    types = PackageType.objects.all()
    return render(request, 'lists/package_types.html', {
        'types': types,
    })


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def package_type_create(request):
    if request.method == 'POST':
        form = PackageTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('orders:package_types')
    else:
        form = PackageTypeForm()
    return render(request, 'forms/form_template.html', {'form': form, 'form_title': 'Create Package Type', 'redirect_back_url': '/orders/package-types/'})


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def package_type_update(request, pk):
    instance = get_object_or_404(PackageType, pk=pk)
    if request.method == 'POST':
        form = PackageTypeForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('orders:package_types')
    else:
        form = PackageTypeForm(instance=instance)
    return render(request, 'forms/form_template.html', {'form': form, 'form_title': 'Edit Package Type', 'redirect_back_url': '/orders/package-types/'})

@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def package_type_delete(request, pk):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    instance = get_object_or_404(PackageType, pk=pk)
    instance.delete()  # cascades to DeliveryPriceListItem; OrderPackages.package_type is SET_NULL
    return JsonResponse({'success': True, 'message': 'Package type deleted'})


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def package_requirements(request):
    requirements = PackageRequirments.objects.all()
    return render(request, 'lists/package_requirements.html', {
        'requirements': requirements,
    })


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def package_requirement_create(request):
    if request.method == 'POST':
        form = PackageRequirementForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('orders:package_requirements')
    else:
        form = PackageRequirementForm()
    return render(request, 'forms/form_template.html', {'form': form, 'form_title': 'Create Package Requirement', 'redirect_back_url': '/orders/package-requirements/'})



@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def package_requirement_update(request, pk):
    instance = get_object_or_404(PackageRequirments, pk=pk)
    if request.method == 'POST':
        form = PackageRequirementForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('orders:package_requirements')
    else:
        form = PackageRequirementForm(instance=instance)
    return render(request, 'forms/form_template.html', {'form': form, 'form_title': 'Edit Package Requirement', 'redirect_back_url': '/orders/package-requirements/'})

@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def package_requirement_delete(request, pk):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    instance = get_object_or_404(PackageRequirments, pk=pk)
    instance.delete()
    return JsonResponse({'success': True, 'message': 'Requirement deleted'})


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def delivery_pricelist_list(request):
    pricelists = DeliveryPriceList.objects.all().order_by('-default', 'name')
    return render(request, 'lists/delivery_pricelists_list.html', {
        'pricelists': pricelists,
    })


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def delivery_pricelist_create(request):
    if request.method == 'POST':
        form = DeliveryPriceListForm(request.POST)
        formset = DeliveryPriceListItemFormSet(request.POST, queryset=DeliveryPriceListItem.objects.none())
        
        if form.is_valid() and formset.is_valid():
            pricelist = form.save()
            
            for item_form in formset:
                if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                    item = item_form.save(commit=False)
                    item.pricelist = pricelist
                    item.save()
            
            return redirect('orders:delivery_pricelist_update', pk=pricelist.pk)
    else:
        form = DeliveryPriceListForm()
        formset = DeliveryPriceListItemFormSet(queryset=DeliveryPriceListItem.objects.none())
    
    return render(request, 'forms/delivery_pricelist_form.html', {
        'form': form,
        'formset': formset,
        'form_title': 'Create Delivery Pricelist',
        'package_types': PackageType.objects.all(),
        'warehouses': Warehouse.objects.filter(active=True)
    })


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def delivery_pricelist_update(request, pk):
    pricelist = get_object_or_404(DeliveryPriceList, pk=pk)
    
    if request.method == 'POST':
        form = DeliveryPriceListForm(request.POST, instance=pricelist)
        formset = DeliveryPriceListItemFormSet(request.POST, queryset=pricelist.pricelist_items.all())
        
        if form.is_valid() and formset.is_valid():
            form.save()
            
            for item_form in formset:
                if item_form.cleaned_data:
                    if item_form.cleaned_data.get('DELETE', False):
                        if item_form.instance.pk:
                            item_form.instance.delete()
                    else:
                        item = item_form.save(commit=False)
                        item.pricelist = pricelist
                        item.save()
            
            return redirect('orders:delivery_pricelist_update', pk=pricelist.pk)
    else:
        form = DeliveryPriceListForm(instance=pricelist)
        formset = DeliveryPriceListItemFormSet(queryset=pricelist.pricelist_items.all())
    
    return render(request, 'forms/delivery_pricelist_form.html', {
        'form': form,
        'formset': formset,
        'form_title': 'Edit Delivery Pricelist',
        'package_types': PackageType.objects.all(),
        'instance': pricelist,
        'warehouses': Warehouse.objects.filter(active=True)
    })


def serialize_tracking(tracking):
    return {
        'id': tracking.id,
        'sender': tracking.sender.name,
        'receiver': tracking.receiver.name,
        'sender_address': str(tracking.sender_address),
        'receiver_address': str(tracking.receiver_address),
        'driver': str(tracking.driver),
        'status': tracking.tracking_status,
        'created_at': tracking.created_at.strftime("%Y-%m-%d %H:%M") if tracking.created_at else '',
        'effective_date': tracking.effective_date.strftime("%Y-%m-%d %H:%M") if tracking.effective_date else '',
    }

@api_view(["GET"])
def get_order_trackings(request, order_id):
    order = Order.objects.get(id=order_id)
    trackings = OrderTracking.objects.filter(order=order).order_by('created_at', 'effective_date')
    return JsonResponse({'trackings': [serialize_tracking(t) for t in trackings]}, safe=False)


@api_view(['POST'])
def confirm_order(request, pk):
    try:
        order = get_object_or_404(Order, pk=pk)
        result = services.confirm_order(order=order, user=request.user)
        if not result.get('success'):
            return JsonResponse({'success': False, 'error': result.get('error', 'Unknown error')}, status=500)
        
        return JsonResponse({'success': True, 'order_id': order.id})
    
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=500)


@api_view(['POST'])
def confirm_orders_bulk_api(request):
    try:
        data = request.data
        order_ids = data.get('order_ids', [])
        if not order_ids:
            return JsonResponse({'success': False, 'error': 'No orders provided'}, status=400)

        result = services.confirm_orders_bulk(order_ids, request.user)
        status_code = 200 if result.get('success') else 400
        return JsonResponse(result, status=status_code)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
def assign_driver(request):
    data = request.data
    driver_id = int(data.get('driver_id') or 0)
    order_ids = [int(order_id) for order_id in data.get('order_ids', [])]
    assign_type = data.get('type')  # pickup or delivery
    
    if assign_type not in ['pickup', 'delivery', 'out_for_delivery'] or not driver_id or not order_ids:
        return JsonResponse({'success': False, 'error': 'Invalid params'})

    driver = Employee.objects.filter(pk=driver_id, active=True).first()
    if not driver:
        return JsonResponse({'success': False, 'error': 'Driver not found (or not active anymore)'})

    # Securely filter based on assign_type
    if assign_type == 'pickup':
        tracking_filter = Q(sender__location_type__in=['supplier', 'warehouse'], receiver__location_type__in=['supplier', 'warehouse'])
    else:
        tracking_filter = Q(sender__location_type='warehouse', receiver__location_type='customer')

    trackings = OrderTracking.objects.filter(
        order__id__in=order_ids,
        tracking_status__in=['draft', 'pending']
    ).filter(tracking_filter)

    if not trackings.exists():
        return JsonResponse({'success': False, 'error': f'No ongoing {assign_type} trackings found for the selected orders'})

    trackings.update(driver=driver)
    # If assigning delivery driver, update order driver_commission
    if assign_type == 'delivery':
        try:
            commission = getattr(driver, 'commission', 0) or 0
            Order.objects.filter(id__in=order_ids).update(driver_commission=commission)
        except Exception:
            pass
        
    return JsonResponse({'success': True})

@login_required
def assign_driver_form_view(request, type):
    if type not in ['pickup', 'delivery', 'out_for_delivery']:
        type = 'pickup'
    form = AssignDriverForm()
    context = {
        'assign_type': type,
        'form': form,
    }
    return render(request, 'forms/assign_driver_form.html', context)


@api_view(['POST'])
def mark_as_arrived_to_warehouse(request):
    try:
        data = request.data
        order_ids = data.get('order_ids', [])
        if not order_ids:
            return JsonResponse({'success': False, 'error': 'No orders provided'})

        updated_orders = []
        failed_orders = []
        employee = Employee.objects.filter(user=request.user, active=True).first()
        
        with transaction.atomic():
            for order_id in order_ids:
                order = Order.objects.select_for_update().filter(pk=order_id).first()
                if not order:
                    failed_orders.append({'order_id': order_id, 'reason': 'Order not found'})
                    continue
                
                if order.order_status in ['draft', 'delivered', 'returned'] and not order.is_cancelled and not order.is_exchanged:
                    failed_orders.append({'order_id': order.tracking_number, 'reason': f'Current Order Status {order.order_status} doesnt allow this action'})
                    continue

                tracking = OrderTracking.objects.filter(
                    order_id=order_id,
                    receiver__location_type='warehouse',
                    tracking_status__in=['draft', 'pending']
                ).order_by('id').first()
                
                if tracking and (tracking.receiver.warehouse != employee.warehouse or not employee.warehouse):
                    failed_orders.append({'order_id': order.tracking_number, 'reason': f'You dont have access to receive orders that are not headed to your warehouse ({tracking.receiver.warehouse})'})
                    continue

                if tracking and tracking.driver:
                    order.order_status = 'in_warehouse'
                    tracking.tracking_status = 'done'
                    tracking.effective_date = datetime.datetime.now()

                    order.save()
                    tracking.save()
                    updated_orders.append(order_id)
                elif tracking and not tracking.driver:
                    failed_orders.append({'order_id': order.tracking_number, 'reason': 'No Driver assigned on the pickup tracking.'})
                else:
                    failed_orders.append({'order_id': order.tracking_number, 'reason': f'No ongoing tracking heading to your warehouse {employee.warehouse}.'})

        return JsonResponse({'success': True, 'failed_orders': failed_orders})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
def out_for_delivery_api(request):
    serializer = OutForDeliverySerializer(data=request.data)
    if serializer.is_valid():
        result = services.set_orders_out_for_delivery(
            serializer.validated_data['order_ids'],
            request.user,
            serializer.validated_data['driver_id']
        )
        return Response(result)
    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@role_required(allowed_roles=['employee'], employee_types=['driver'])
def confirm_pickup_driver(request):
    return confirmation_action(request, 'pickup', 'driver')

@api_view(['POST'])
@role_required(allowed_roles=['employee'], employee_types=['driver'])
def confirm_delivery_driver(request):
    return confirmation_action(request, 'delivery', 'driver')


def confirmation_action(request, action, role):
    if role not in ['driver', 'supplier'] or action not in ['pickup', 'delivery']:
        return JsonResponse({'success': False, 'error': 'Invalid role or action'}, status=400)
    try:
        serializer = OrderConfirmationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_id = serializer.validated_data['order_id']
        
        return services.confirm_action(request.user, order_id, role, action)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@api_view(['POST'])
def mark_as_delivered(request):
    order_ids = request.data.get('order_ids', [])
    provided_code = request.data.get('verification_code')
    if not order_ids:
        return JsonResponse({'success': False, 'error': 'No orders provided'})

    updated_orders = []
    failed_orders = []

    try:
        with transaction.atomic():
            for order_id in order_ids:
                order = Order.objects.select_for_update().filter(pk=order_id).first()
                if not order:
                    failed_orders.append({'order_id': order.tracking_number, 'reason': 'Order not found'})
                    continue

                from django.conf import settings
                if getattr(settings, 'REQUIRE_DELIVERY_CODE_VERIFICATION', False):
                    is_driver = Employee.objects.filter(user=request.user, employee_type='driver', active=True).exists()
                    if is_driver:
                        if len(order_ids) > 1:
                            return JsonResponse({'success': False, 'error': 'Drivers must confirm each delivery with its own code (select one order).'}, status=500)
                        
                        result = verify_phone_code(order, (provided_code or '').strip())
                        if not result.get('success'):
                            return JsonResponse({'success': False, 'error': 'Invalid Verification Code'}, status=500)
                
                if order.order_status != OrderStatuses.out_for_delivery:
                    failed_orders.append({'order_id': order.tracking_number, 'reason': f'Order should be Out For Delivery.'})
                    continue
                
                tracking = OrderTracking.objects.filter(
                    order_id=order_id,
                    receiver__location_type='customer',
                    tracking_status__in=['draft', 'pending']
                ).first()

                if tracking and tracking.driver:
                    order.order_status = OrderStatuses.delivered
                    order.effective_date = datetime.datetime.now()
                    
                    tracking.tracking_status = OrderTrackingStatuses.done
                    tracking.effective_date = datetime.datetime.now()

                    order.save()
                    tracking.save()
                    updated_orders.append(order_id)
                
                elif tracking and not tracking.driver:
                    failed_orders.append({'order_id': order.tracking_number, 'reason': 'No Driver assigned on the delivery tracking.'})
                else:
                    failed_orders.append({'order_id': order.tracking_number, 'reason': 'No ongoing delivery track to the customer.'})

        return JsonResponse({'success': True, 'failed_orders': failed_orders})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@role_required(allowed_roles=['employee', 'supplier'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def order_request_form_view(request, pk=None):
    instance = get_object_or_404(OrderRequest, pk=pk) if pk else None
    is_supplier, supplier = False, None
    if request.user.user_type == 'supplier':
        is_supplier = True
        supplier = Supplier.objects.get(user=request.user, active=True)

    form = OrderRequestForm(instance=instance, supplier=supplier, is_supplier=is_supplier)
    return render(request, 'forms/order_request_form.html', {'form': form, 'instance': instance})


@api_view(['GET'])
@role_required(allowed_roles=['employee', 'supplier'])
def order_request_list_view(request):
    if request.user.user_type == 'supplier':
        suppliers = Supplier.objects.filter(user=request.user, active=True)
    else:
        suppliers = Supplier.objects.filter(active=True)
    
    context = {
        "suppliers": suppliers,
        "warehouses": Warehouse.objects.filter(active=True),
        "drivers": Employee.objects.filter(employee_type="driver", active=True),
        "statuses": OrderRequestStatuses.choices,
    }
    return render(request, "lists/order_requests_list.html", context)


@api_view(['POST'])
@role_required(allowed_roles=['employee', 'supplier'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def order_request_save_api(request, pk=None):
    try:
        data = request.data
        instance = get_object_or_404(OrderRequest, pk=pk) if pk else None
        
        is_supplier = request.user.user_type == 'supplier'
        supplier = Supplier.objects.filter(user=request.user, active=True).first()

        form = OrderRequestForm(data, instance=instance, supplier=supplier, is_supplier=is_supplier)
        
        if form.is_valid():
            obj = form.save(commit=False)
            # ✅ If the logged-in user is a supplier, set supplier programmatically
            if is_supplier and supplier:
                obj.supplier = supplier
                obj.warehouse = supplier.warehouse
        
            obj.reference = obj.reference or generate_order_request_reference_number(request.user.company)
            obj.created_by = obj.created_by or request.user
            obj.created_at = obj.created_at or datetime.datetime.now()
            obj.status = obj.status or 'requested'
            obj.save()
            return JsonResponse({'success': True, 'id': obj.id})
        else:
            return JsonResponse({'success': False, 'error': str(form.errors)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def generate_order_request_reference_number(company) -> str:
    # Sequence-based reference using company config
    prefix = getattr(company, 'order_request_prefix', 'RQ') or 'RQ'
    length = getattr(company, 'order_request_seq_length', 5) or 5
    seq = NumberSequence.next(company, 'order_request')
    return f"{prefix}{str(seq).zfill(length)}"

@api_view(['POST'])
@role_required(allowed_roles=['employee', 'supplier'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def confirm_order_requests(request):
    try:
        if request.user.user_type == 'supplier':
            return JsonResponse({'success': False, 'error': 'Suppliers cannot confirm order requests'}, status=403)
        
        data = request.data
        order_request_ids = data.get('order_request_ids', [])

        if not order_request_ids:
            return JsonResponse({'success': False, 'error': 'Couldnt load order requests'}, status=400)

        confirmed_requests = []
        failed_requests = []

        with transaction.atomic():
            for request_id in order_request_ids:
                try:
                    order_request = OrderRequest.objects.select_for_update().get(pk=request_id)

                    if order_request.status == "confirmed":
                        failed_requests.append({'id': order_request.reference, 'reason': 'Already confirmed'})
                        continue
                    
                    if not order_request.driver:
                        failed_requests.append({'id': order_request.reference, 'reason': 'No driver assigned'})
                        continue
                    
                    if not order_request.warehouse:
                        failed_requests.append({'id': order_request.reference, 'reason': 'No pickup warehouse selected'})
                        continue

                    if not order_request.delivery_pricelist:
                        failed_requests.append({'id': order_request.reference, 'reason': 'Select a delivery pricelist first'})
                        continue
                    
                    if not order_request.supplier or not order_request.supplier.address:
                        failed_requests.append({'id': order_request.reference, 'reason': 'Supplier address not found'})
                        continue
                    
                    for _ in range(order_request.nb_orders):
                        order = Order.objects.create(
                            supplier=order_request.supplier,
                            delivery_pricelist=order_request.delivery_pricelist,
                            supplier_address=order_request.supplier.address,
                            pickup_warehouse=order_request.warehouse,
                            created_by=order_request.created_by,
                            order_date=order_request.created_at,
                            order_status=OrderStatuses.draft,
                            company=request.user.company,
                            order_request=order_request
                        )
                        
                        order.planned_route = order.compute_planned_route()
                        response  = services.confirm_order(order=order, driver=order_request.driver, user=request.user)

                        if not response.get('success'):
                            failed_requests.append({'id': order_request.reference, 'reason': 'Orders created but couldnt confirm them'})
                        
                    order_request.status = "confirmed"
                    order_request.save(update_fields=["status"])
                    confirmed_requests.append(order_request.id)
                
                except OrderRequest.DoesNotExist:
                    failed_requests.append({'id': request_id, 'reason': 'Not found'})
                except Exception as inner_error:
                    transaction.set_rollback(True)
                    return JsonResponse({'success': False, 'error': str(inner_error)}, status=500)

        return JsonResponse({
            'success': True,
            'confirmed_requests': confirmed_requests,
            'failed_requests': failed_requests,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@api_view(['POST'])
def cancel_order_requests(request):
    try:
        order_request_ids = request.data.get('order_request_ids', [])

        if not order_request_ids:
            return JsonResponse({'success': False, 'error': 'Couldnt load order requests'}, status=400)

        failed_requests = []

        with transaction.atomic():
            for request_id in order_request_ids:
                try:
                    order_request = OrderRequest.objects.filter(id=request_id).first()

                    if not order_request:
                        failed_requests.append({'id': request_id, 'reason': 'OrderRequest not found'})
                        continue
                
                    if order_request.status != OrderRequestStatuses.requested:
                        failed_requests.append({'id': order_request.reference, 'reason': 'Can only cancel draft requests'})
                        continue
                    
                    related_orders = Order.objects.filter(order_request=order_request)
                    non_draft_orders = related_orders.exclude(order_status=OrderStatuses.draft)

                    if non_draft_orders.exists():
                        failed_requests.append({'id': order_request.reference, 'reason': 'Some orders already confirmed or in progress'})
                        continue
                
                    related_orders.update(is_cancelled=True, order_status=OrderStatuses.cancelled)
                    order_request.status = OrderRequestStatuses.cancelled
                    order_request.cancelled_by = request.user
                    order_request.save(update_fields=['status', 'cancelled_by'])
                
                except Exception as inner_error:
                    transaction.set_rollback(True)
                    return JsonResponse({'success': False, 'error': str(inner_error)}, status=500)

        return JsonResponse({
            'success': True,
            'failed_requests': failed_requests,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def send_to_next_warehouse_form(request):
    drivers = Employee.objects.filter(employee_type='driver', active=True)
    warehouses = Warehouse.objects.filter(active=True)
    employee = Employee.objects.filter(user=request.user, active=True).first()

    return render(request, 'forms/send_to_next_warehouse_form.html', {
        'drivers': drivers,
        'warehouses': warehouses,
        'employee': employee,
    })

@api_view(['POST'])
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def send_to_next_warehouse(request):
    try:
        data = request.data
        order_ids = [int(oid) for oid in data.get('order_ids', [])]
        from_warehouse_id = int(data.get('from_warehouse') or 0)
        target_warehouse_id = int(data.get('target_warehouse') or 0)
        driver_id = int(data.get('driver_id') or 0)

        if not order_ids or not target_warehouse_id or not driver_id or not from_warehouse_id:
            return JsonResponse({'success': False, 'error': 'Missing required data'})

        driver = Employee.objects.filter(pk=driver_id, employee_type='driver', active=True).first()
        if not driver:
            return JsonResponse({'success': False, 'error': 'Driver not found (or not active anymore)'})

        target_warehouse = Warehouse.objects.filter(pk=target_warehouse_id).first()
        sender_warehouse = Warehouse.objects.filter(pk=from_warehouse_id).first()
        if not target_warehouse or not sender_warehouse:
            return JsonResponse({'success': False, 'error': 'Invalid warehouse selection'})
        if target_warehouse == sender_warehouse:
            return JsonResponse({'success': False, 'error': 'You cant transfer to the same warehouse'})

        target_location = StockLocation.objects.filter(location_type='warehouse', warehouse=target_warehouse).first()
        sender_location = StockLocation.objects.filter(location_type='warehouse', warehouse=sender_warehouse).first()
        if not target_location or not sender_location:
            return JsonResponse({'success': False, 'error': 'Warehouse Location for the selected warehouse is not found'})

        failed_orders = []
        with transaction.atomic():
            orders = Order.objects.select_for_update().filter(id__in=order_ids)
            for oid in order_ids:
                if oid not in orders.values_list('id', flat=True):
                    failed_orders.append({'order_id': oid, 'reason': 'Order not found or invalid status'})

            for order in orders:
                if order.order_status not in ['in_warehouse', 'in_warehouse_transit'] and not order.is_cancelled:
                    failed_orders.append({'order_id': order.tracking_number, 'reason': 'Order Status doesnt allow this action.'})
                    
                # Verify order currently at sender warehouse (last completed warehouse tracking)
                last_tracking = (OrderTracking.objects
                    .filter(order=order, receiver__location_type='warehouse', tracking_status='done')
                    .order_by('-effective_date', '-created_at')
                    .first())
                if not last_tracking or last_tracking.receiver != sender_location:
                    failed_orders.append({'order_id': order.tracking_number, 'reason': f'Order not found in {sender_warehouse.name}'})
                    continue

                # Check if there is ongoing tracking with same sender/receiver
                existing_tracking = (OrderTracking.objects
                    .filter(order=order, sender=sender_location, receiver=target_location,
                            tracking_status__in=['draft', 'pending']).first())
                
                if existing_tracking:
                    # update driver and addresses if needed
                    existing_tracking.driver = driver
                    existing_tracking.sender_address = sender_location.warehouse.address
                    existing_tracking.receiver_address = target_location.warehouse.address
                    existing_tracking.tracking_status = OrderTrackingStatuses.pending
                    existing_tracking.updated_by = request.user
                    existing_tracking.save()
                
                else:
                    # Create new transit tracking
                    OrderTracking.objects.create(
                        order=order,
                        sender=sender_location,
                        receiver=target_location,
                        sender_address=sender_location.warehouse.address,
                        receiver_address=target_location.warehouse.address,
                        driver=driver,
                        tracking_status=OrderTrackingStatuses.pending,
                        created_by=request.user,
                        created_at=datetime.datetime.now()
                    )

                order.order_status = OrderStatuses.in_warehouse_transit
                order.save(update_fields=['order_status'])

        return JsonResponse({'success': True, 'failed_orders': failed_orders})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_allowed_pricelist_items(pricelist, source, destination):
    items = DeliveryPriceListItem.objects.filter(
        pricelist_id=pricelist,
        source_warehouse=source,
        destination_warehouse=destination,
    ).all()
    
    if not items:
        items = DeliveryPriceListItem.objects.filter(
            pricelist_id=pricelist,
            source_warehouse=None,
            destination_warehouse=None,
        ).all()
    
    return items

@api_view(['GET'])
def get_package_types_for_pricelist(request):
    pricelist_id = request.GET.get('pricelist_id')
    if not pricelist_id:
        return JsonResponse({'package_types': []})
    
    pickup_warehouse = request.GET.get('pickup_warehouse', None)
    delivery_warehouse = request.GET.get('delivery_warehouse', None)
    if not pickup_warehouse or not delivery_warehouse:
        return JsonResponse({'package_types': []})
    

    items = get_allowed_pricelist_items(pricelist_id, pickup_warehouse, delivery_warehouse)

    package_types = [
        {
            'id': item.id,
            'name': item.package_type.name,
            'fees': float(item.fees),
        }
        for item in items
    ]

    return JsonResponse({'package_types': package_types})

@api_view(['GET'])
def get_supplier_pricelist(request):
    supplier_id = request.GET.get('supplier_id')
    pricelist_id = None
    warehouse_id = None
    warehouse_name = None

    if supplier_id:
        try:
            supplier = Supplier.objects.select_related('delivery_pricelist', 'warehouse').get(pk=supplier_id)
            if supplier.delivery_pricelist:
                pricelist_id = supplier.delivery_pricelist.pk
            if supplier.warehouse:
                warehouse_id = supplier.warehouse.pk
                warehouse_name = supplier.warehouse.name
        except Supplier.DoesNotExist:
            pass

    return JsonResponse({
        'pricelist_id': pricelist_id,
        'warehouse_id': warehouse_id,
        'warehouse_name': warehouse_name,
    })


@api_view(['POST'])
@role_required(allowed_roles=['employee'])
def cancel_order_api(request, order_id):
   try:
       with transaction.atomic():
           order = get_object_or_404(Order, pk=order_id)

           # Guard: already finalized in another way
           if order.order_status in [OrderStatuses.returned, OrderStatuses.cancelled] or order.is_cancelled or order.is_exchanged:
               return JsonResponse({'success': False, 'error': 'Order is already cancelled/exchanged'}, status=400)

           # If any done tracking exists, pickup already happened; this API is only for pre-pickup
           if order.order_tracking.filter(tracking_status=OrderTrackingStatuses.done).exists():
               return JsonResponse({'success': False, 'error': 'Pickup already done; please do `Return and Cancel`'}, status=400)

           # Cancel draft/pending trackings (no return/exchange needed pre-pickup)
           draft_pending = order.order_tracking.filter(
               tracking_status__in=[OrderTrackingStatuses.draft, OrderTrackingStatuses.pending]
           )
           if draft_pending.exists():
               draft_pending.update(
                   tracking_status=OrderTrackingStatuses.cancelled,
                   updated_by=request.user,
                   effective_date=datetime.datetime.now()
               )

           # Mark order cancelled
           order.order_status = OrderStatuses.cancelled
           order.cancelled_at = datetime.datetime.now()
           order.cancelled_by = request.user
           order.save(update_fields=['order_status', 'cancelled_at', 'cancelled_by'])

           return JsonResponse({'success': True, 'message': 'Order cancelled successfully'}, status=200)
   except Exception as e:
       return JsonResponse({'success': False, 'error': str(e)}, status=500)


def validate_return_and_cancel_request_data(request, order_id) -> dict:
    try:
        order = get_object_or_404(Order, pk=order_id)
        if order.order_status in [OrderStatuses.returned, OrderStatuses.cancelled] or order.is_cancelled or order.is_exchanged:
            return {'success': False, 'error': 'Order is already cancelled/exchanged'}
        
        return_from_warehouse_id = int(request.data.get('return_from_warehouse') or 0)
        driver_id = int(request.data.get('driver_id') or 0)
        
        if not return_from_warehouse_id or not driver_id:
            return {'success': False, 'error': 'Missing Warehouse or driver'}
        
        return_from_warehouse = Warehouse.objects.filter(pk=return_from_warehouse_id).first()
        if not return_from_warehouse:
            return {'success': False, 'error': 'Invalid return-from warehouse'}
        
        return_from_location = StockLocation.objects.filter(location_type='warehouse', warehouse=return_from_warehouse).first()
        if not return_from_location:
            return {'success': False, 'error': 'Return-from warehouse location not found'}
        
        driver = Employee.objects.filter(pk=driver_id, employee_type='driver', active=True).first()
        if not driver:
            return {'success': False, 'error': 'Driver not found (or not active anymore)'}
    
        return {'success': True, 'order': order, 'return_from_warehouse': return_from_warehouse, 'driver': driver}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

@api_view(['POST'])
@role_required(allowed_roles=['employee'])
def return_and_cancel_order_api(request, order_id):
    """Cancel order and, if already at selected warehouse, create return-to-supplier tracking.

    Expects: return_from_warehouse (warehouse id), driver_id
    """
    validation = validate_return_and_cancel_request_data(request, order_id)
    if not validation.get('success'):
        return JsonResponse({'success': False, 'error': validation.get('error')}, status=400)

    response = services.return_and_cancel(validation.get('order'), request.user, validation.get('return_from_warehouse') , validation.get('driver'))
    return JsonResponse(response, status=200 if response.get('success') else 400)


@api_view(['POST'])
@role_required(allowed_roles=['employee'])
def send_to_supplier_api(request, order_id):
    """Create or update a tracking from selected warehouse to supplier for the order.

    Validates that the order's last completed tracking location equals the selected warehouse.
    Expects payload keys: return_from_warehouse (warehouse id), driver_id
    """
    try:
        with transaction.atomic():
            order = get_object_or_404(Order, pk=order_id)
            
            if not order.is_cancelled and not order.is_exchanged:
                return JsonResponse({'success': False, 'error': 'Order must be cancelled or exchanged before returning to supplier'}, status=400)
                
            data = request.data

            warehouse_id = int((data.get('return_from_warehouse') or 0))
            driver_id = int((data.get('driver_id') or 0))

            if not warehouse_id or not driver_id:
                return JsonResponse({'success': False, 'error': 'Missing Warehouse or driver'}, status=400)

            driver = Employee.objects.filter(pk=driver_id, employee_type='driver', active=True).first()
            if not driver:
                return JsonResponse({'success': False, 'error': 'Driver not found (or not active anymore)'}, status=400)

            warehouse = Warehouse.objects.filter(pk=warehouse_id).first()
            if not warehouse:
                return JsonResponse({'success': False, 'error': 'Invalid warehouse'}, status=400)

            sender_location = StockLocation.objects.filter(location_type='warehouse', warehouse=warehouse).first()
            if not sender_location:
                return JsonResponse({'success': False, 'error': 'Warehouse stock location not found'}, status=400)

            supplier_location = StockLocation.objects.filter(location_type='supplier').first()
            if not supplier_location:
                return JsonResponse({'success': False, 'error': 'Supplier stock location not configured'}, status=500)

            # Validate current order location
            last_tracking = (OrderTracking.objects
                .filter(order=order, tracking_status=OrderTrackingStatuses.done)
                .order_by('-effective_date', '-created_at')
                .first())

            if not last_tracking or last_tracking.receiver != sender_location:
                current_wh = last_tracking.receiver.warehouse.name if last_tracking and last_tracking.receiver and last_tracking.receiver.warehouse else 'Unknown'
                return JsonResponse({'success': False, 'error': f'Order is found in "{current_wh}" not {warehouse}, please send it first.'}, status=400)

            # Find existing draft/pending tracking to supplier from this warehouse
            tracking = (OrderTracking.objects
                .filter(order=order, sender=sender_location, receiver__location_type='supplier',
                        tracking_status__in=[OrderTrackingStatuses.draft, OrderTrackingStatuses.pending])
                .first())

            if tracking:
                tracking.driver = driver
                tracking.sender_address = sender_location.warehouse.address if sender_location and sender_location.warehouse else None
                tracking.receiver = supplier_location
                tracking.receiver_address = order.supplier_address
                tracking.tracking_status = OrderTrackingStatuses.pending
                tracking.updated_by = request.user
                tracking.save()
                action = 'updated'
            else:
                OrderTracking.objects.create(
                    order=order,
                    sender=sender_location,
                    receiver=supplier_location,
                    sender_address=sender_location.warehouse.address if sender_location and sender_location.warehouse else None,
                    receiver_address=order.supplier_address,
                    driver=driver,
                    tracking_status=OrderTrackingStatuses.pending,
                    created_by=request.user,
                    created_at=datetime.datetime.now()
                )
                action = 'created'

            # Update order status to transit between locations
            order.order_status = OrderStatuses.out_for_supplier
            order.save(update_fields=['order_status'])

            return JsonResponse({'success': True, 'message': f'Return-to-supplier tracking {action}.'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@api_view(['POST'])
@role_required(allowed_roles=['employee']) 
def return_and_exchange_order_api(request, order_id):
    """Cancel order and, if already at selected warehouse, create return-to-supplier tracking.
    And then create an exchange order and link it to the original order.

    Expects: return_from_warehouse (warehouse id), driver_id
    """
    # same logic as return and cancel
    validation = validate_return_and_cancel_request_data(request, order_id)
    if not validation.get('success'):
        return JsonResponse({'success': False, 'error': validation.get('error')}, status=400)

    response = services.return_and_cancel(validation.get('order'), request.user, validation.get('return_from_warehouse') , validation.get('driver'))
    if not response.get('success'):
        return JsonResponse(response, status=400)
    
    # create exchange order
    try:
        result = exchange_services.create_exchange_order(original_id=order_id, actor=request.user, reason=request.data.get('reason', ''))
        if result is None:
            return JsonResponse({"success": False, "error": "Failed to create exchange order."}, status=500)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse(response, status=200 if response.get('success') else 400)

@api_view(['POST'])
@role_required(allowed_roles=['employee'])
def mark_returned_to_supplier(request, order_id):
    try:
        with transaction.atomic():
            order = get_object_or_404(Order, pk=order_id)
            
            if not order.is_cancelled:
                return JsonResponse({'success': False, 'error': 'Order must be cancelled before marking as returned to supplier'}, status=400)
            
            # get the tracking going from the warehouse to the supplier and make it done and change order status to returned
            tracking = order.order_tracking.filter(
                sender__location_type='warehouse',
                receiver__location_type='supplier',
                tracking_status__in=[OrderTrackingStatuses.draft,OrderTrackingStatuses.pending]
            ).first()
            
            if not tracking:
                return JsonResponse({'success': False, 'error': 'No valid tracking found for returning to supplier'}, status=400)
            
            employee = Employee.objects.filter(user=request.user, active=True).first()       
            if employee and employee.employee_type == 'driver' and tracking.driver.user != request.user:
                return JsonResponse({'success': False, 'error': 'Confirmation failed, you are not the assigned driver'}, status=403)
            
            # Find the last completed tracking
            last_tracking = (OrderTracking.objects
                .filter(order=order, tracking_status='done')
                .order_by('-effective_date', '-created_at')
                .first())
            
            if last_tracking.receiver != tracking.sender:
                return JsonResponse({'success': False, 'error': 'Order is not currently at the warehouse that is selected to be returned from'}, status=400)
            
            tracking.tracking_status = OrderTrackingStatuses.done
            tracking.effective_date = datetime.datetime.now()
            tracking.updated_by = request.user
            tracking.save()
            
            order.order_status = OrderStatuses.returned
            order.effective_date = datetime.datetime.now()
            order.updated_by = request.user
            # order.is_cancelled = False  # no need anymore to have it cancelled
            # order.is_exchanged = False  # no need anymore to have it as exchanged
            order.save()
            return JsonResponse({'success': True, 'message': 'Order marked as returned to supplier successfully'}, status=200)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    

def _label_blocks(order):
    packages = list(OrderPackages.objects.filter(order=order).order_by("id"))
    total = len(packages) or 1

    supplier, customer = order.supplier, order.customer
    # Prepare collection display based on currency
    amount = None
    order_price_fmt = None
    delivery_fees_fmt = None
    
    if order.currency_secondary and order.currency_secondary != order.currency:
        # Show split lines: order price (with secondary) + fees in USD
        order_price_fmt = display_order_price(order)
        delivery_fees_fmt = format_currency(order.total_delivery_fees or 0)
    
    else:
        try:
            is_usd = (order.currency and getattr(order.currency, 'name', '').upper() == 'USD')
        except Exception:
            is_usd = False
        if is_usd:
            # Sum and format in USD
            total_val = (order.order_price or 0) + (order.total_delivery_fees or 0)
            amount = format_currency(total_val)
        else:
            # Show split lines: order price (with optional secondary) + fees in USD
            order_price_fmt = display_order_price(order)
            delivery_fees_fmt = format_currency(order.total_delivery_fees or 0)

    blocks = []
    for i, pkg in enumerate(packages or [None], 1):
        blocks.append({
            "package_counter": f"{i}/{total}",
            "supplier_name": supplier.name if supplier else "N/A",
            "supplier_phone": supplier.phone_number if supplier else "N/A",
            "supplier_address": order.supplier_address if order.supplier_address else "",
            "customer_name": customer.name if customer else "N/A",
            "customer_phone": customer.phone_number if customer else "N/A",
            "customer_address": order.customer_address if order.customer_address else "",
            "amount": amount,
            "order_price": order_price_fmt,
            "delivery_fees": delivery_fees_fmt,
            "payment_method": getattr(order, "payment_method", "Cash"),
            "created_at": order.order_date.strftime("%Y-%m-%d %H:%M:%S") if order.order_date else "",
            "company_logo": order.company.logo.url if order.company and order.company.logo else "",
            "company_name": order.company.name if order.company else "",
            "barcode_url": barcode_data_uri(order.tracking_number),
            "tracking_number": order.tracking_number,
            "description": pkg.description if pkg else "",
            "requirement": pkg.package_requirment if pkg and pkg.package_requirment else "",
            "printed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    return blocks

@login_required
def download_order_labels(request, pk: int):
    order = get_object_or_404(Order, pk=pk)
    response = render_template_to_pdf(
        request,
        "reports/print_labels.html",
        {"packages": _label_blocks(order)}
    )
    return pdf_download(response, f"order-{order.tracking_number}-labels")


@login_required
def multi_download_order_labels(request):
    try:
        if request.method != "POST":
            return HttpResponseBadRequest("Invalid request method")
    
        ids = [int(order_id) for order_id in request.POST.get('order_ids', '').split(',') if order_id.isdigit()]
        if not ids:
            return HttpResponseBadRequest("No orders selected")

        blocks = []
        for o in Order.objects.filter(id__in=ids).order_by("id"):
            blocks.extend(_label_blocks(o))

        pdf_bytes = render_template_to_pdf(request, "reports/print_labels.html", {"packages": blocks})
        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="{len(ids)}-orders-labels.pdf"'
        resp["Content-Length"] = str(len(pdf_bytes))
        return resp
    except Exception as e:
        return HttpResponseBadRequest(f"Error: {str(e)}")



# ---------------------------
# Public Order Tracking Views
# ---------------------------
def public_track_lookup(request):
    """Public page to enter a tracking number and redirect to detail view."""
    error = None
    if request.method == 'POST':
        tracking = (request.POST.get('tracking_number') or '').strip()
        if tracking:
            return redirect('orders:public_track_detail', tracking_number=tracking)
        error = 'Please enter a tracking number.'

    return render(request, 'public/track_lookup.html', {
        'error': error,
    })


def _build_tracking_timeline(order: Order):
    """Create a timeline list from order and its tracking legs.

    Each entry: { title, subtitle, status, date, icon }
    status in: done | pending | draft | cancelled
    """
    items = []

    # Order placed
    if order.order_date:
        currency_label = ''
        if order.currency:
            try:
                currency_label = order.currency.symbol or order.currency.name
            except Exception:
                currency_label = ''
        items.append({
            'title': f"Order {order.tracking_number} Placed",
            'subtitle': f"Total: {order.total_amount} {currency_label}",
            'status': 'done',
            'date': order.order_date,
            'icon': 'fa-bell'
        })

    # Tracking legs
    legs = order.order_tracking.filter(tracking_status__in=['draft', 'pending', 'done']).order_by('effective_date')
    for leg in legs:
        status = leg.tracking_status
        title = 'Transit'
        if leg.receiver and leg.receiver.location_type == 'customer' and status == 'done':
            title = 'Delivered'
        elif leg.receiver and leg.sender.location_type == 'supplier' and status == 'done':
            title = 'Picked Up'
        
        items.append({
            'title': title,
            'subtitle': f"{leg.sender.name if leg.sender else ''} → {leg.receiver.name if leg.receiver else ''}",
            'status': status,
            'date': leg.effective_date or leg.created_at,
            'icon': 'fa-truck' if status in ['pending', 'draft'] else 'fa-check-circle'
        })

    return items


def public_track_detail(request, tracking_number: str):
    """Public order tracking detail page (no login required)."""
    order = Order.objects.filter(tracking_number__iexact=tracking_number).first()
    if not order:
        return render(request, 'public/track_detail.html', {
            'not_found': True,
            'tracking_number': tracking_number,
        })

    timeline = _build_tracking_timeline(order)

    packages = order.order_packages.all()
    share_url = request.build_absolute_uri(
        reverse('orders:public_track_detail', kwargs={'tracking_number': order.tracking_number})
    )

    context = {
        'order': order,
        'packages': packages,
        'timeline': timeline,
        'share_url': share_url,
        'estimated_delivery': order.estimated_delivery_date,
    }
    return render(request, 'public/track_detail.html', context)
