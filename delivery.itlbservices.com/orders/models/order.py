from django.db import models

from users.models import User, Customer, Supplier, Employee
from core.models import Company, Address, Currency, StockLocation, Warehouse
from .order_request import OrderRequest
from .packages import PackageRequirments, DeliveryPriceList, DeliveryPriceListItem

import logging

logger = logging.getLogger(__name__)


class OrderStatuses(models.TextChoices):
    draft = "draft", "Draft"
    confirmed = "confirmed", "Confirmed"
    pending_pickup = "pending_pickup", "Pending Pickup"
    pickup_confirmed = "pickup_confirmed", "Pickup Confirmed"
    in_warehouse = "in_warehouse", "In Warehouse"
    in_warehouse_transit = "in_warehouse_transit", "In Transit to Warehouse"
    out_for_delivery = "out_for_delivery", "Out For Delivery"
    delivered = "delivered", "Delivered"
    cancelled = "cancelled", "Cancelled"
    returned = "returned", "Returned"
    out_for_supplier = "out_for_supplier", "Out Returning to Supplier"


class Order(models.Model):
    order_reference = models.CharField(max_length=255)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    supplier_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='supplier_address')
    customer_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='customer_address')
    pickup_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True)
    delivery_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, related_name="delivery_warehouse")
    order_status = models.CharField(max_length=30, choices=OrderStatuses.choices, default=OrderStatuses.draft)
    order_date = models.DateTimeField(null=True, db_comment="Creation Date")
    effective_date = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_created_by")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_updated_by")
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    order_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_delivery_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tracking_number = models.CharField(max_length=255, null=True, default="DRAFT")
    order_request = models.ForeignKey(OrderRequest, on_delete=models.SET_NULL, null=True)
    delivery_pricelist = models.ForeignKey(DeliveryPriceList, on_delete=models.SET_NULL, null=True)
    driver_commission = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    is_cancelled = models.BooleanField(default=False)
    cancelled_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    estimated_delivery_date = models.DateTimeField(null=True, blank=True)
    planned_route = models.JSONField(default=list, blank=True)
    
    # exchange fields
    is_exchanged = models.BooleanField(default=False)
    exchange_reason = models.CharField(max_length=255, blank=True)
    exchanged_at = models.DateTimeField(null=True, blank=True)
    # replacement->original link (set only on the exchange order)
    exchange_parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="exchange_children"
    )
    
    is_direct_to_warehouse = models.BooleanField(default=False, help_text="Tick if the driver brought the order directly to the warehouse.")

    # new optional secondary currency
    order_price_secondary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency_secondary = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True, related_name="orders_secondary")
    
    @property
    def is_replacement(self) -> bool:
        return self.exchange_parent_id is not None
    
    def __str__(self):
        return f"Order #{self.tracking_number}"


    def compute_planned_route(self) -> list:
        """Compute planned route nodes as a list of dicts: {id, name, type}.
        Supplier -> via warehouses (routing rules) -> Customer.
        """
        from core import utils as core_utils
        nodes = []
        supplier_loc = StockLocation.objects.filter(location_type='supplier').first()
        customer_loc = StockLocation.objects.filter(location_type='customer').first()
        # Supplier
        if supplier_loc:
            nodes.append({'id': supplier_loc.id, 'name': supplier_loc.name, 'type': 'supplier'})
        
        # Warehouses routes
        if self.pickup_warehouse and not self.delivery_warehouse:
            wh = self.pickup_warehouse
            loc = StockLocation.objects.filter(location_type='warehouse', warehouse=wh).first()
            if loc:
                nodes.append({'id': loc.id, 'name': loc.name, 'type': 'warehouse'})
        
        elif self.delivery_warehouse and not self.pickup_warehouse:
            wh = self.delivery_warehouse
            loc = StockLocation.objects.filter(location_type='warehouse', warehouse=wh).first()
            if loc:
                nodes.append({'id': loc.id, 'name': loc.name, 'type': 'warehouse'})
        
        elif self.pickup_warehouse and self.delivery_warehouse:
            route = core_utils.get_expected_route(self.pickup_warehouse, self.delivery_warehouse)
            for wh in route:
                loc = StockLocation.objects.filter(location_type='warehouse', warehouse=wh).first()
                if loc:
                    nodes.append({'id': loc.id, 'name': loc.name, 'type': 'warehouse'})
        
        # Customer
        if customer_loc:
            nodes.append({'id': customer_loc.id, 'name': customer_loc.name, 'type': 'customer'})
        return nodes


    def update_planned_route(self):
        """Recompute and persist planned route if possible."""
        try:
            self.planned_route = self.compute_planned_route()
        except Exception as e:
            logger.error("Error computing planned route for Order %s: %s", self.id, e)


    def get_planned_route_text(self) -> str:
        nodes = self.planned_route or []
        if not nodes:
            return ""
        names = [n.get('name') for n in nodes if n.get('name')]
        return ' → '.join(names) if names else ''


    def get_next_destination_id(self):
        nd = self.get_next_destination()
        return nd.get('id') if nd else None
        
    def get_next_destination(self):
        planned_route = self.planned_route
        
        # PRIORITY 1: Check for in-progress trackings
        in_progress_tracking = self.get_in_progress_tracking()  # pending/draft status
        if in_progress_tracking:
            return {
                'id': in_progress_tracking.receiver.id,
                'name': in_progress_tracking.receiver.name,
                'type': in_progress_tracking.receiver.location_type,
                'status': 'in_progress'  # Flag to show "en route" status
            }
            
        if not in_progress_tracking and (self.is_cancelled or self.is_exchanged or self.order_status in [OrderStatuses.delivered, OrderStatuses.returned]):
            return None  # No next destination for cancelled or exchanged orders
        
        # PRIORITY 2: Check completed trackings
        last_completed_tracking = self.get_last_completed_tracking()
        
        # Case 1: No completed trackings yet
        if not last_completed_tracking:
            if planned_route and len(planned_route) > 1:
                return {**planned_route[1], 'status': 'planned'}  # First warehouse
            return None
        
        # Case 2: Last completed is customer
        if last_completed_tracking.receiver.location_type == 'customer':
            return None  # Journey complete
        
        # Case 3: Find current position in planned route
        current_position = self.find_location_in_route(last_completed_tracking.receiver.id)
        
        if current_position is not None:
            # Following planned route
            if current_position < len(planned_route) - 1:
                return {**planned_route[current_position + 1], 'status': 'planned'}
            return None  # At end of route
        
        # Case 4: Off-route - smart logic
        return self.calculate_smart_next_destination()

    def get_in_progress_tracking(self):
        return (OrderTracking.objects
                .filter(order=self, tracking_status__in=['draft', 'pending'])
                .order_by('created_at')
                .first())

    def get_last_completed_tracking(self):
        return (OrderTracking.objects
                .filter(order=self, tracking_status='done')
                .order_by('-effective_date', '-created_at')
                .first())

    def find_location_in_route(self, location_id):
        for idx, node in enumerate(self.planned_route):
            if node.get('id') == location_id:
                return idx
        return None

    def calculate_smart_next_destination(self):
        # Default: try to complete delivery
        if self.planned_route:
            # Go to customer (direct delivery)
            customer_location = self.find_customer_in_route()
            if customer_location:
                return customer_location
        
        # Fallback: go to delivery warehouse if set
        if self.delivery_warehouse:
            wh = StockLocation.objects.filter(location_type='warehouse', warehouse=self.delivery_warehouse).first()
            return {'id': wh.id, 'name': wh.name, 'type': 'warehouse'}
        
        return None  # Can't determine

    def find_customer_in_route(self):
        for node in self.planned_route:
            if node.get('type') == 'customer':
                return node
        return None 

