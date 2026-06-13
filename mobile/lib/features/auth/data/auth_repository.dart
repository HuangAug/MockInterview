// AuthRepository — handles auth API calls and token persistence.
import 'package:dio/dio.dart';
import 'package:mobile/core/network/api_exception.dart';
import 'package:mobile/core/storage/secure_storage.dart';
import 'package:mobile/features/auth/data/models/auth_tokens.dart';
import 'package:mobile/features/auth/data/models/auth_user.dart';

class AuthRepository {
  final Dio _dio;
  final SecureStorage _secureStorage;

  AuthRepository({required this._dio, required this._secureStorage});

  /// Register a new user. Returns (user, tokens).
  Future<(AuthUser, AuthTokens)> register({
    required String email,
    required String password,
    required String displayName,
  }) async {
    try {
      final response = await _dio.post('/auth/register', data: {
        'email': email,
        'password': password,
        'displayName': displayName,
      });
      return _parseAuthResponse(response);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Login with email and password. Returns (user, tokens).
  Future<(AuthUser, AuthTokens)> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _dio.post('/auth/login', data: {
        'email': email,
        'password': password,
      });
      return _parseAuthResponse(response);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Logout — revoke the current refresh token.
  Future<void> logout() async {
    final refreshToken = await _secureStorage.getRefreshToken();
    if (refreshToken != null) {
      try {
        await _dio.post('/auth/logout', data: {
          'refreshToken': refreshToken,
        });
      } on DioException {
        // Ignore errors — token may already be revoked
      }
    }
    await _secureStorage.deleteTokens();
  }

  /// Check if the user has a stored access token.
  Future<bool> hasToken() async {
    final token = await _secureStorage.getAccessToken();
    return token != null;
  }

  Future<(AuthUser, AuthTokens)> _parseAuthResponse(Response response) async {
    final data = response.data as Map<String, dynamic>;
    final responseData = data['data'] as Map<String, dynamic>;
    final user = AuthUser.fromJson(responseData['user'] as Map<String, dynamic>);
    final tokens = AuthTokens.fromJson(responseData['tokens'] as Map<String, dynamic>);

    await _secureStorage.saveTokens(
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
    );

    return (user, tokens);
  }
}
