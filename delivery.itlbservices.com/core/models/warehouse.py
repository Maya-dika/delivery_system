from django.db import models
from .address import Address
from .company import Company
from .accounts import Account

class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, null=True)
    warehouse_manager = models.ForeignKey("users.Employee", on_delete=models.SET_NULL, null=True, related_name="store_manager")
    active = models.BooleanField(default=True)
    accounts = models.ManyToManyField(Account, blank=True, related_name='warehouses')

    def __str__(self):
        return self.name


class RoutingRule(models.Model):
    from_warehouse = models.ForeignKey(Warehouse, related_name='routing_from', on_delete=models.CASCADE)
    to_warehouse = models.ForeignKey(Warehouse, related_name='routing_to', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.from_warehouse} → {self.to_warehouse}"

    def get_full_route(self):
        return [self.from_warehouse] + \
           [step.warehouse for step in self.steps.all()] + \
           [self.to_warehouse]

class RoutingStep(models.Model):
    rule = models.ForeignKey(RoutingRule, related_name='steps', on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.position}. {self.warehouse.name}"
