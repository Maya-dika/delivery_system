from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django_countries import countries
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, logout, update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authtoken.models import Token
from rest_framework import status

from .models import User, Employee, Supplier, Customer
from .models import user as UserModel, UserTypes
from .forms import UserForm, EmployeeForm, CustomerForm, LoginForm, UserPasswordResetForm, UserSetPasswordForm, UserPasswordChangeForm
from .forms import SupplierForm, OptionalUserForm, AddressFormSet, AddressForm
from core.models import Address, Warehouse
from core.decorators import role_required

import datetime
import phonenumbers

@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def all_system_users(request):
    sys_users = User.objects.filter(is_active=True)
    return render(request, 'lists/users.html', {'users': sys_users})


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def save_user(request, pk):
    user = get_object_or_404(User, pk=pk) if pk else None
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('users:users')
    else:
        form = UserForm(instance=user)
    return render(request, 'forms/form_template.html', {'form': form, 'form_title': 'Update User' if pk else 'Create User', 'redirect_back_url': '/users'})


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def employees(request):
    employees = Employee.objects.filter().exclude(employee_type="driver")
    return render(request, 'lists/employees.html', {'employees': employees})

@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def drivers(request):
    drivers = Employee.objects.filter(employee_type="driver", active=True)
    return render(request, 'lists/employees.html', {'employees':drivers})


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def save_employee(request, pk=None):
    employee = get_object_or_404(Employee, pk=pk) if pk else None
    form = EmployeeForm(request.POST or None, instance=employee)
    user_form = OptionalUserForm(request.POST or None, instance=employee.user if employee else None)
    form.user_form = user_form
    
    redirect_back_url = '/users/employees/'
    if employee and employee.employee_type == 'driver':
        redirect_back_url = '/users/drivers/'

    if request.method == 'POST':
        if form.is_valid() and form.user_form.is_valid():
            form.save()
            if employee and employee.employee_type == 'driver':
                return redirect('users:drivers')
            return redirect('users:employees')
    
    return render(request, 'forms/form_template.html', {'form': form, 'form_title': 'Update Employee' if pk else 'Create Employee', 'redirect_back_url': redirect_back_url})


@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def suppliers(request):
    suppliers = Supplier.objects.filter()
    return render(request, 'lists/suppliers.html', {'suppliers': suppliers})

@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def supplier_create(request):
    supplier_form = SupplierForm(request.POST or None)
    user_form = OptionalUserForm(request.POST or None)
    address_form = AddressForm(request.POST or None)
    create_user = request.POST.get("create_user") == "1"
    user_has_account = create_user

    if request.method == 'POST':
        is_valid = (
            supplier_form.is_valid() and
            address_form.is_valid() and
            (not create_user or user_form.is_valid())
        )

        if is_valid:
            supplier = supplier_form.save(commit=False)

            if create_user:
                user = user_form.save(commit=False)
                user = fill_user_info(
                    user,
                    UserTypes.SUPPLIER,
                    supplier.name,
                    supplier.phone_number,
                    supplier.email,
                    supplier.company
                )
                user.save()
                supplier.user = user

            address = address_form.save()
			
            supplier.address = address
            supplier.created_by = request.user
            supplier.created_at = datetime.datetime.now()
            supplier.save()
            return redirect('users:suppliers')

    return render(request, 'forms/supplier_form_view.html', {
        'form_title': 'Create',
        'supplier_form': supplier_form,
        'user_form': user_form,
        'address_form': address_form,
        'user_has_account': user_has_account
    })


def _save_user_from_form(user_form, supplier):
    user = user_form.save(commit=False)
    user = fill_user_info(user, UserTypes.SUPPLIER , supplier.name, supplier.phone_number, supplier.email, supplier.company)
    user.save()
    return user

@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager'])
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    user_has_account = supplier.user is not None

    if request.method == 'POST':
        supplier_form = SupplierForm(request.POST, instance=supplier)
        address_form = AddressForm(request.POST)

        user_form_submitted = request.POST.get('username')
        user_form = OptionalUserForm(request.POST, instance=supplier.user if supplier.user else None) if user_form_submitted else None

        if supplier_form.is_valid() and address_form.is_valid() and (not user_form or user_form.is_valid()):
            supplier = supplier_form.save(commit=False)

            if user_form:
                user = _save_user_from_form(user_form, supplier)
                supplier.user = user
                user_has_account = True

            address = address_form.save()
            supplier.address = address
            supplier.updated_by = request.user
            supplier.updated_at = datetime.datetime.now()
            supplier.save()

            return redirect('users:update_supplier', pk=supplier.pk)

        elif user_form and not user_form.is_valid():
            user_has_account = True

    else:
        supplier_form = SupplierForm(instance=supplier)
        user_form = OptionalUserForm(instance=supplier.user or None)
        address_form = AddressForm(instance=supplier.address or None)

    return render(request, 'forms/supplier_form_view.html', {
        'form_title': 'Update',
        'supplier_form': supplier_form,
        'user_form': user_form,
        'address_form': address_form,
        'user_has_account': user_has_account
    })

