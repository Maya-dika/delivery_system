class Order {
  final int id;
  final String trackingNumber;
  final String supplier;
  final String supplierAddress;
  final String customer;
  final String customerAddress;
  final String orderStatus;
  final String orderDate;
  final String orderRequest;
  final String orderPrice;
  final String totalDeliveryFees;
  final bool isCancelled;
  final bool isExchanged;

  Order({
    required this.id,
    required this.trackingNumber,
    required this.supplier,
    required this.supplierAddress,
    required this.customer,
    required this.customerAddress,
    required this.orderStatus,
    required this.orderDate,
    required this.orderRequest,
    required this.orderPrice,
    required this.totalDeliveryFees,
    required this.isCancelled,
    required this.isExchanged,
  });

  factory Order.fromJson(Map<String, dynamic> json) {
    return Order(
      id: json['id'] ?? 0,
      trackingNumber: json['tracking_number'] ?? '',
      supplier: json['supplier'] ?? '',
      supplierAddress: json['supplier_address'] ?? '',
      customer: json['customer'] ?? '',
      customerAddress: json['customer_address'] ?? '',
      orderStatus: json['order_status'] ?? '',
      orderDate: json['order_date'] ?? '',
      orderRequest: json['order_request'] ?? '',
      orderPrice: json['order_price'] ?? '',
      totalDeliveryFees: json['total_delivery_fees'] ?? '',
      isCancelled: json['is_cancelled'] ?? false,
      isExchanged: json['is_exchanged'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'tracking_number': trackingNumber,
      'supplier': supplier,
      'supplier_address': supplierAddress,
      'customer': customer,
      'customer_address': customerAddress,
      'order_status': orderStatus,
      'order_date': orderDate,
      'order_request': orderRequest,
      'order_price': orderPrice,
      'total_delivery_fees': totalDeliveryFees,
      'is_cancelled': isCancelled,
      'is_exchanged': isExchanged,
    };
  }
}

