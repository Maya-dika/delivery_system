from django.db import models
from .company import Company
from .currency import Currency

class Account(models.Model):
    name = models.CharField(max_length=255)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='accounts'
    )

    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children'
    )

    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='accounts'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def is_parent(self):
        return self.parent is None

    def has_children(self):
        return self.children.count() > 0

    def __str__(self):
        return self.name