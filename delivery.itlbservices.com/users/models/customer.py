from django.db import models

from core.models import Address, Company, Account
from . import User

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=50)
    addresses = models.ManyToManyField(Address, related_name='customers')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    active = models.BooleanField(db_comment="determines if customer is active with this company", default=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    accounts = models.ManyToManyField(Account, blank=True, related_name='customers')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="customer_created_by")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="customer_updated_by")
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True)
    
    def __str__(self):
        return self.name
