from django.contrib import admin
from .models import Order
from .models import PackageRequirments, PackageType, DeliveryPriceList, DeliveryPriceListItem


admin.site.register(Order)
admin.site.register(PackageRequirments)
admin.site.register(PackageType)
admin.site.register(DeliveryPriceList)
admin.site.register(DeliveryPriceListItem)
