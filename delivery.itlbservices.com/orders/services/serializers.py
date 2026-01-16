from rest_framework import serializers
from orders.models import OrderTracking


class OutForDeliverySerializer(serializers.Serializer):
    order_ids = serializers.ListField(
        child=serializers.IntegerField(), required=True
    )
    driver_id = serializers.IntegerField(required=True, allow_null=True)

class OrderConfirmationSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
