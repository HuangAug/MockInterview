// Configured Dio HTTP client with auth interceptor.
import 'package:dio/dio.dart';
import 'package:mobile/core/constants/api_constants.dart';
import 'package:mobile/core/network/auth_interceptor.dart';
import 'package:mobile/core/storage/secure_storage.dart';

class DioClient {
  static Dio create({
    required SecureStorage secureStorage,
    void Function()? onUnauthorized,
  }) {
    final dio = Dio(
      BaseOptions(
        baseUrl: ApiConstants.baseUrl,
        connectTimeout: ApiConstants.connectTimeout,
        receiveTimeout: ApiConstants.receiveTimeout,
        headers: {'Content-Type': 'application/json'},
      ),
    );

    dio.interceptors.addAll([
      LogInterceptor(
        requestBody: true,
        responseBody: true,
        error: true,
      ),
      AuthInterceptor(
        dio: dio,
        secureStorage: secureStorage,
        onUnauthorized: onUnauthorized,
      ),
    ]);

    return dio;
  }
}
