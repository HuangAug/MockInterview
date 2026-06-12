import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/network/api_exception.dart';

void main() {
  group('ApiException', () {
    test('parses unified error response from DioException', () {
      final dioError = DioException(
        requestOptions: RequestOptions(path: '/test'),
        response: Response(
          requestOptions: RequestOptions(path: '/test'),
          statusCode: 400,
          data: {
            'success': false,
            'data': null,
            'error': {
              'code': 40001,
              'message': '参数校验失败',
              'details': [
                {'field': 'email', 'message': '邮箱格式不正确'},
              ],
            },
          },
        ),
      );

      final exception = ApiException.fromDioError(dioError);

      expect(exception.code, 40001);
      expect(exception.message, '参数校验失败');
      expect(exception.details, isNotNull);
      expect(exception.details!.length, 1);
      expect(exception.details!.first['field'], 'email');
    });

    test('falls back to 50001 when response has no error object', () {
      final dioError = DioException(
        requestOptions: RequestOptions(path: '/test'),
        response: Response(
          requestOptions: RequestOptions(path: '/test'),
          statusCode: 500,
          data: 'Internal Server Error',
        ),
      );

      final exception = ApiException.fromDioError(dioError);

      expect(exception.code, 50001);
    });

    test('falls back to 50001 when no response at all', () {
      final dioError = DioException(
        requestOptions: RequestOptions(path: '/test'),
        message: 'Connection refused',
      );

      final exception = ApiException.fromDioError(dioError);

      expect(exception.code, 50001);
      expect(exception.message, 'Connection refused');
    });

    test('toString includes code and message', () {
      const exception = ApiException(code: 40102, message: '邮箱或密码错误');
      expect(exception.toString(), contains('40102'));
      expect(exception.toString(), contains('邮箱或密码错误'));
    });
  });
}