@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def create_supplier_modal_view(request):
    if request.method == "GET":
        warehouses = Warehouse.objects.filter(active=True)
        allowed_countries = ['LB']
        country_choices = [(code, name) for code, name in countries if code in allowed_countries]

        return render(request, 'forms/supplier_modal_form.html', {
            'warehouses': warehouses,
            'countries': country_choices,
        })
    
    elif request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        domain = request.POST.get('domain_description')
        warehouse = request.POST.get('warehouse')
        country = request.POST.get('country')
        city = request.POST.get('city')
        street = request.POST.get('street')
        building = request.POST.get('building')
        zip_code = request.POST.get('zip_code')
        create_user = request.POST.get('create_user')
        username = request.POST.get('username')
        password = request.POST.get('password')

        form_data = {
            'name': name,
            'email': email,
            'phone_number': phone_number,
            'domain_description': domain,
            'warehouse': warehouse,
            'country': country,
            'city': city,
            'street': street,
            'building': building,
            'zip_code': zip_code,
            'create_user': create_user == 'on',
            'username': username,
        }

        # validate phone number; on error, re-render modal with message and original inputs
        region = country or 'LB'
        try:
            num = phonenumbers.parse(phone_number or '', region)
            if not phonenumbers.is_valid_number(num):
                raise ValidationError('Invalid phone number for the selected country.')

        except Exception:
            warehouses = Warehouse.objects.filter(active=True)
            allowed_countries = ['LB']
            country_choices = [(code, name) for code, name in countries if code in allowed_countries]
            return render(request, 'forms/supplier_modal_form.html', {
                'warehouses': warehouses,
                'countries': country_choices,
                'error': 'Invalid phone number. Please enter a valid number.',
                'form_data': form_data,
            })

        user = None
        if create_user == 'on':
            user = User.objects.create(
                username=username,
                password=password,
                user_type='supplier',
                company=request.user.company
            )
        
        address = Address.objects.create(
            country=country,
            city=city,
            street=street,
            building=building,
            zip_code=zip_code
        )
        
        # Create supplier
        supplier = Supplier.objects.create(
            name=name,
            email=email,
            phone_number=phone_number,
            domain_description=domain,
            address=address,
            warehouse=Warehouse.objects.get(pk=int(warehouse) or 0),
            user=user,
            company=request.user.company,
            created_by=request.user,
            created_at=datetime.datetime.now()
        )

        return render(request, 'forms/supplier_success_modal.html', {
            'supplier': supplier,
            'address': address
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})



@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def customers(request):
    customers = Customer.objects.filter()
    return render(request, 'lists/customers.html', {'customers': customers})

@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def customer_create(request):
    customer_form = CustomerForm(request.POST or None)
    user_form = OptionalUserForm(request.POST or None)
    address_formset = AddressFormSet(request.POST or None)
    create_user = request.POST.get("create_user") == "1"
    user_has_account = create_user

    if request.method == 'POST':
        is_valid = (
            customer_form.is_valid() and
            address_formset.is_valid() and
            (not create_user or user_form.is_valid())
        )

        if is_valid:
            customer = customer_form.save(commit=False)

            if create_user:
                user = user_form.save(commit=False)
                user = fill_user_info(user, UserTypes.CUSTOMER, customer.name, customer.phone_number, customer.email, customer.company)
                user.save()
                customer.user = user

            customer.created_at = datetime.datetime.now()
            customer.created_by = request.user
					   
            customer.save()

            addresses = []
            for form in address_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    address = form.save()
                    addresses.append(address)

            customer.addresses.set(addresses)

            return redirect('users:customers')							 

    return render(request, 'forms/customer_form_view.html', {
        'form_title': 'Create',
        'customer_form': customer_form,
        'user_form': user_form,
        'address_formset': address_formset,
        'user_has_account': user_has_account
    })

