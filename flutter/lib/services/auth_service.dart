import '../models/api_response.dart';
import '../models/user.dart';
import 'api_service.dart';
import 'storage_service.dart';

class AuthService {
  final ApiService _apiService = ApiService();
  User? _currentUser;

  Future<LoginResponse> login(String username, String password) async {
    try {
      final loginResponse = await _apiService.login(username, password);
      
      // Save token and username
      await StorageService.saveToken(loginResponse.token);
      await StorageService.saveUsername(username);
      
      // Store current user (supplierId is already included in user from LoginResponse)
      _currentUser = loginResponse.user;

      return loginResponse;
    } catch (e) {
      rethrow;
    }
  }

  User? get currentUser => _currentUser;

  Future<void> loadUser() async {
    // Load user from storage if needed
    final username = await StorageService.getUsername();
    if (username != null) {
      // User info should be loaded from login response
      // For now, we'll rely on login to set currentUser
    }
  }

  Future<void> logout() async {
    await StorageService.clearAll();
  }

  Future<bool> isLoggedIn() async {
    final token = await StorageService.getToken();
    return token != null && token.isNotEmpty;
  }

  Future<String?> getToken() async {
    return await StorageService.getToken();
  }

  Future<String?> getUsername() async {
    return await StorageService.getUsername();
  }
}

