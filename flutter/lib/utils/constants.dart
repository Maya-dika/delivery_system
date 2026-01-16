class Constants {
  // static const String defaultApiBaseUrl = 'https://delivery.itlbservices.com';
  // For web, use 127.0.0.1 instead of localhost (UrlHelper will handle conversion)
  static const String defaultApiBaseUrl = 'http://127.0.0.1:7001';
  
  // Storage keys
  static const String tokenKey = 'auth_token';
  static const String usernameKey = 'username';
  static const String apiBaseUrlKey = 'api_base_url';
  
  // Default balance (can be replaced with API call later)
  static const double defaultBalance = 1000.0;
}

