from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view

from .models import Company, Warehouse, Currency, StockLocation
from . import utils
from .forms import WarehouseForm, CurrencyForm, StockLocationForm, AddressForm

from django.shortcuts import render, get_object_or_404, redirect
from .models import RoutingRule
from .forms import RoutingRuleForm, RoutingStepFormSet, CompanyForm, CompanySequenceForm
from .decorators import role_required

from orders.services import metrics
from orders.models import Order, OrderTracking
from orders.models.order import OrderStatuses
from django.db.models import Q
from rest_framework.decorators import api_view

@login_required
def dashboard(request):
    # ✅ add total sum here
    delivered_week = metrics.delivered_this_week_by_day()
    delivered_week_total = sum(item['total'] for item in delivered_week)
    context = {
        "orders_in_warehouse": metrics.get_orders_in_warehouse(),
        "delivery_success_rate": metrics.get_delivery_success_rate(),
        "orders_by_status": metrics.get_orders_by_status(),
        "average_delivery_time": metrics.get_average_delivery_time(),
        "new_orders_3d": metrics.new_orders_last_n_days(3),
        "snapshot": metrics.status_snapshot(),
        "awaiting_pickup": metrics.awaiting_pickup(),
        "delivered_week": delivered_week,
        "delivered_week_total": delivered_week_total,
        "delayed_count": metrics.delayed_orders_count(),
        "delayed_sample": metrics.delayed_orders_sample(5),
        "on_time_rate": metrics.on_time_delivery_rate(),
        "avg_delay": metrics.average_delay_late_orders(),
    }
    return render(request, "dashboard.html", context)


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def companies(request):
    companies = Company.objects.filter(active=True)
    return render(request, 'companies.html', {'companies': companies})


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def update_company_profile(request):
    company = get_object_or_404(Company, pk=request.user.company.id) if request.user.company else None

    if request.method == "POST":
        form = CompanyForm(request.POST, request.FILES, instance=company)
        address_form = AddressForm(request.POST, instance=company.address)
        seq_form = CompanySequenceForm(request.POST, instance=company)

        if form.is_valid() and address_form.is_valid() and seq_form.is_valid():
            # Save address first
            address = address_form.save()

            # Save company profile
            company = form.save(commit=False)
            company.address = address
            company.save()
            # Save sequence config
            seq_form.instance = company
            seq_form.save()

            return redirect("company_profile")  # redirect to a detail page or dashboard
    else:
        form = CompanyForm(instance=company)
        address_form = AddressForm(instance=company.address)
        seq_form = CompanySequenceForm(instance=company)

    return render(request, "forms/form_template.html", {
        "form": form,
        "address_form": address_form,
        "sequence_form": seq_form,
        "form_title": "Update Company Profile",
        "redirect_back_url": "/",  # adjust as needed
    })


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def warehouses(request):
    # Filter by active flag via query param ?active=1|0 (default 1)
    active_param = (request.GET.get('active') or '1').strip().lower()
    is_active = not (active_param in ['0', 'false', 'no'])
    warehouses = Warehouse.objects.filter(active=is_active)
    return render(request, 'warehouses.html', {
        'warehouses': warehouses,
        'active_flag': 1 if is_active else 0,
    })

@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def create_warehouse(request):
    if request.method == "POST":
        form = WarehouseForm(request.POST)
        address_form = AddressForm(request.POST)

        if form.is_valid() and address_form.is_valid():
            address = address_form.save()
            warehouse = form.save(commit=False)
            warehouse.address = address
            warehouse.save()
            return redirect('update_warehouse', pk=warehouse.pk)

    else:  # GET
        form = WarehouseForm()
        address_form = AddressForm()

    return render(request, 'forms/form_template.html', {
        'form': form,
        'address_form': address_form,
        'form_title': 'Create Warehouse',
        'redirect_back_url': '/warehouses',
    })



@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def update_warehouse(request, pk):
    instance = get_object_or_404(Warehouse, pk=pk)

    # GET → Show forms with existing data
    if request.method == "GET":
        form = WarehouseForm(instance=instance)
        address_form = AddressForm(instance=instance.address)
    
    # POST → Validate and save
    else:
        form = WarehouseForm(request.POST, instance=instance)
        address_form = AddressForm(request.POST, instance=instance.address)

        if form.is_valid() and address_form.is_valid():
            address = address_form.save()
            warehouse = form.save(commit=False)
            warehouse.address = address
            warehouse.save()
            return redirect('update_warehouse', pk=pk)

    return render(request, 'forms/form_template.html', {
        'form': form,
        'address_form': address_form,
        'form_title': 'Update Warehouse',
        'redirect_back_url': '/warehouses',
    })


