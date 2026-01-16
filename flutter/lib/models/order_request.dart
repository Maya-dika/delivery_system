class OrderRequest {
  final int id;
  final String reference;
  final String supplier;
  final String warehouse;
  final String driver;
  final int nbOrders;
  final int nbPackages;
  final String createdAt;
  final String status;

  OrderRequest({
    required this.id,
    required this.reference,
    required this.supplier,
    required this.warehouse,
    required this.driver,
    required this.nbOrders,
    required this.nbPackages,
    required this.createdAt,
    required this.status,
  });

  factory OrderRequest.fromJson(Map<String, dynamic> json) {
    return OrderRequest(
      id: json['id'] ?? 0,
      reference: json['reference'] ?? '',
      supplier: json['supplier'] ?? '',
      warehouse: json['warehouse'] ?? '',
      driver: json['driver'] ?? '',
      nbOrders: json['nb_orders'] ?? 0,
      nbPackages: json['nb_packages'] ?? 0,
      createdAt: json['created_at'] ?? '',
      status: json['status'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'reference': reference,
      'supplier': supplier,
      'warehouse': warehouse,
      'driver': driver,
      'nb_orders': nbOrders,
      'nb_packages': nbPackages,
      'created_at': createdAt,
      'status': status,
    };
  }
}
