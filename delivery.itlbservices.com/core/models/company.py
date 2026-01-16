from django.db import models
from .address import Address
from .currency import Currency

class Company(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, null=True)
    parent_company = models.ForeignKey("self", on_delete=models.SET_NULL, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True)
    active = models.BooleanField(default=True)
    
    # Sequencing configuration
    order_request_prefix = models.CharField(max_length=10, default='RQ')
    order_request_seq_length = models.PositiveIntegerField(default=5, help_text="Digits for Order Request sequence (excluding prefix)")
    order_prefix = models.CharField(max_length=10, blank=True, default='', help_text="Optional static prefix for Orders (will be prepended before country code)")
    order_seq_length = models.PositiveIntegerField(default=6, help_text="Digits for Order sequence (excluding prefix)")

    def __str__(self):
        return self.name
