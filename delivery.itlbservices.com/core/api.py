from django.http import JsonResponse
from django.db.models import Q
from rest_framework.decorators import api_view
from core.decorators import role_required
from core.models import Warehouse


@api_view(["GET"])
@role_required(allowed_roles=['employee', 'supplier'],  employee_types=['admin'])
def api_warehouse_list(request):
    params = request.GET

    # DataTables parameters
    search = params.get('search[value]', '')
    start = int(params.get('start', 0))
    length = int(params.get('length', 20))
    draw = int(params.get('draw', 1))

    order_column_index = params.get('order[0][column]')
    order_column_name = params.get(f'columns[{order_column_index}][data]', 'name')
    order_direction = params.get('order[0][dir]', 'asc')

    # Filter by active flag via query param ?active=1|0 (default 1)
    active_param = (params.get('active') or '1').strip().lower()
    is_active = not (active_param in ['0', 'false', 'no'])
    base_qs = Warehouse.objects.filter(active=is_active).select_related('company', 'warehouse_manager', 'address')

    # Apply search across key fields
    if search:
        base_qs = base_qs.filter(
            Q(name__icontains=search) |
            Q(company__name__icontains=search) |
            Q(warehouse_manager__name__icontains=search)
        )

    total_records = base_qs.count()

    # Secure ordering
    allowed_order_fields = ['name', 'company', 'warehouse_manager', 'active']
    if order_column_name not in allowed_order_fields:
        order_column_name = 'name'
    ordering = order_column_name if order_direction == 'asc' else f'-{order_column_name}'

    qs = base_qs.order_by(ordering)[start:start + length]

    data = []
    for wh in qs:
        address_str = ''
        if wh.address:
            parts = [wh.address.street, wh.address.city]
            address_str = ', '.join([p for p in parts if p])
        
        data.append({
            "id": wh.id,
            "name": wh.name,
            "company": wh.company.name if wh.company else '',
            "warehouse_manager": wh.warehouse_manager.name if wh.warehouse_manager else '',
            "active": wh.active,
            "address": address_str,
        })

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data,
    })
