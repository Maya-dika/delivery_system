import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/api_response.dart';
import '../models/order.dart';
import '../models/order_request.dart';
import '../models/warehouse.dart';
import '../models/delivery_pricelist.dart';
import '../utils/constants.dart';
import '../utils/url_helper.dart';
import 'storage_service.dart';

class ApiService {
  Future<String> get baseUrl async {
    final url = await StorageService.getApiBaseUrl();
    return UrlHelper.normalizeUrl(url);
  }

  Future<Map<String, String>> _getHeaders({bool includeAuth = true}) async {
    final headers = <String, String>{
      'Content-Type': 'application/json',
    };

    if (includeAuth) {
      final token = await StorageService.getToken();
      if (token != null) {
        headers['Authorization'] = 'Token $token';
      }
    }

    return headers;
  }

  Future<LoginResponse> login(String username, String password) async {
    try {
      final apiUrl = await baseUrl;
      final url = Uri.parse('$apiUrl/users/api/login/');
      final response = await http.post(
        url,
        headers: await _getHeaders(includeAuth: false),
        body: jsonEncode({
          'username': username,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print(data);
        return LoginResponse.fromJson(data);
      } else {
        print(response.body);
        final error = jsonDecode(response.body);
        print(error);
        throw ApiError.fromJson(error);
      }
    } catch (e) {
      if (e is ApiError) {
        print(e);
        rethrow;
      }
      print(e);
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  Future<Map<String, dynamic>> getDriverStatement({
    String? from,
    String? to,
  }) async {
    try {
      final apiUrl = await baseUrl;
      final queryParams = <String, String>{};
      if (from != null) queryParams['from'] = from;
      if (to != null) queryParams['to'] = to;

      final uri = Uri.parse('$apiUrl/orders/api/reports/driver-statement/')
          .replace(queryParameters: queryParams);

      final response = await http.get(uri, headers: await _getHeaders());
      print(response.body); 
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        print(response.body);
        final error = jsonDecode(response.body);
        print(error);
        throw ApiError.fromJson(error);
      }
    } catch (e) {
      print(e);
      if (e is ApiError) rethrow;
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  Future<Map<String, dynamic>> getDriverPerformance({
    String? from,
    String? to,
  }) async {
    try {
      final apiUrl = await baseUrl;
      final queryParams = <String, String>{};
      if (from != null) queryParams['from'] = from;
      if (to != null) queryParams['to'] = to;

      final uri = Uri.parse('$apiUrl/orders/api/reports/drivers-performance/')
          .replace(queryParameters: queryParams);

      final response = await http.get(uri, headers: await _getHeaders());

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw ApiError.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      if (e is ApiError) rethrow;
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  Future<OrdersApiResponse> getOrders({
    int start = 0,
    int length = 20,
    String? status,
    String? search,
  }) async {
    try {
      final queryParams = <String, String>{
        'start': start.toString(),
        'length': length.toString(),
        'draw': '1',
      };

      if (status != null && status.isNotEmpty) {
        queryParams['status'] = status;
      }

      if (search != null && search.isNotEmpty) {
        queryParams['search[value]'] = search;
      }

      final apiUrl = await baseUrl;
      final uri = Uri.parse('$apiUrl/orders/api/orders/').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(
        uri,
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return OrdersApiResponse.fromJson(data);
      } else {
        final error = jsonDecode(response.body);
        throw ApiError.fromJson(error);
      }
    } catch (e) {
      if (e is ApiError) {
        rethrow;
      }
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  Future<OrderRequestApiResponse> getOrderRequests({
    int start = 0,
    int length = 20,
    String? search,
  }) async {
    try {
      final queryParams = <String, String>{
        'start': start.toString(),
        'length': length.toString(),
        'draw': '1',
      };

      if (search != null && search.isNotEmpty) {
        queryParams['search[value]'] = search;
      }

      final apiUrl = await baseUrl;
      final uri = Uri.parse('$apiUrl/orders/api/order-requests/').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(
        uri,
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return OrderRequestApiResponse.fromJson(data);
      } else {
        final error = jsonDecode(response.body);
        throw ApiError.fromJson(error);
      }
    } catch (e) {
      if (e is ApiError) {
        rethrow;
      }
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  Future<Map<String, dynamic>> confirmOrder(int orderId) async {
    try {
      final apiUrl = await baseUrl;
      final url = Uri.parse('$apiUrl/orders/$orderId/confirm/');
      final response = await http.post(url, headers: await _getHeaders());

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw ApiError.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      if (e is ApiError) rethrow;
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  Future<Map<String, dynamic>> confirmOrdersBulk(List<int> orderIds) async {
    try {
      final apiUrl = await baseUrl;
      final url = Uri.parse('$apiUrl/orders/confirm-orders/');
      final response = await http.post(
        url,
        headers: await _getHeaders(),
        body: jsonEncode({'order_ids': orderIds}),
      );
      print(response.body);
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        print(response.body);
        final error = jsonDecode(response.body);
        print(error);
        throw ApiError.fromJson(error);
      }
    } catch (e) {
      if (e is ApiError) rethrow;
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  Future<Map<String, dynamic>> markArrivedToWarehouse(List<int> orderIds) async {
    try {
      final apiUrl = await baseUrl;
      final url = Uri.parse('$apiUrl/orders/arrived-to-warehouse/');
      final response = await http.post(
        url,
        headers: await _getHeaders(),
        body: jsonEncode({'order_ids': orderIds}),
      );
      print(response.body);
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        print(response.body);
        final error = jsonDecode(response.body);
        print(error);
        throw ApiError.fromJson(error);
      }
    } catch (e) {
      if (e is ApiError) rethrow;
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  Future<Map<String, dynamic>> confirmPickup(int orderId) async {
    try {
      final apiUrl = await baseUrl;
      final url = Uri.parse('$apiUrl/orders/confirm-pickup/driver/');
      final response = await http.post(
        url,
        headers: await _getHeaders(),
        body: jsonEncode({'order_id': orderId}),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw ApiError.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      if (e is ApiError) rethrow;
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  Future<Map<String, dynamic>> confirmPickupDriver(int orderId) async {
    try {
      final apiUrl = await baseUrl;
      final url = Uri.parse('$apiUrl/orders/confirm-pickup/driver/');
      final response = await http.post(
        url,
        headers: await _getHeaders(),
        body: jsonEncode({'order_id': orderId}),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw ApiError.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      if (e is ApiError) rethrow;
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  Future<Map<String, dynamic>> confirmDeliveryDriver(int orderId) async {
    try {
      final apiUrl = await baseUrl;
      final url = Uri.parse('$apiUrl/orders/confirm-delivery/driver/');
      final response = await http.post(
        url,
        headers: await _getHeaders(),
        body: jsonEncode({'order_id': orderId}),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw ApiError.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      if (e is ApiError) rethrow;
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  Future<Map<String, dynamic>> markAsDelivered(List<int> orderIds, {String? verificationCode}) async {
    try {
      final apiUrl = await baseUrl;
      final url = Uri.parse('$apiUrl/orders/order-delivered/');
      final body = <String, dynamic>{'order_ids': orderIds};
      if (verificationCode != null && verificationCode.isNotEmpty) {
        body['verification_code'] = verificationCode;
      }
      
      final response = await http.post(
        url,
        headers: await _getHeaders(),
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw ApiError.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      if (e is ApiError) rethrow;
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  Future<Map<String, dynamic>> markReturnedToSupplier(int orderId) async {
    try {
      final apiUrl = await baseUrl;
      final url = Uri.parse('$apiUrl/orders/mark-returned/$orderId/');
      final response = await http.post(
        url,
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw ApiError.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      if (e is ApiError) rethrow;
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  /// Get order by tracking number (barcode)
  Future<Order?> getOrderByTrackingNumber(String trackingNumber) async {
    try {
      final response = await getOrders(
        start: 0,
        length: 1,
        search: trackingNumber,
      );
      
      if (response.data.isNotEmpty) {
        // Find exact match
        final order = response.data.firstWhere(
          (o) => o.trackingNumber.toLowerCase() == trackingNumber.toLowerCase(),
          orElse: () => response.data.first,
        );
        return order;
      }
      return null;
    } catch (e) {
      throw ApiError(message: 'Error fetching order: ${e.toString()}');
    }
  }

  /// Get warehouses list
  Future<WarehouseApiResponse> getWarehouses({
    int start = 0,
    int length = 100,
    String? search,
  }) async {
    try {
      final queryParams = <String, String>{
        'start': start.toString(),
        'length': length.toString(),
        'draw': '1',
        'active': '1', // Only active warehouses
      };

      if (search != null && search.isNotEmpty) {
        queryParams['search[value]'] = search;
      }

      final apiUrl = await baseUrl;
      final uri = Uri.parse('$apiUrl/api/warehouses/').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(
        uri,
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return WarehouseApiResponse.fromJson(data);
      } else {
        final error = jsonDecode(response.body);
        throw ApiError.fromJson(error);
      }
    } catch (e) {
      if (e is ApiError) {
        rethrow;
      }
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  /// Get delivery price lists
  Future<DeliveryPriceListApiResponse> getDeliveryPriceLists({
    int start = 0,
    int length = 100,
    String? search,
  }) async {
    try {
      final queryParams = <String, String>{
        'start': start.toString(),
        'length': length.toString(),
        'draw': '1',
      };

      if (search != null && search.isNotEmpty) {
        queryParams['search[value]'] = search;
      }

      final apiUrl = await baseUrl;
      final uri = Uri.parse('$apiUrl/orders/api/delivery-pricelists/').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(
        uri,
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return DeliveryPriceListApiResponse.fromJson(data);
      } else {
        final error = jsonDecode(response.body);
        throw ApiError.fromJson(error);
      }
    } catch (e) {
      if (e is ApiError) {
        rethrow;
      }
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  /// Get supplier defaults (warehouse and pricelist)
  /// Note: supplierId is optional - if not provided, backend should get it from logged-in user
  /// For now, we'll call without supplier_id and backend should handle it
  Future<SupplierDefaultsResponse> getSupplierDefaults({int? supplierId}) async {
    try {
      final apiUrl = await baseUrl;
      final queryParams = <String, String>{};
      if (supplierId != null) {
        queryParams['supplier_id'] = supplierId.toString();
      }
      // If supplier_id is not provided, backend should get it from logged-in user
      // This may require backend modification to support this case
      
      final uri = Uri.parse('$apiUrl/orders/api/get-supplier-pricelist/').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(
        uri,
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return SupplierDefaultsResponse.fromJson(data);
      } else {
        final error = jsonDecode(response.body);
        throw ApiError.fromJson(error);
      }
    } catch (e) {
      if (e is ApiError) {
        rethrow;
      }
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }

  /// Create order request
  Future<Map<String, dynamic>> createOrderRequest({
    required int warehouse,
    required int supplier,
    required int nbOrders,
    required int nbPackages,
    required double totalAmount,
    int? deliveryPricelist,
  }) async {
    try {
      final apiUrl = await baseUrl;
      final url = Uri.parse('$apiUrl/orders/api/order-requests/save');
      
      final body = <String, dynamic>{
        'warehouse': warehouse,
        'supplier': supplier,
        'nb_orders': nbOrders,
        'nb_packages': nbPackages,
        'total_amount': totalAmount,
      };
      
      if (deliveryPricelist != null) {
        body['delivery_pricelist'] = deliveryPricelist;
      }

      final response = await http.post(
        url,
        headers: await _getHeaders(),
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw ApiError.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      if (e is ApiError) rethrow;
      throw ApiError(message: 'Network error: ${e.toString()}');
    }
  }
}

