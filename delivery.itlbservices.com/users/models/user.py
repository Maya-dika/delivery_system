from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models.company import Company

class UserTypes(models.TextChoices):
    SUPPLIER = 'supplier', 'Supplier'
    CUSTOMER = 'customer', 'Customer'
    EMPLOYEE = 'employee', 'Employee'

class User(AbstractUser):
    GENDER = [
        ('male', 'Male'),
        ('female', 'Female')
    ]

    full_name = models.CharField(max_length=100)
    email = models.EmailField(null=True)
    phone_number = models.CharField(max_length=20)
    gender = models.CharField(max_length=10, choices=GENDER)
    profile_image = models.ImageField(upload_to='user_images/', blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=UserTypes.choices)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    password = models.CharField(max_length=128, help_text="Keep it empty it you don't want to change the password.")