@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    user_has_account = customer.user is not None

    if request.method == 'POST':
        customer_form = CustomerForm(request.POST, instance=customer)
        address_formset = AddressFormSet(request.POST)
        
        user_form_submitted = request.POST.get('username')
        user_form = OptionalUserForm(request.POST, instance=customer.user if customer.user else None) if user_form_submitted else None
												
        # if 'delete_user' in request.POST and customer.user:
        #     customer.user.is_active = False
        #     customer.user.save()
        #     customer.user = None
        #     customer.save()
        #     user_has_account = False

        if customer_form.is_valid() and address_formset.is_valid() and (not user_form or user_form.is_valid()):
            customer = customer_form.save(commit=False)

            if user_form:
                user = user_form.save(commit=False) # password logic handled in form
                user = fill_user_info(user, UserTypes.CUSTOMER, customer.name, customer.phone_number, customer.email, customer.company)
                user.save()
                customer.user = user
                user_has_account = True

            addresses = []
            for form in address_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    address = form.save()
                    addresses.append(address)

            customer.addresses.set(addresses)

            customer.updated_by = request.user
            customer.updated_at = datetime.datetime.now()
            customer.save()

            return redirect('users:update_customer', pk=customer.pk)

		
        elif user_form and not user_form.is_valid():																	
            user_has_account = True

	
    else:
        customer_form = CustomerForm(instance=customer)
        user_form = OptionalUserForm(instance=customer.user or None)
        initial_data = [
            {
                'country': address.country,
                'city': address.city,
                'street': address.street,
                'building': address.building,
                'zip_code': address.zip_code,
            }
            for address in customer.addresses.all()
        ]
        address_formset = AddressFormSet(initial=initial_data)


    return render(request, 'forms/customer_form_view.html', {
        'form_title': 'Update',
        'customer_form': customer_form,
        'user_form': user_form,
        'address_formset': address_formset,
        'user_has_account': user_has_account,
    })


def fill_user_info(user, type, name, phone_number, email, company):
    user.full_name = name
    user.user_type = type
    user.phone_number = phone_number
    user.email = email
    user.company = company
    return user