@api_view(['POST'])
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def archive_warehouses(request):
    try:
        data = request.data
        ids = data.get('ids') or []
        if not ids:
            return JsonResponse({'success': False, 'error': 'No warehouses selected'}, status=400)

        failed = []
        open_exclude = [OrderStatuses.delivered, OrderStatuses.cancelled, OrderStatuses.returned]
        for wid in ids:
            wh = Warehouse.objects.filter(pk=wid).first()
            if not wh:
                failed.append({'id': wid, 'reason': 'Not found'})
                continue

            # Direct order usage (pickup/delivery warehouse) on open orders
            used_order = Order.objects.filter(~Q(order_status__in=open_exclude)) \
                .filter(Q(pickup_warehouse=wh) | Q(delivery_warehouse=wh)) \
                .exists()

            # Tracking usage through stock location on open orders
            loc = StockLocation.objects.filter(location_type='warehouse', warehouse=wh).first()
            used_trk = False
            if loc:
                used_trk = OrderTracking.objects.filter(
                    ~Q(order__order_status__in=open_exclude)
                ).filter(Q(sender=loc) | Q(receiver=loc)).exists()

            if used_order or used_trk:
                failed.append({'id': wh.name, 'reason': 'warehouse is used by open orders.'})
                continue

            wh.active = False
            wh.save(update_fields=['active'])
            loc.active = False
            loc.save(update_fields='active')

        return JsonResponse({'success': True, 'message': 'Selected warehouses archived', 'failed_orders': failed})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def delete_warehouses(request):
    try:
        data = request.data
        ids = data.get('ids') or []
        if not ids:
            return JsonResponse({'success': False, 'error': 'No warehouses selected'}, status=400)

        failed = []
        deleted = 0
        for wid in ids:
            wh = Warehouse.objects.filter(pk=wid).first()
            if not wh:
                failed.append({'id': wid, 'reason': 'Not found'})
                continue
            refs = utils.get_object_references(wh, include_counts=False)
            if refs:
                failed.append({'id': wh.name, 'reason': 'warehouse is linked to some models. Please archive instead.'})
                continue
            wh.delete()
            deleted += 1

        return JsonResponse({'success': True, 'message': f'{deleted} warehouse(s) deleted', 'failed_orders': failed})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def unarchive_warehouses(request):
    try:
        data = request.data
        ids = data.get('ids') or []
        if not ids:
            return JsonResponse({'success': False, 'error': 'No warehouses selected'}, status=400)

        failed = []
        updated = 0
        for wid in ids:
            wh = Warehouse.objects.filter(pk=wid).first()
            if not wh:
                failed.append({'id': wid, 'reason': 'Not found'})
                continue
            if wh.active:
                failed.append({'id': wh.name, 'reason': 'Warehouse already active'})
                continue
            wh.active = True
            wh.save(update_fields=['active'])
            updated += 1

        return JsonResponse({'success': True, 'message': f'{updated} warehouse(s) unarchived', 'failed_orders': failed})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def currencies(request):
    currencies = Currency.objects.filter()
    return render(request, 'currencies.html', {'currencies': currencies})

@login_required
@csrf_exempt
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def create_currency(request):
    if request.method == 'POST':
        form = CurrencyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('currencies')
    else:
        form = CurrencyForm()
    
    return render(request, 'forms/form_template.html', {'form': form, 'form_title': 'Add Currency', 'redirect_back_url': '/currencies'})


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def delete_currency(request, pk):
    if request.method != 'POST':
        return HttpResponse(status=405)

    currency = Currency.objects.filter(pk=pk).first()
    if not currency:
        return render(request, 'currencies.html', {'currencies': Currency.objects.all()})

    # Generic validation: check any reverse relation has rows
    refs = utils.get_object_references(currency, include_counts=False)
    if refs:
        # Build a friendly message with up to 3 model names
        names = []
        for r in refs[:3]:
            try:
                names.append(r['model'].__name__)
            except Exception:
                names.append('Related data')
        from django.http import JsonResponse
        return JsonResponse({
            'success': False,
            'error': f"Cannot delete currency: it is referenced by {', '.join(names)} (and possibly more)."
        }, status=400)

    currency.delete()
    from django.http import JsonResponse
    return JsonResponse({'success': True, 'message': 'Currency deleted'})


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def get_stock_locations(request):
    # Filter by active via query param ?active=1|0 (default 1)
    active_param = (request.GET.get('active') or '1').strip().lower()
    is_active = not (active_param in ['0', 'false', 'no'])
    locations = StockLocation.objects.filter(active=is_active)
    return render(request, 'stock_locations.html', {
        'stockLocations': locations,
        'active_flag': 1 if is_active else 0,
    })

