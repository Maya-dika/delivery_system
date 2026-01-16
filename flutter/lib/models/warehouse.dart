class Warehouse {
  final int id;
  final String name;
  final String company;
  final String warehouseManager;
  final bool active;
  final String address;

  Warehouse({
    required this.id,
    required this.name,
    required this.company,
    required this.warehouseManager,
    required this.active,
    required this.address,
  });

  factory Warehouse.fromJson(Map<String, dynamic> json) {
    return Warehouse(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      company: json['company'] ?? '',
      warehouseManager: json['warehouse_manager'] ?? '',
      active: json['active'] ?? true,
      address: json['address'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'company': company,
      'warehouse_manager': warehouseManager,
      'active': active,
      'address': address,
    };
  }
}