@login_required
@role_required(allowed_roles=['employee'], employee_types=['admin', 'warehouse_manager', 'internal_user'])
def create_customer_modal_view(request):
    if request.method == "GET":
        allowed_countries = ['LB']
        country_choices = [(code, name) for code, name in countries if code in allowed_countries]

        return render(request, 'forms/customer_modal_form.html', {
            'countries': country_choices,
        })
    
    elif request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        country = request.POST.get('country')
        city = request.POST.get('city')
        street = request.POST.get('street')
        building = request.POST.get('building')
        zip_code = request.POST.get('zip_code')
        create_user = request.POST.get('create_user')
        username = request.POST.get('username')
        password = request.POST.get('password')

        form_data = {
            'name': name,
            'email': email,
            'phone_number': phone_number,
            'country': country,
            'city': city,
            'street': street,
            'building': building,
            'zip_code': zip_code,
            'create_user': create_user == 'on',
            'username': username,
        }

        # validate phone number; on error, re-render modal with message and original inputs
        region = country or 'LB'
        try:
            num = phonenumbers.parse(phone_number or '', region)
            if not phonenumbers.is_valid_number(num):
                raise ValidationError('Invalid phone number for the selected country.')

        except Exception:
            allowed_countries = ['LB']
            country_choices = [(code, name) for code, name in countries if code in allowed_countries]
            return render(request, 'forms/customer_modal_form.html', {
                'countries': country_choices,
                'error': 'Invalid phone number. Please enter a valid number.',
                'form_data': form_data,
            })

        user = None
        if create_user == 'on':
            user = User.objects.create(
                username=username,
                password=password,
                user_type='customer',
                company=request.user.company
            )
        
        # customer customer
        customer = Customer.objects.create(
            name=name,
            email=email,
            phone_number=phone_number,
            user=user,
            company=request.user.company,
            created_by=request.user,
            created_at=datetime.datetime.now()
        )

        address = Address.objects.create(
            country=country,
            city=city,
            street=street,
            building=building,
            zip_code=zip_code
        )
        customer.addresses.add(address)

        return render(request, 'forms/customer_success_modal.html', {
            'customer': customer,
            'address': address
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def create_address(request, entity_type, entity_id):
    if request.method == "GET":
        allowed_countries = ['LB']
        country_choices = [(code, name) for code, name in countries if code in allowed_countries]

        return render(request, 'forms/address_modal_form.html', {
            'countries': country_choices,
            'entity_type': entity_type,
            'entity_id': entity_id,
        })
    
    elif request.method == 'POST':
        if entity_type == '' or entity_id == 0:
            return JsonResponse({'success': False, 'error': 'Invalid request'})
        
        country = request.POST.get('country')
        city = request.POST.get('city')
        street = request.POST.get('street')
        building = request.POST.get('building')
        zip_code = request.POST.get('zip_code')

        address = Address.objects.create(
            country=country,
            city=city,
            street=street,
            building=building,
            zip_code=zip_code
        )
        if entity_type == 'customer':
            customer = Customer.objects.get(pk=entity_id)
            customer.addresses.add(address)
        elif entity_type == 'supplier':
            supplier = Supplier.objects.get(pk=entity_id)
            supplier.address = address
            supplier.save()
            

        return render(request, 'forms/address_success_modal.html', {
            'entity_type': entity_type,
            'address': address
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})

@api_view(['GET'])
def get_supplier_addresses(request, supplier_id):
    try:
        supplier = Supplier.objects.get(pk=supplier_id)
        address = supplier.address
        data = [
            {"id": address.id, "text": str(address)}
        ]
        return JsonResponse({"success": True, "addresses": data})
    except Supplier.DoesNotExist:
        return JsonResponse({"success": False, "error": "Supplier not found"}, status=404)

@api_view(['GET'])
def get_supplier_warehouse(request, supplier_id):
    try:
        supplier = Supplier.objects.get(pk=supplier_id)
        return JsonResponse({"success": True, "warehouse_id": supplier.warehouse.id if supplier.warehouse else None})
    except Supplier.DoesNotExist:
        return JsonResponse({"success": False, "error": "Supplier not found"}, status=404)

@api_view(['GET'])
def get_customer_addresses(request, customer_id):
    try:
        customer = Customer.objects.get(pk=customer_id)
        addresses = customer.addresses.all()
        data = [
            {"id": addr.id, "text": str(addr)}
            for addr in addresses
        ]
        return JsonResponse({"success": True, "addresses": data})
    except Customer.DoesNotExist:
        return JsonResponse({"success": False, "error": "Customer not found"}, status=404)


@api_view(['POST'])
def change_password_view(request):
    data = request.data
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    user = request.user
    if not user.check_password(old_password):
        return JsonResponse({'success': False, 'error': 'Old password is incorrect'}, status=400)

    user.set_password(new_password)
    user.save()
    update_session_auth_hash(request, user)  # Prevent logout after password change
    return JsonResponse({'success': True, 'message': 'Password updated successfully'})


class UserLoginView(auth_views.LoginView):
  template_name = 'forms/login.html'
  form_class = LoginForm
  success_url = '/'

class UserPasswordResetView(auth_views.PasswordResetView):
  template_name = 'forms/forgot-password.html'
  form_class = UserPasswordResetForm

class UserPasswordChangeView(auth_views.PasswordChangeView):
  template_name = 'forms/password_change.html'
  form_class = UserPasswordChangeForm
  success_url = reverse_lazy('users:password_change_done')

@login_required
def user_logout_view(request):
  logout(request)
  return redirect('/users/login/')

@api_view(["POST"])
@authentication_classes([])  # 🚫 No auth required
@permission_classes([])      # 🚫 Anyone can call
def login_api(request):
    """
    Mobile login endpoint that returns token
    """
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        
        # Get employee if exists
        employee = user.employee_user.first()
        employee_type = employee.employee_type if employee else None
        
        is_supplier = user.user_type == 'supplier'
        if is_supplier:
            supplier = Supplier.objects.filter(user=user, active=True).first()
            supplier_id = supplier.id if supplier else None
        else:
            supplier_id = None
        # Prepare user data
        user_data = {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "user_type": user.user_type,
        }
        
        # Prepare employee data
        employee_data = None
        if employee:
            employee_data = {
                "id": employee.id,
                "name": employee.name,
                "email": employee.email,
                "phone_number": employee.phone_number,
                "employee_type": employee.employee_type,
                "active": employee.active,
            }
        
        response_data = {
            "token": token.key,
            "user": user_data,
            "employee": employee_data,
            "employee_type": employee_type,
            "supplier_id": supplier_id,
        }
        
        return JsonResponse(response_data)
    return JsonResponse({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout_api(request):
    """
    Mobile logout - delete token
    """
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
        return JsonResponse({'message': 'Logout successful'})
    except Token.DoesNotExist:
        return JsonResponse({'message': 'Already logged out'})
