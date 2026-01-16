from django.db import models, transaction


class NumberSequence(models.Model):
    """
    Generic numeric sequence per company and key (e.g., 'order', 'order_request').
    Keeps last_number monotonically increasing; deleted business objects won't affect it.
    """
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='sequences')
    key = models.CharField(max_length=50)
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('company', 'key')

    def __str__(self):
        return f"{self.company} - {self.key}: {self.last_number}"

    @classmethod
    def next(cls, company, key: str) -> int:
        with transaction.atomic():
            seq, _ = cls.objects.select_for_update().get_or_create(company=company, key=key, defaults={'last_number': 0})
            seq.last_number += 1
            seq.save(update_fields=['last_number'])
            return seq.last_number

