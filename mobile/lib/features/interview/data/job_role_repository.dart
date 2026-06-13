// JobRoleRepository — fetches job roles from the API.
import 'package:dio/dio.dart';
import 'package:mobile/core/network/api_exception.dart';
import 'package:mobile/shared/models/job_role.dart';

class JobRoleRepository {
  final Dio _dio;

  JobRoleRepository({required this._dio});

  /// GET /job-roles — returns active job roles sorted by sortOrder.
  Future<List<JobRole>> getJobRoles() async {
    try {
      final response = await _dio.get('/job-roles');
      final data = response.data as Map<String, dynamic>;
      final responseData = data['data'] as Map<String, dynamic>;
      final items = responseData['items'] as List<dynamic>;
      return items
          .map((e) => JobRole.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}
