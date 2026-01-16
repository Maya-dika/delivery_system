from django.db import models

from core.models import Warehouse

class PackageRequirments(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class PackageType(models.Model):
    name = models.CharField(max_length=255)
    size = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name
    
class DeliveryPriceList(models.Model):
    name = models.CharField(max_length=255)
    default = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class DeliveryPriceListItem(models.Model):
    pricelist = models.ForeignKey(DeliveryPriceList, on_delete=models.CASCADE, related_name="pricelist_items")
    package_type = models.ForeignKey(PackageType, on_delete=models.CASCADE)
    source_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='source_items', null=True)
    destination_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='destination_items', null=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.package_type.name}: {self.fees}"