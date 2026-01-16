from django.db import models

class Currency(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    
    def __str__(self):
         return f"{self.name}, {self.symbol}"