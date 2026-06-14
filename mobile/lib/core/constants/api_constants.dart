// API configuration constants loaded from environment.
//
// [baseUrl] reads from `flutter_dotenv` at runtime.
// Ensure `dotenv.load()` is called before accessing it (done in `main()`).
library;
import 'package:flutter_dotenv/flutter_dotenv.dart';

class ApiConstants {
  ApiConstants._();

  /// Base URL for the backend API.
  /// Falls back to Android emulator localhost when not set in `.env`.
  static String get baseUrl =>
      dotenv.env['API_BASE_URL'] ?? 'http://10.0.2.2:8000/api/v1';

  /// Connection timeout in seconds.
  static const Duration connectTimeout = Duration(seconds: 10);

  /// Receive timeout in seconds — accounts for backend OpenAI calls
  /// (60s timeout + 2 retries = worst case ~180s).
  static const Duration receiveTimeout = Duration(seconds: 180);
}
