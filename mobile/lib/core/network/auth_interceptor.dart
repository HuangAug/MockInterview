// Dio interceptor that injects the access token and auto-refreshes on 401.
import 'package:dio/dio.dart';
import 'package:mobile/core/storage/secure_storage.dart';

class AuthInterceptor extends Interceptor {
  final Dio _dio;
  final SecureStorage _secureStorage;

  void Function()? onUnauthorized;

  bool _isRefreshing = false;
  Future<void>? _refreshFuture;

  AuthInterceptor({
    required this._dio,
    required this._secureStorage,
    this.onUnauthorized,
  });

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _secureStorage.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode != 401) {
      handler.next(err);
      return;
    }

    final options = err.requestOptions;

    // Don't retry refresh or auth endpoints to avoid infinite loops
    if (options.path.contains('/auth/refresh') ||
        options.path.contains('/auth/login') ||
        options.path.contains('/auth/register')) {
      handler.next(err);
      return;
    }

    // If already refreshing, wait for existing refresh
    if (_isRefreshing && _refreshFuture != null) {
      try {
        await _refreshFuture;
        final token = await _secureStorage.getAccessToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        final response = await _dio.fetch(options);
        handler.resolve(response);
      } catch (_) {
        handler.next(err);
      }
      return;
    }

    _isRefreshing = true;
    _refreshFuture = _performRefresh();

    try {
      await _refreshFuture;
      final token = await _secureStorage.getAccessToken();
      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      }
      final response = await _dio.fetch(options);
      handler.resolve(response);
    } catch (_) {
      await _secureStorage.deleteTokens();
      onUnauthorized?.call();
      handler.next(err);
    } finally {
      _isRefreshing = false;
      _refreshFuture = null;
    }
  }

  Future<void> _performRefresh() async {
    final refreshToken = await _secureStorage.getRefreshToken();
    if (refreshToken == null) {
      throw Exception('No refresh token available');
    }

    final response = await _dio.post(
      '/auth/refresh',
      data: {'refreshToken': refreshToken},
      options: Options(
        validateStatus: (status) => status != null && status < 500,
      ),
    );

    if (response.statusCode == 200) {
      final responseData = response.data;
      if (responseData is Map<String, dynamic>) {
        final data = responseData['data'];
        if (data is Map<String, dynamic>) {
          await _secureStorage.saveTokens(
            accessToken: data['accessToken'] as String,
            refreshToken: data['refreshToken'] as String,
          );
          return;
        }
      }
    }

    throw Exception('Refresh failed');
  }
}
