from django.db import models

from users.models import User, Supplier, Employee
from core.models import Warehouse
from .packages import DeliveryPriceList

class OrderRequestStatuses(models.TextChoices):
    requested = "requested", "Requested"
    confirmed = "confirmed", "Confirmed"
    cancelled = "cancelled", "Cancelled"
    picked_up = "picked_up", "Picked Up"
    
class OrderRequest(models.Model):
    reference = models.CharField(max_length=50)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    driver = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    nb_orders = models.IntegerField()
    nb_packages = models.IntegerField()
    total_amount = models.FloatField(default=0)
    status = models.CharField(choices=OrderRequestStatuses.choices, max_length=20, default=OrderRequestStatuses.requested)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="request_created_by")
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="request_cancelled_by")
    created_at = models.DateTimeField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True)
    delivery_pricelist = models.ForeignKey(DeliveryPriceList, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return self.reference