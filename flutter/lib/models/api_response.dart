import 'order.dart';
import 'order_request.dart';
import 'warehouse.dart';
import 'delivery_pricelist.dart';
import 'user.dart';
import 'employee.dart';

class OrdersApiResponse {
  final int draw;
  final int recordsTotal;
  final int recordsFiltered;
  final List<Order> data;

  OrdersApiResponse({
    required this.draw,
    required this.recordsTotal,
    required this.recordsFiltered,
    required this.data,
  });

  factory OrdersApiResponse.fromJson(Map<String, dynamic> json) {
    return OrdersApiResponse(
      draw: json['draw'] ?? 0,
      recordsTotal: json['recordsTotal'] ?? 0,
      recordsFiltered: json['recordsFiltered'] ?? 0,
      data: (json['data'] as List<dynamic>?)
              ?.map((item) => Order.fromJson(item as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

class LoginResponse {
  final String token;
  final User user;
  final Employee? employee;
  final String? employeeType;
  final int? supplierId;
  LoginResponse({
    required this.token,
    required this.user,
    this.employee,
    this.employeeType,
    this.supplierId,
  });

  factory LoginResponse.fromJson(Map<String, dynamic> json) {
    return LoginResponse(
      token: json['token'] ?? '',
      user: User.fromJson({
        ...json['user'] ?? {},
        'token': json['token'],
        'supplier_id': json['supplier_id'], // Include supplier_id in user data
      }),
      employee: json['employee'] != null
          ? Employee.fromJson(json['employee'] as Map<String, dynamic>)
          : null,
      employeeType: json['employee_type'] ?? json['employee']?['employee_type'],
      supplierId: json['supplier_id'],
    );
  }
}

// Keep TokenResponse for backward compatibility
class TokenResponse {
  final String token;

  TokenResponse({required this.token});

  factory TokenResponse.fromJson(Map<String, dynamic> json) {
    return TokenResponse(token: json['token'] ?? '');
  }
}

class OrderRequestApiResponse {
  final int draw;
  final int recordsTotal;
  final int recordsFiltered;
  final List<OrderRequest> data;

  OrderRequestApiResponse({
    required this.draw,
    required this.recordsTotal,
    required this.recordsFiltered,
    required this.data,
  });

  factory OrderRequestApiResponse.fromJson(Map<String, dynamic> json) {
    return OrderRequestApiResponse(
      draw: json['draw'] ?? 0,
      recordsTotal: json['recordsTotal'] ?? 0,
      recordsFiltered: json['recordsFiltered'] ?? 0,
      data: (json['data'] as List<dynamic>?)
              ?.map((item) => OrderRequest.fromJson(item as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

class WarehouseApiResponse {
  final int draw;
  final int recordsTotal;
  final int recordsFiltered;
  final List<Warehouse> data;

  WarehouseApiResponse({
    required this.draw,
    required this.recordsTotal,
    required this.recordsFiltered,
    required this.data,
  });

  factory WarehouseApiResponse.fromJson(Map<String, dynamic> json) {
    return WarehouseApiResponse(
      draw: json['draw'] ?? 0,
      recordsTotal: json['recordsTotal'] ?? 0,
      recordsFiltered: json['recordsFiltered'] ?? 0,
      data: (json['data'] as List<dynamic>?)
              ?.map((item) => Warehouse.fromJson(item as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

class DeliveryPriceListApiResponse {
  final int draw;
  final int recordsTotal;
  final int recordsFiltered;
  final List<DeliveryPriceList> data;

  DeliveryPriceListApiResponse({
    required this.draw,
    required this.recordsTotal,
    required this.recordsFiltered,
    required this.data,
  });

  factory DeliveryPriceListApiResponse.fromJson(Map<String, dynamic> json) {
    return DeliveryPriceListApiResponse(
      draw: json['draw'] ?? 0,
      recordsTotal: json['recordsTotal'] ?? 0,
      recordsFiltered: json['recordsFiltered'] ?? 0,
      data: (json['data'] as List<dynamic>?)
              ?.map((item) => DeliveryPriceList.fromJson(item as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

class SupplierDefaultsResponse {
  final int? pricelistId;
  final int? warehouseId;
  final String? warehouseName;

  SupplierDefaultsResponse({
    this.pricelistId,
    this.warehouseId,
    this.warehouseName,
  });

  factory SupplierDefaultsResponse.fromJson(Map<String, dynamic> json) {
    return SupplierDefaultsResponse(
      pricelistId: json['pricelist_id'],
      warehouseId: json['warehouse_id'],
      warehouseName: json['warehouse_name'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'pricelist_id': pricelistId,
      'warehouse_id': warehouseId,
      'warehouse_name': warehouseName,
    };
  }
}

class ApiError {
  final String message;
  final int? statusCode;

  ApiError({required this.message, this.statusCode});

  factory ApiError.fromJson(Map<String, dynamic> json) {
    return ApiError(
      message: json['detail'] ?? json['error'] ?? 'An error occurred',
      statusCode: json['status_code'],
    );
  }
}

