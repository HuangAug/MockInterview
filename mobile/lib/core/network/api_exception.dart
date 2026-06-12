import 'package:dio/dio.dart';

/// Exception parsed from the backend unified error response.
///
/// Backend error format:
/// ```json
/// {
///   "success": false,
///   "data": null,
///   "error": { "code": 40001, "message": "...", "details": [...] }
/// }
/// ```
class ApiException implements Exception {
  /// Business error code (e.g. 40001, 40102, 50201).
  final int code;

  /// Human-readable error message.
  final String message;

  /// Optional field-level error details.
  final List<Map<String, dynamic>>? details;

  const ApiException({
    required this.code,
    required this.message,
    this.details,
  });

  /// Parse an [ApiException] from a Dio [DioException].
  ///
  /// If the response contains the unified error structure, extract code/message.
  /// Otherwise, fall back to a generic 50001 error.
  factory ApiException.fromDioError(DioException error) {
    final response = error.response;

    if (response?.data is Map<String, dynamic>) {
      final data = response!.data as Map<String, dynamic>;
      final errorObj = data['error'] as Map<String, dynamic>?;

      if (errorObj != null) {
        return ApiException(
          code: errorObj['code'] as int? ?? 50001,
          message: errorObj['message'] as String? ?? 'Unknown error',
          details: _parseDetails(errorObj['details']),
        );
      }
    }

    return ApiException(
      code: 50001,
      message: error.message ?? 'Network error',
    );
  }

  static List<Map<String, dynamic>>? _parseDetails(dynamic raw) {
    if (raw is List) {
      return raw.cast<Map<String, dynamic>>();
    }
    return null;
  }

  @override
  String toString() => 'ApiException(code: $code, message: $message)';
}
