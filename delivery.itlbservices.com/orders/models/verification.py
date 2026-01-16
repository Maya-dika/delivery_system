from django.db import models
from django.utils import timezone

import datetime


class OrderPhoneVerification(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("expired", "Expired"),
        ("failed", "Failed"),
    )

    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='phone_verifications')
    phone_number = models.CharField(max_length=32)
    code = models.CharField(max_length=12)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    attempts = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.datetime.now)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["order", "status"]),
        ]

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def mark_verified(self):
        self.status = 'verified'
        self.verified_at = datetime.datetime.now()
        self.save(update_fields=["status", "verified_at"])

