from django.db import models

from core.models import Warehouse, Address, Company, Account
from . import User


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=50)
    domain_description = models.CharField(max_length=200, null=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True)
    address = models.OneToOneField(Address, related_name='address', on_delete=models.SET_NULL, null=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    accounts = models.ManyToManyField(Account, blank=True, related_name='suppliers')
    active = models.BooleanField(db_comment="determines if supplier is active with this company", default=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_by")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="updated_by")
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True)
    delivery_pricelist = models.ForeignKey("orders.DeliveryPriceList", on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name


