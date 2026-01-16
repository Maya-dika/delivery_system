from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField, Q
from django.db.models.functions import TruncDate

from orders.models import Order

import datetime
from datetime import timedelta

def get_orders_in_warehouse():
    return None #TODO: implement
    # return (
    #     Order.objects.filter(order_status__in=["in_warehouse", "in_transit"])
    #     .values("delivery_warehouse__name")
    #     .annotate(total=Count("id"))
    #     .order_by("delivery_warehouse__name")
    # )

def get_delivery_success_rate():
    total = Order.objects.filter(is_cancelled=False).count()
    delivered = Order.objects.filter(is_cancelled=False, order_status="delivered").count()
    return round((delivered / total) * 100, 2) if total else 0


def get_orders_by_status():
    return (
        Order.objects.values("order_status")
        .annotate(total=Count("id"))
        .order_by("order_status")
    )

def get_average_delivery_time():
    qs = Order.objects.filter(
        is_cancelled=False,
        order_status="delivered",
        effective_date__isnull=False,
    ).annotate(
        duration=ExpressionWrapper(
            F("effective_date") - F("order_date"),
            output_field=DurationField()
        )
    )
    return qs.aggregate(avg_time=Avg("duration"))["avg_time"]


def new_orders_last_n_days(days: int = 3):
    cutoff = datetime.datetime.now() - timedelta(days=days)
    return Order.objects.filter(
        Q(is_cancelled=False),
        order_status__in=["draft", "confirmed", "pending_pickup"],
        order_date__gte=cutoff,
    ).count()


def status_snapshot():
    delivered = Order.objects.filter(is_cancelled=False, order_status="delivered").count()
    cancelled = Order.objects.filter(Q(order_status="cancelled") | Q(is_cancelled=True)).count()
    returned = Order.objects.filter(order_status="returned").count()
    in_progress = (
        Order.objects.filter(is_cancelled=False)
        .exclude(order_status__in=["draft", "delivered", "returned"])
        .count()
    )
    return {
        "delivered": delivered,
        "in_progress": in_progress,
        "cancelled": cancelled,
        "returned": returned,
    }

def awaiting_pickup():
    return Order.objects.filter(is_cancelled=False, order_status="pending_pickup").count()


def delivered_this_week_by_day():
    """
    Returns a list of dicts: [{'day': 'YYYY-MM-DD', 'total': N}, ...]
    Week = Monday..Sunday of the current ISO week.
    """
    today = datetime.datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)

    qs = (
        Order.objects.filter(
            is_cancelled=False,
            order_status="delivered",
            effective_date__date__gte=start_of_week,
            effective_date__date__lte=end_of_week,
        )
        .annotate(day=TruncDate("effective_date"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )
    # Normalize to include empty days
    day_map = {row["day"].isoformat(): row["total"] for row in qs}
    labels = [(start_of_week + timedelta(days=i)).isoformat() for i in range(7)]
    return [{"day": d, "total": day_map.get(d, 0)} for d in labels]

def delayed_orders_count():
    return Order.objects.filter(
        is_cancelled=False,
        estimated_delivery_date__isnull=False,
        estimated_delivery_date__lt=datetime.datetime.now(),
    ).exclude(order_status__in=["delivered", "cancelled", "returned"]).count()


def delayed_orders_sample(limit=5):
    qs = (
        Order.objects.filter(
            is_cancelled=False,
            estimated_delivery_date__isnull=False,
            estimated_delivery_date__lt=datetime.datetime.now(),
        )
        .exclude(order_status__in=["delivered", "cancelled", "returned"])
        .order_by("estimated_delivery_date")[:limit]
        .values("id", "tracking_number", "order_status", "estimated_delivery_date")
    )

    # Format the date as YYYY-MM-DD
    formatted_qs = []
    for o in qs:
        formatted_qs.append({
            **o,
            "estimated_delivery_date": o["estimated_delivery_date"].strftime("%Y-%m-%d") if o["estimated_delivery_date"] else None
        })

    return formatted_qs

def on_time_delivery_rate():
    qs = Order.objects.filter(
        is_cancelled=False,
        order_status="delivered",
        estimated_delivery_date__isnull=False,
        effective_date__isnull=False,
    )
    total = qs.count()
    if not total:
        return 0
    on_time = qs.filter(effective_date__lte=F("estimated_delivery_date")).count()
    return round((on_time / total) * 100, 2)


def average_delay_late_orders():
    qs = Order.objects.filter(
        is_cancelled=False,
        order_status="delivered",
        estimated_delivery_date__isnull=False,
        effective_date__isnull=False,
        effective_date__gt=F("estimated_delivery_date"),
    ).annotate(
        delay=ExpressionWrapper(
            F("effective_date") - F("estimated_delivery_date"),
            output_field=DurationField()
        )
    )
    return qs.aggregate(avg_delay=Avg("delay"))["avg_delay"]