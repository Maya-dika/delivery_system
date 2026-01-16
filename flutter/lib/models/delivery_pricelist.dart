class DeliveryPriceList {
  final int id;
  final String name;
  final bool defaultList;
  final int itemsCount;

  DeliveryPriceList({
    required this.id,
    required this.name,
    required this.defaultList,
    required this.itemsCount,
  });

  factory DeliveryPriceList.fromJson(Map<String, dynamic> json) {
    return DeliveryPriceList(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      defaultList: json['default'] ?? false,
      itemsCount: json['items_count'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'default': defaultList,
      'items_count': itemsCount,
    };
  }
}
