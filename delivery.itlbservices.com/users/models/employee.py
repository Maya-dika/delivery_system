from django.db import models
from core.models import Warehouse, Address, Company, Account
from . import User

class EmployeeTypes(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    WAREHOUSE_MANAGER = 'warehouse_manager', 'Warehouse Manager'
    DRIVER = 'driver', 'Driver'
    INTERNAL_USER = 'internal_user', 'Internal User'

class Employee(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(null=True)
    phone_number = models.CharField(max_length=20)
    employee_type = models.CharField(max_length=20, choices=EmployeeTypes.choices)
    commission = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0, help_text="Commission in USD (drivers only)")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    manager = models.ForeignKey("self", on_delete=models.SET_NULL, null=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="employee_user")
    active = models.BooleanField(db_comment="If employee is still working for the company or not", default=1)
    accounts = models.ManyToManyField(Account, blank=True, related_name='employee')

    def __str__(self):
        return self.name

class WarehouseEmployees(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField(db_comment="Start date for employment under this warehouse", null=False)
    end_date = models.DateField(db_column="End Date for working under this warehouse", null=True)
    active = models.BooleanField(db_comment="Bool field determines of the employee is still working under this warehouse", default=1)
    notes = models.TextField()