class OrderPackages(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_packages')
    description = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    delivery_fees = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    package_type = models.ForeignKey(DeliveryPriceListItem, on_delete=models.SET_NULL, null=True)
    package_requirment = models.ForeignKey(PackageRequirments, on_delete=models.SET_NULL, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    barcode = models.CharField(max_length=255, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True)


class OrderTrackingStatuses(models.TextChoices):
    draft = "draft", "Draft"
    pending = "pending", "Pending"
    done = "done", "Done"
    cancelled = "cancelled", "Cancelled"
    
class OrderTracking(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_tracking')
    sender = models.ForeignKey(StockLocation, on_delete=models.SET_NULL, null=True, related_name='tracking_sender')
    receiver = models.ForeignKey(StockLocation, on_delete=models.SET_NULL, null=True, related_name='tracking_receiver')
    sender_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='sender_address')
    receiver_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='receiver_address')
    driver = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    tracking_status = models.CharField(max_length=30, choices=OrderTrackingStatuses.choices, default=OrderTrackingStatuses.draft)
    notes = models.CharField(max_length=255, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_tracking_created_by")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_tracking_updated_by")
    created_at = models.DateTimeField(null=True)
    effective_date = models.DateTimeField(null=True)
    confirmed_by_driver = models.BooleanField(default=False)
    confirmed_by_other = models.BooleanField(default=False)  # supplier/customer depending on context





