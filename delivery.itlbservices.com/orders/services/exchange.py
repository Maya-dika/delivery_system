from django.db import transaction
from django.core.exceptions import ValidationError

from orders import models
from orders.models import order as models_order
from . import services

from dataclasses import dataclass
from typing import Iterable, Optional
import datetime

def create_reverse_trackings(order: models.Order, *, actor) -> bool:
    """
    Reuse your existing 'return' reverse-tracking builder for the ORIGINAL order.
    Should mirror the route back: customer -> ... -> supplier.
    """
    try:
        done_trackings = order.order_tracking.filter(tracking_status=models_order.OrderTrackingStatuses.done)
        
        if done_trackings.exists():
            # Reverse only the compeleted trackings
            for tracking in done_trackings.order_by('-effective_date'):
                reverse_tracking = models.OrderTracking.objects.create(
                    order=tracking.order,
                    sender=tracking.receiver,
                    receiver=tracking.sender,
                    sender_address=tracking.receiver_address,
                    receiver_address=tracking.sender_address,
                    driver=tracking.driver,
                    tracking_status=models_order.OrderTrackingStatuses.draft,
                    created_by=actor,
                    created_at=datetime.datetime.now()
                )
                reverse_tracking.save()
        
        return True
    except Exception as e:
        return False



@dataclass
class ExchangeResult:
    original: models.Order
    replacement: models.Order

def _clone_packages(src: models.Order, dest: models.Order) -> None:
    src_pkgs: Iterable[models.OrderPackages] = src.order_packages.all().order_by("id")
    clones = []
    for p in src_pkgs:
        clones.append(models.OrderPackages(
            order=dest,
            description=p.description,
            package_type=p.package_type,
            package_requirment=p.package_requirment,
            delivery_fees=p.delivery_fees,
        ))
    models.OrderPackages.objects.bulk_create(clones)

def _copy_fees(src: models.Order, dest: models.Order) -> None:
    dest.total_delivery_fees = src.total_delivery_fees
    dest.total_amount = src.total_delivery_fees
    dest.order_price = 0 # assuming replacement has no product cost

@transaction.atomic
def create_exchange_order(*, original_id: int, actor, reason: Optional[str] = "") -> ExchangeResult:
    # Lock original row to prevent race (double exchanges)
    original = models.Order.objects.select_for_update().select_related("supplier", "customer").get(pk=original_id)

    # # Validation rules (tweak to your workflow)
    # if original.is_replacement:
    #     raise ValidationError("Exchanges can only be created from original orders, not replacements.")
    # if original.is_exchanged or original.exchange_children.exists():
    #     raise ValidationError("This order already has an exchange.")
    # if original.is_cancelled:
    #     raise ValidationError("Cannot exchange an already cancelled order.")

    # 1) Flag original & reverse trackings
    original.is_exchanged = True
    original.exchange_reason = (reason or "")[:255]
    original.exchanged_at = datetime.datetime.now()
    original.save(update_fields=["is_exchanged", "exchange_reason", "exchanged_at"])

    # success = create_reverse_trackings(original, actor=actor)
    # if not success:
    #     return None

    # 2) Create replacement order (linked to original)
    replacement = models.Order.objects.create(
        supplier=original.supplier,
        customer=original.customer,
        supplier_address=original.supplier_address,
        customer_address=original.customer_address,
        pickup_warehouse=original.pickup_warehouse,
        delivery_warehouse=original.delivery_warehouse,
        order_status=models_order.OrderStatuses.draft,
        order_date=datetime.datetime.now(),
        created_by=actor,
        currency=original.currency,
        company=original.company,
        delivery_pricelist=original.delivery_pricelist,
        is_exchanged=False,
        exchange_parent=original,
    )
    
    replacement.planned_route = replacement.compute_planned_route()

    # 3) Copy packages & fees
    _clone_packages(original, replacement)
    _copy_fees(original, replacement)
    replacement.save()
    
    # 4) Confirm & route the replacement (these create trackings for the new order all over again from the supplier to the customer)
    # services.confirm_order(replacement, driver=None, user=actor)
    # services.generate_order_routes(replacement, user=actor)

    return ExchangeResult(original=original, replacement=replacement)