@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def stock_location_form_view(request, pk=None):
    location = get_object_or_404(StockLocation, pk=pk) if pk else None
    
    form = StockLocationForm(request.POST or None, instance=location)

    if request.method == 'POST':
        if form.is_valid():
            # Server-side uniqueness validation
            loc_type = form.cleaned_data.get('location_type')
            wh = form.cleaned_data.get('warehouse')
            company = request.user.company

            # Existing object id for exclusion when updating
            current_id = location.id if location else None

            # Rule 1: Only one supplier location per company
            if loc_type == 'supplier' and StockLocation.objects.filter(company=company, location_type='supplier').exclude(pk=current_id).exists():
                form.add_error('location_type', 'Only one Supplier location is allowed per company.')

            # Rule 2: Only one customer location per company
            if loc_type == 'customer' and StockLocation.objects.filter(company=company, location_type='customer').exclude(pk=current_id).exists():
                form.add_error('location_type', 'Only one Customer location is allowed per company.')

            # Rule 3: One warehouse location per warehouse
            if loc_type == 'warehouse':
                if not wh:
                    form.add_error('warehouse', 'Warehouse is required for warehouse location type.')
                else:
                    if StockLocation.objects.filter(location_type='warehouse', warehouse=wh).exclude(pk=current_id).exists():
                        form.add_error('warehouse', 'Each Warehouse must have exactly one Stock location.')

            if not form.errors:
                location = form.save(commit=False)
                location.company = request.user.company
                location.save()
                # Stay on the edit page after save (for both create/update)
                return redirect('update_stock_location', pk=location.pk)

    
    return render(request, 'forms/stock_location_form.html', { 'form_title': 'Stock Location', 'location_form': form})


# Stock Locations bulk APIs (POST-only, no login_required as requested)
@api_view(['POST'])
def archive_stock_locations(request):
    try:
        ids = (request.data.get('ids') or [])
        failed = []
        updated = 0
        open_exclude = [OrderStatuses.delivered, OrderStatuses.cancelled, OrderStatuses.returned]
        for sid in ids:
            loc = StockLocation.objects.filter(pk=sid).first()
            if not loc:
                failed.append({'id': sid, 'reason': 'Not found'})
                continue
            # Is used in any tracking of open orders?
            used = OrderTracking.objects.filter(~Q(order__order_status__in=open_exclude)) \
                .filter(Q(sender=loc) | Q(receiver=loc)).exists()
            if used:
                failed.append({'id': sid, 'reason': 'Location used by open orders'})
                continue
            loc.active = False
            loc.save(update_fields=['active'])
            updated += 1
        return JsonResponse({'success': True, 'message': f'{updated} location(s) archived', 'failed_orders': failed})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
def unarchive_stock_locations(request):
    try:
        ids = (request.data.get('ids') or [])
        failed = []
        updated = 0
        for sid in ids:
            loc = StockLocation.objects.filter(pk=sid).first()
            if not loc:
                failed.append({'id': sid, 'reason': 'Not found'})
                continue
            if loc.active:
                failed.append({'id': sid, 'reason': 'Location already active'})
                continue
            loc.active = True
            loc.save(update_fields=['active'])
            updated += 1
        return JsonResponse({'success': True, 'message': f'{updated} location(s) unarchived', 'failed_orders': failed})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
def delete_stock_locations(request):
    try:
        ids = (request.data.get('ids') or [])
        failed = []
        deleted = 0
        for sid in ids:
            loc = StockLocation.objects.filter(pk=sid).first()
            if not loc:
                failed.append({'id': sid, 'reason': 'Not found'})
                continue
            refs = utils.get_object_references(loc, include_counts=False)
            if refs:
                failed.append({'id': sid, 'reason': 'Location has related data. Please archive instead of delete.'})
                continue
            loc.delete()
            deleted += 1
        return JsonResponse({'success': True, 'message': f'{deleted} location(s) deleted', 'failed_orders': failed})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def routing_rule_list(request):
    rules = RoutingRule.objects.all().prefetch_related('steps', 'from_warehouse', 'to_warehouse')
    return render(request, 'routing_rules.html', {'rules': rules})


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin'])
def routing_rule_form_view(request, pk=None):
    instance = get_object_or_404(RoutingRule, pk=pk) if pk else None

    form = RoutingRuleForm(request.POST or None, instance=instance)
    formset = RoutingStepFormSet(request.POST or None, instance=instance)

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            rule = form.save()
            formset.instance = rule
            formset.save()
            return redirect('routing_rules')  # update this URL as needed

    return render(request, 'forms/routing_rule_form.html', {
        'form': form,
        'formset': formset,
        'instance': instance,
        'warehouses': Warehouse.objects.filter(active=True).all(),  # For the dynamic row select box
    })
