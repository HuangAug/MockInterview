/// API configuration constants loaded from environment.
class ApiConstants {
  ApiConstants._();

  /// Base URL for the backend API.
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1',
  );

  /// Connection timeout in seconds.
  static const Duration connectTimeout = Duration(seconds: 10);

  /// Receive timeout in seconds — accounts for backend OpenAI calls
  /// (60s timeout + 2 retries = worst case ~180s).
  static const Duration receiveTimeout = Duration(seconds: 180);
}
