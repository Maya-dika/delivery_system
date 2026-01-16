from django import forms
from django_countries.widgets import CountrySelectWidget
from django_countries import countries

from django.forms import inlineformset_factory
from .models import RoutingRule, RoutingStep
from .models import Company, Warehouse, Currency, StockLocation, Address
from users.models import Employee


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class CompanySequenceForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['order_prefix', 'order_seq_length', 'order_request_prefix', 'order_request_seq_length']
        widgets = {
            'order_prefix': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., ORD'}),
            'order_seq_length': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'order_request_prefix': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., RQ'}),
            'order_request_seq_length': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class CustomCompanyAdminForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['address'].required = False
        self.fields['parent_company'].required = False


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['country', 'city', 'street', 'building', 'zip_code']
        widgets = {
            'country': CountrySelectWidget(
                layout="{widget}",  # ✅ disables the flag image!
                attrs={'class': 'form-select'}
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        allowed_countries = ['LB']  # ✅ your allowed list
        choices = [(code, name) for code, name in countries if code in allowed_countries]

        self.fields['country'].choices = choices
        self.fields['street'].required = False
        self.fields['building'].required = False
        self.fields['zip_code'].required = False


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'warehouse_manager', 'company']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['warehouse_manager'].queryset = Employee.objects.filter(employee_type='warehouse_manager', active=True)
        

class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ['name', 'symbol']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'symbol': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
class StockLocationForm(forms.ModelForm):
    class Meta:
        model = StockLocation
        fields = ['name', 'location_type', 'warehouse']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location_type':  forms.Select(attrs={'class': 'form-select'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['warehouse'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        location_type = cleaned_data.get('location_type')
        warehouse = cleaned_data.get('warehouse')

        if location_type == 'warehouse' and not warehouse:
            self.add_error('warehouse', 'Warehouse is required when location type is warehouse.')
        return cleaned_data


class RoutingRuleForm(forms.ModelForm):
    class Meta:
        model = RoutingRule
        fields = ['from_warehouse', 'to_warehouse']


class RoutingStepForm(forms.ModelForm):
    class Meta:
        model = RoutingStep
        fields = ['warehouse', 'position']


RoutingStepFormSet = inlineformset_factory(
    RoutingRule,
    RoutingStep,
    form=RoutingStepForm,
    extra=0,
    can_delete=True,
)
