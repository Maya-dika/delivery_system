from django.db import models
from django_countries.fields import CountryField

class Address(models.Model):
    country = CountryField()
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=100, blank=True)
    building = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.city}, {self.street}"
    