// UserRepository — handles user profile API calls.
import 'package:dio/dio.dart';
import 'package:mobile/core/network/api_exception.dart';
import 'package:mobile/features/auth/data/models/auth_user.dart';

class UserRepository {
  final Dio _dio;

  UserRepository({required this._dio});

  /// GET /users/me — get current user profile.
  Future<AuthUser> getUser() async {
    try {
      final response = await _dio.get('/users/me');
      final data = response.data as Map<String, dynamic>;
      final responseData = data['data'] as Map<String, dynamic>;
      return AuthUser.fromJson(responseData);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// PATCH /users/me — update display name and/or target job role.
  Future<AuthUser> updateUser({
    String? displayName,
    String? targetJobRoleId,
  }) async {
    try {
      final body = <String, dynamic>{};
      if (displayName != null) body['displayName'] = displayName;
      if (targetJobRoleId != null) {
        // Allow null to clear the target job role
        body['targetJobRoleId'] = targetJobRoleId.isEmpty ? null : targetJobRoleId;
      }
      final response = await _dio.patch('/users/me', data: body);
      final data = response.data as Map<String, dynamic>;
      final responseData = data['data'] as Map<String, dynamic>;
      return AuthUser.fromJson(responseData);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}
