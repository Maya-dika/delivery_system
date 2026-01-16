from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from core.utility.pdf import render_template_to_pdf, pdf_download
from core.decorators import role_required
from users.models import Employee

from .models.order import OrderStatuses
from .api import api_general_report, api_driver_statement, api_employees_performance

from decimal import Decimal
import datetime
import json
import logging

logger = logging.getLogger(__name__)


# -----------------------------
# Account Statement Report
# -----------------------------
@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def account_statement_view(request):
    return render(request, 'reports/account_statement.html')


# -----------------------------
# General Report
# -----------------------------
@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def general_report_view(request):
    context = {
        'statuses': OrderStatuses.choices,
        'drivers': Employee.objects.filter(employee_type='driver', active=True).order_by('name'),
    }
    return render(request, 'reports/general_report.html', context)


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def general_report_print(request):
    try:
        # Reuse API logic for data
        api_resp = api_general_report(request)
        if api_resp.status_code != 200:
            return api_resp
        payload = json.loads(api_resp.content.decode('utf-8'))
        if not payload.get('success'):
            return JsonResponse({'success': False, 'error': payload.get('error', 'Failed')}, status=500)

        rows = payload.get('data', [])
        totals = payload.get('totals', {})

        # Applied filters (only those set)
        applied = []
        from_str = request.GET.get('from')
        to_str = request.GET.get('to')
        if from_str or to_str:
            applied.append(f"Date: {from_str or ''} to {to_str or ''}")
        st = (request.GET.get('status') or '').strip()
        if st:
            st_label = dict(OrderStatuses.choices).get(st, st)
            applied.append(f"Status: {st_label}")
        driver_id = request.GET.get('driver')
        if driver_id:
            try:
                drv = Employee.objects.get(pk=driver_id)
                applied.append(f"Driver: {drv.name}")
            except Employee.DoesNotExist:
                pass
        fees = (request.GET.get('delivery_fees') or '').strip()
        if fees:
            applied.append(f"Delivery Fees = {fees}")
        comm = (request.GET.get('driver_commission') or '').strip()
        if comm:
            applied.append(f"Driver Commission = {comm}")
        pay = (request.GET.get('payment_method') or '').strip()
        if pay:
            applied.append(f"Payment: {pay}")

        company = getattr(request.user, 'company', None)
        ctx = {
            'company': company,
            'printed_at': datetime.datetime.now(),
            'applied_filters': applied,
            'rows': rows,
            'totals': {
                'total_delivery_fees': totals.get('total_fees', ''),
                'driver_commission': totals.get('total_commissions', ''),
                'profit': totals.get('total_profit', ''),
            }
        }
        pdf_bytes = render_template_to_pdf(request, 'reports/general_report_pdf.html', ctx)
        return pdf_download(pdf_bytes, f"general-report-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}")
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ----------------------
# Driver Statement Report
# ----------------------
@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def driver_statement_view(request):
    context = {
        'drivers': Employee.objects.filter(employee_type='driver', active=True).order_by('name')
    }
    return render(request, 'reports/driver_statement.html', context)


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def driver_statement_print(request):
    try:
        api_resp = api_driver_statement(request)
        if api_resp.status_code != 200:
            return api_resp
        payload = json.loads(api_resp.content.decode('utf-8'))
        if not payload.get('success'):
            return JsonResponse({'success': False, 'error': payload.get('error', 'Failed')}, status=500)

        rows = payload.get('data', [])
        totals = payload.get('totals', {})

        applied = []
        from_str = request.GET.get('from')
        to_str = request.GET.get('to')
        if from_str or to_str:
            applied.append(f"Date: {from_str or ''} to {to_str or ''}")
        driver_id = request.GET.get('driver')
        if driver_id:
            try:
                drv = Employee.objects.get(pk=driver_id)
                applied.append(f"Driver: {drv.name}")
            except Employee.DoesNotExist:
                pass
        fees = (request.GET.get('delivery_fees') or '').strip()
        if fees:
            applied.append(f"Delivery Fees = {fees}")
        comm = (request.GET.get('driver_commission') or '').strip()
        if comm:
            applied.append(f"Driver Commission = {comm}")

        company = getattr(request.user, 'company', None)
        from datetime import datetime as _dt
        ctx = {
            'company': company,
            'printed_at': _dt.now(),
            'applied_filters': applied,
            'rows': rows,
            'totals': {
                'nb_orders': totals.get('nb_orders', ''),
                'total_fees': totals.get('total_fees', ''),
                'total_commission': totals.get('total_commission', ''),
                'profit': totals.get('profit', ''),
            }
        }
        pdf_bytes = render_template_to_pdf(request, 'reports/driver_statement_pdf.html', ctx)
        return pdf_download(pdf_bytes, f"driver-statement-{_dt.now().strftime('%Y%m%d-%H%M')}")
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# -----------------------------
# Employees Performance Report
# -----------------------------
@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def employees_performance_view(request):
    return render(request, 'reports/employees_performance.html')


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def employees_performance_print(request):
    try:
        api_resp = api_employees_performance(request)
        if api_resp.status_code != 200:
            return api_resp
        payload = json.loads(api_resp.content.decode('utf-8'))
        if not payload.get('success'):
            return JsonResponse({'success': False, 'error': payload.get('error', 'Failed')}, status=500)

        rows = payload.get('data', [])
        totals = payload.get('totals', {})

        company = getattr(request.user, 'company', None)
        from datetime import datetime as _dt
        from_str = request.GET.get('from') or ''
        to_str = request.GET.get('to') or ''
        applied = []
        if from_str or to_str:
            applied.append(f"Date: {from_str} to {to_str}")
        fees = (request.GET.get('delivery_fees') or '').strip()
        if fees:
            applied.append(f"Delivery Fees = {fees}")
        comm = (request.GET.get('driver_commission') or '').strip()
        if comm:
            applied.append(f"Driver Commission = {comm}")

        ctx = {
            'company': company,
            'printed_at': _dt.now(),
            'applied_filters': applied,
            'rows': rows,
            'totals': totals,
            'range_text': f"{from_str} to {to_str}" if (from_str or to_str) else ''
        }
        pdf_bytes = render_template_to_pdf(request, 'reports/employees_performance_pdf.html', ctx)
        return pdf_download(pdf_bytes, f"drivers-performance-{_dt.now().strftime('%Y%m%d-%H%M')}")
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)