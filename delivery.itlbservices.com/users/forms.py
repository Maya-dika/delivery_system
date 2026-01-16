from django import forms
from django.forms import formset_factory
from django_countries.widgets import CountrySelectWidget
from django_countries import countries
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm, PasswordResetForm, UsernameField
from django.core.exceptions import ValidationError

from .models import User, Employee, Supplier, Customer
from core.models import Address

import phonenumbers


class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    password = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))


class UserPasswordResetForm(PasswordResetForm):
  email = forms.EmailField(widget=forms.EmailInput(attrs={
    'class': 'form-control',
    'placeholder': 'Email'
  }))

class UserSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'New Password'
    }), label="New Password")
    new_password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm New Password'
    }), label="Confirm New Password")
    

class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Old Password'
    }), label='Old Password')
    new_password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'New Password'
    }), label="New Password")
    new_password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm New Password'
    }), label="Confirm New Password")
    

class CustomUserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number', 'username', 'password', 'user_type', 'company', 'is_active']
        widgets = {
            'user_type': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.RadioSelect(attrs={'class': 'form-control d-flex'}, choices=[(True,'Active'), (False, 'Inactive')]),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        self.fields['password'].required = False
        self.fields['is_active'].label = "Active User"
        self._original_password = self.instance.password  # store original

    def clean_phone_number(self):
        phone = (self.cleaned_data.get('phone_number') or '').strip()
        if not phone:
            return phone

        region = 'LB'
        try:
            num = phonenumbers.parse(phone, region)
            if not phonenumbers.is_valid_number(num):
                raise ValidationError('Invalid phone number for the selected country.')
            return phone
        except Exception:
            raise ValidationError('Invalid phone number.')
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.instance.pk and not password:
            raise forms.ValidationError('Password is required for new users.')
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        if not self.cleaned_data.get('password'):
            user.password = self._original_password  # preserve password
        else:
            user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()
        return user


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'email', 'phone_number', 'employee_type', 'commission', 'manager', 'warehouse', 'company', 'active']
        widgets = {
            'employee_type': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'active': forms.RadioSelect(attrs={'class': 'form-control d-flex'}, choices=[(True,'Active'), (False, 'Inactive')]),
        }
    
    def is_valid(self):
        return super().is_valid() and self.user_form.is_valid()
    
    def __init__(self, *args, **kwargs):
        # self.user_form = OptionalUserForm(*args, **kwargs)
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        self.fields['manager'].required = False
        self.fields['active'].label = "Employee Status"
        # Commission field configuration
        if 'commission' in self.fields:
            self.fields['commission'].label = 'Commission (USD)'
            self.fields['commission'].widget = forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'})
            emp_type = None
            try:
                emp_type = self.instance.employee_type if self.instance and self.instance.pk else None
            except Exception:
                emp_type = None
            if not emp_type:
                emp_type = self.data.get('employee_type') or self.initial.get('employee_type')
            if emp_type != 'driver':
                self.fields['commission'].required = False
                self.fields['commission'].widget = forms.HiddenInput()

    def clean_phone_number(self):
        phone = (self.cleaned_data.get('phone_number') or '').strip()
        if not phone:
            return phone

        region = 'LB'
        try:
            num = phonenumbers.parse(phone, region)
            if not phonenumbers.is_valid_number(num):
                raise ValidationError('Invalid phone number for the selected country.')
            return phone
        except Exception:
            raise ValidationError('Invalid phone number.')
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        user = self.user_form.save(commit=False)

        # Fill extra user fields
        user.full_name = self.cleaned_data['name']
        user.user_type = 'employee'
        user.company = employee.company

        if commit:
            user.save()
            employee.user = user
            employee.save()

        return employee


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone_number', 'user', 'company', 'active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'active': forms.RadioSelect(attrs={'class': 'form-control d-flex'}, choices=[(True,'Active'), (False, 'Inactive')]),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        self.fields['user'].required = False
        self.fields['active'].label = "Customer Status"

    def clean_phone_number(self):
        phone = (self.cleaned_data.get('phone_number') or '').strip()
        if not phone:
            return phone

        # Default country LB; can be adapted to use first address country if available
        region = 'LB'
        try:
            num = phonenumbers.parse(phone, region)
            if not phonenumbers.is_valid_number(num):
                raise ValidationError('Invalid phone number for the selected country.')
            return phone
        except Exception:
            raise ValidationError('Invalid phone number.')
        

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'email', 'phone_number', 'domain_description', 'company', 'warehouse', 'active', 'delivery_pricelist']
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select', 'placeholder': 'Select a Warehouse'}),
            'active': forms.RadioSelect(attrs={'class': 'form-control d-flex'}, choices=[(True,'Active'), (False, 'Inactive')]),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['warehouse'].required = False
        self.fields['delivery_pricelist'].required = False
        self.fields['active'].label = "Merchant Status"

    def clean_phone_number(self):
        phone = (self.cleaned_data.get('phone_number') or '').strip()
        if not phone:
            return phone

        # Default country LB; can be adapted to use first address country if available
        region = 'LB'
        try:
            num = phonenumbers.parse(phone, region)
            if not phonenumbers.is_valid_number(num):
                raise ValidationError('Invalid phone number for the selected country.')
            return phone
        except Exception:
            raise ValidationError('Invalid phone number.')
        

class OptionalUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password', 'is_active']
        widgets = {
            'is_active': forms.RadioSelect(attrs={'class': 'form-control d-flex'}, choices=[(True,'Active'), (False, 'Inactive')]),
            'password': forms.PasswordInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].required = False
        self.fields['password'].required = False
        self._original_password = self.instance.password  # store original
        self.fields['is_active'].label = "User Status"
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.instance.pk and not password:
            raise forms.ValidationError('Password is required for new users.')
        return password
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if not self.cleaned_data.get('password'):
            user.password = self._original_password  # preserve password
        else:
            user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()
        return user


class AddressForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        allowed_countries = ['LB']  # ✅ your allowed list
        choices = [(code, name) for code, name in countries if code in allowed_countries]

        self.fields['country'].choices = choices
        self.fields['street'].required = False
        self.fields['building'].required = False
        self.fields['zip_code'].required = False

    class Meta:
        model = Address
        fields = ['country', 'city', 'street', 'building', 'zip_code']
        widgets = {
            'country': CountrySelectWidget(
                layout="{widget}",  # ✅ disables the flag image!
                attrs={'class': 'form-select'}
            ),
        }


AddressFormSet = formset_factory(AddressForm, extra=0, can_delete=True)
