import 'package:flutter/foundation.dart';

class UrlHelper {
  /// Converts localhost to 127.0.0.1 for Flutter web compatibility
  /// Browsers block localhost connections, but 127.0.0.1 works
  static String normalizeUrl(String url) {
    if (kIsWeb) {
      // On web, replace localhost with 127.0.0.1
      return url.replaceAll('http://localhost', 'http://127.0.0.1')
                 .replaceAll('https://localhost', 'https://127.0.0.1');
    }
    // On mobile/desktop, localhost works fine
    return url;
  }
}


