from django import forms
from django.forms import modelform_factory, modelformset_factory
from django_select2.forms import ModelSelect2Widget

from .models import Order, OrderPackages, PackageType, PackageRequirments, OrderRequest, DeliveryPriceList, DeliveryPriceListItem
from users.models import Supplier, Customer, Employee
from core.models import Warehouse
from .permissions import get_allowed_order_actions

class SupplierSelectWidget(ModelSelect2Widget):
    model = Supplier
    search_fields = [
        'name__icontains',
        'phone_number__icontains',
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add unique identifier to prevent conflicts
        self.attrs.update({
            'data-widget-type': 'supplier-select2',
            'data-minimum-input-length': 1,
        })

    def label_from_instance(self, obj):
        return f"{obj.name} [{obj.phone_number}]"


class CustomerSelectWidget(ModelSelect2Widget):
    model = Customer
    search_fields = [
        'name__icontains',
        'phone_number__icontains',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add unique identifier to prevent conflicts
        self.attrs.update({
            'data-widget-type': 'customer-select2',
            'data-minimum-input-length': 1,
        })
    
    def label_from_instance(self, obj):
        return f"{obj.name} [{obj.phone_number}]"


class OrderForm(forms.ModelForm):
    received_by_driver = forms.ModelChoiceField(
        queryset=Employee.objects.filter(employee_type='driver', active=True),
        required=False,
        label="Received By (Driver)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    class Meta:
        model = Order
        fields = ['tracking_number', 'supplier', 'customer', 'supplier_address', 'customer_address', 
                  'order_status', 'total_amount', 'total_delivery_fees', 'order_price', 'driver_commission',
                  'pickup_warehouse', 'delivery_warehouse', 'delivery_pricelist', 'estimated_delivery_date', 'effective_date',
                  'is_cancelled', 'cancelled_by', 'cancelled_at', 'is_exchanged', 'exchange_reason', 'exchanged_at', 'currency']
        # is_direct_to_warehouse is intentionally appended to ensure visibility in form
        fields = fields + ['is_direct_to_warehouse', 'order_price_secondary', 'currency_secondary']
        widgets = {
            'supplier': SupplierSelectWidget(
                attrs={'data-placeholder': 'Search Supplier...', 'style': 'width: 100%'}
            ),
            'customer': CustomerSelectWidget(
                attrs={'data-placeholder': 'Search Customer...', 'style': 'width: 100%'}
            ),
            'estimated_delivery_date': forms.DateInput(
                attrs={
                    'type': 'date',   # HTML5 native date picker
                    'class': 'form-control',
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        order = kwargs.get("instance")
        super().__init__(*args, **kwargs)
        
        self.fields['tracking_number'].required = False
        self.fields['tracking_number'].disabled = True
        self.fields['tracking_number'].initial = 'DRAFT'
        self.fields['order_status'].disabled = True
        self.fields['delivery_warehouse'].required = False
        self.fields['pickup_warehouse'].required = False
        self.fields['estimated_delivery_date'].required = False
        self.fields['exchange_reason'].disabled = True
        self.fields['effective_date'].label = "Delivered At"
        self.fields['effective_date'].required = False
        self.fields['customer'].required = False
        self.fields['customer_address'].required = False
        self.fields['driver_commission'].disabled = True
        # Total amount removed from UI; keep disabled to avoid binding
        if 'total_amount' in self.fields:
            self.fields['total_amount'].disabled = True
            self.fields['total_amount'].required = False
        
        # Role-based edit restriction
        if user:
            allowed_actions = get_allowed_order_actions(user)
            if "edit" not in allowed_actions:
                for field in self.fields.values():
                    field.disabled = True
        
        # Order-status-based restriction for all users
        if order and (order.order_status in ["out_for_delivery", "delivered", "cancelled", "returned"] or order.is_cancelled):
            for _, field in self.fields.items():
                field.disabled = True

        # Supplier fields read-only once order is not draft
        if order and order.order_status != "draft":
            if 'supplier' in self.fields:
                self.fields['supplier'].disabled = True
            if 'supplier_address' in self.fields:
                self.fields['supplier_address'].disabled = True
            if 'pickup_warehouse' in self.fields:
                self.fields['pickup_warehouse'].disabled = True

        # Enable direct-to-warehouse only for draft/confirmed in UI
        if 'is_direct_to_warehouse' in self.fields and order:
            if order.order_status not in ['draft', 'confirmed']:
                self.fields['is_direct_to_warehouse'].disabled = True

    def clean(self):
        cleaned = super().clean()
        new_flag = cleaned.get('is_direct_to_warehouse')
        old_flag = bool(getattr(self.instance, 'is_direct_to_warehouse', False))
        # Only enforce when transitioning from False -> True
        if new_flag and not old_flag:
            status = (self.instance.order_status or cleaned.get('order_status'))
            errors = []
            if status not in ['draft', 'confirmed']:
                errors.append('Direct to warehouse can only be set when order is Draft or Confirmed.')
            if not cleaned.get('pickup_warehouse'):
                errors.append('Pickup warehouse is required when marking as received directly to warehouse.')
            if not cleaned.get('received_by_driver'):
                errors.append('Driver is required when marking as received directly to warehouse.')
            if errors:
                raise forms.ValidationError(' '.join(errors))

        # Secondary currency validation: if either provided, both required, and currency must differ
        sec_price = cleaned.get('order_price_secondary')
        sec_curr = cleaned.get('currency_secondary')
        if sec_price != 0 or sec_curr is not None:
            # If any is present (even 0), require both
            if sec_price in [None, 0] or sec_curr is None:
                raise forms.ValidationError('Secondary currency and amount are both required when adding another currency.')
            base_curr = cleaned.get('currency') or getattr(self.instance, 'currency', None)
            if base_curr and sec_curr and base_curr == sec_curr:
                raise forms.ValidationError('Secondary currency must be different from the primary currency.')
        return cleaned
    

OrderFormFactory = modelform_factory(Order, form=OrderForm, exclude=[])

class OrderPackageForm(forms.ModelForm):
    class Meta:
        model = OrderPackages
        fields = [
            'description', 'package_type', 'package_requirment', 'delivery_fees',
        ]

    def __init__(self, *args, **kwargs):
        allowed_package_types = kwargs.pop('allowed_package_types', None)
        super().__init__(*args, **kwargs)

        if allowed_package_types:            
            self.fields['package_type'].queryset = allowed_package_types
        else:
            self.fields['package_type'].queryset = DeliveryPriceListItem.objects.none()



  
PackageFormSet = modelformset_factory(
    OrderPackages,
    form=OrderPackageForm,
    extra=0,
    can_delete=True
)

class PackageTypeForm(forms.ModelForm):
    class Meta:
        model = PackageType
        fields = ['name', 'size']


class PackageRequirementForm(forms.ModelForm):
    class Meta:
        model = PackageRequirments
        fields = ['name']


class AssignDriverForm(forms.Form):
    driver = forms.ModelChoiceField(
        queryset=Employee.objects.filter(employee_type='driver', active=True),
        label="Driver",
        widget=forms.Select(attrs={'class': 'form-select'})
    )



class OrderRequestForm(forms.ModelForm):
    class Meta:
        model = OrderRequest
        fields = ['supplier', 'driver', 'nb_orders', 'nb_packages', 'warehouse', 'status', 'created_at', 'created_by', 'total_amount', 'delivery_pricelist']
        widgets = {
            'supplier': SupplierSelectWidget(
                attrs={'data-placeholder': 'Search Supplier...', 'style': 'width: 100%'}
            ),
        }
        
    def __init__(self, *args, supplier=None, is_supplier=False, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['status'].disabled = True
        self.fields['created_at'].disabled = True
        self.fields['created_by'].disabled = True
        self.fields['driver'].queryset = Employee.objects.filter(employee_type='driver', active=True)
        self.fields['created_at'].required = False
        self.fields['created_by'].required = False
        self.fields['driver'].required = False
        self.fields['delivery_pricelist'].required = False
        
        if is_supplier:
            self.fields['supplier'].initial = supplier
            self.fields['warehouse'].initial = supplier.warehouse
            self.fields['delivery_pricelist'].initial = supplier.delivery_pricelist
            self.fields['supplier'].widget = forms.HiddenInput()  # Just in case
            self.fields['warehouse'].widget = forms.HiddenInput()
            self.fields['driver'].widget = forms.HiddenInput()
            self.fields['delivery_pricelist'].widget = forms.HiddenInput()


class DeliveryPriceListForm(forms.ModelForm):
    class Meta:
        model = DeliveryPriceList
        fields = ['name', 'default']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-control'})
        self.fields['default'].widget.attrs.update({'class': 'form-check-input'})


class DeliveryPriceListItemForm(forms.ModelForm):
    class Meta:
        model = DeliveryPriceListItem
        fields = ['package_type', 'fees', 'source_warehouse', 'destination_warehouse']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['package_type'].widget.attrs.update({'class': 'form-control'})
        self.fields['fees'].widget.attrs.update({'class': 'form-control', 'step': '0.01'})
        self.fields['source_warehouse'].queryset = Warehouse.objects.filter(active=True)
        self.fields['destination_warehouse'].queryset = Warehouse.objects.filter(active=True)
        self.fields['source_warehouse'].required = False
        self.fields['destination_warehouse'].required = False

# Create formset for delivery pricelist items
DeliveryPriceListItemFormSet = modelformset_factory(
    DeliveryPriceListItem,
    form=DeliveryPriceListItemForm,
    extra=0,
    can_delete=True
)
