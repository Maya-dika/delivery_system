from django.db import models
from . import Company
from .warehouse import Warehouse


class StockLocationTypes(models.TextChoices):
    customer = "customer", "Customer"
    supplier = "supplier", "Supplier"
    warehouse = "warehouse", "Warehouse"


class StockLocation(models.Model):    
    name = models.CharField(max_length=100)
    location_type = models.CharField(choices=StockLocationTypes.choices, max_length=20)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    
    def __str__(self):
         return self.name
