// InterviewRepository — handles all interview API calls.
import 'package:dio/dio.dart';
import 'package:mobile/core/network/api_exception.dart';
import 'package:mobile/core/storage/secure_storage.dart';
import 'package:mobile/shared/models/interview_message.dart';
import 'package:mobile/shared/models/interview_report.dart';
import 'package:mobile/shared/models/interview_session.dart';
import 'package:mobile/shared/models/pagination.dart';
import 'package:path/path.dart' as p;

/// Response shape for GET /interviews (paginated list).
class InterviewListResponse {
  final List<InterviewSessionListItem> items;
  final Pagination pagination;

  const InterviewListResponse({required this.items, required this.pagination});
}

/// Response shape for POST /interviews/{id}/start.
class StartInterviewResponse {
  final InterviewSession session;
  final InterviewMessage question;

  const StartInterviewResponse({
    required this.session,
    required this.question,
  });
}

/// Response shape for POST /interviews/{id}/messages.
class SubmitAnswerResponse {
  final InterviewMessage answer;
  final InterviewMessage? nextQuestion;
  final bool isFinished;
  final int questionCount;

  const SubmitAnswerResponse({
    required this.answer,
    this.nextQuestion,
    required this.isFinished,
    required this.questionCount,
  });
}

class InterviewRepository {
  final Dio _dio;
  final SecureStorage _secureStorage;

  InterviewRepository({required this._dio, required this._secureStorage});

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  /// Extract the `data` field from a unified API response.
  Map<String, dynamic> _extractData(Response response) {
    final body = response.data as Map<String, dynamic>;
    return body['data'] as Map<String, dynamic>;
  }

  /// Extract the `items` and `pagination` from a paginated response.
  InterviewListResponse _extractList(Map<String, dynamic> data) {
    final items = (data['items'] as List<dynamic>)
        .map((e) =>
            InterviewSessionListItem.fromJson(e as Map<String, dynamic>))
        .toList();
    final pagination =
        Pagination.fromJson(data['pagination'] as Map<String, dynamic>);
    return InterviewListResponse(items: items, pagination: pagination);
  }

  // ---------------------------------------------------------------------------
  // POST /interviews — create a new interview session
  // ---------------------------------------------------------------------------

  Future<InterviewSession> createSession({
    required String jobRoleId,
    required String difficulty,
    required String mode,
  }) async {
    try {
      final response = await _dio.post('/interviews', data: {
        'jobRoleId': jobRoleId,
        'difficulty': difficulty,
        'mode': mode,
      });
      final data = _extractData(response);
      return InterviewSession.fromJson(data);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ---------------------------------------------------------------------------
  // GET /interviews — list user's interview history (paginated)
  // ---------------------------------------------------------------------------

  Future<InterviewListResponse> listSessions({
    int page = 1,
    int pageSize = 20,
    String? status,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'page': page,
        'pageSize': pageSize,
      };
      if (status != null) {
        queryParams['status'] = status;
      }
      final response = await _dio.get('/interviews', queryParameters: queryParams);
      final data = _extractData(response);
      return _extractList(data);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ---------------------------------------------------------------------------
  // GET /interviews/{id} — get session detail with messages
  // ---------------------------------------------------------------------------

  Future<InterviewSession> getSession(String id) async {
    try {
      final response = await _dio.get('/interviews/$id');
      final data = _extractData(response);
      return InterviewSession.fromJson(data);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ---------------------------------------------------------------------------
  // POST /interviews/{id}/start — start the interview
  // ---------------------------------------------------------------------------

  Future<StartInterviewResponse> startInterview(String id) async {
    try {
      final response = await _dio.post('/interviews/$id/start');
      final data = _extractData(response);
      return StartInterviewResponse(
        session: InterviewSession.fromJson(
            data['session'] as Map<String, dynamic>),
        question: InterviewMessage.fromJson(
            data['question'] as Map<String, dynamic>),
      );
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ---------------------------------------------------------------------------
  // POST /interviews/{id}/messages — submit an answer
  // ---------------------------------------------------------------------------

  Future<SubmitAnswerResponse> submitAnswer(
    String id, {
    required String content,
  }) async {
    try {
      final response = await _dio.post('/interviews/$id/messages', data: {
        'content': content,
      });
      final data = _extractData(response);
      final nextQuestionJson = data['nextQuestion'] as Map<String, dynamic>?;
      return SubmitAnswerResponse(
        answer: InterviewMessage.fromJson(
            data['answer'] as Map<String, dynamic>),
        nextQuestion: nextQuestionJson != null
            ? InterviewMessage.fromJson(nextQuestionJson)
            : null,
        isFinished: data['isFinished'] as bool,
        questionCount: data['questionCount'] as int,
      );
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ---------------------------------------------------------------------------
  // POST /interviews/{id}/complete — complete the interview
  // ---------------------------------------------------------------------------

  Future<InterviewSession> completeInterview(String id) async {
    try {
      final response = await _dio.post('/interviews/$id/complete');
      final data = _extractData(response);
      return InterviewSession.fromJson(data);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ---------------------------------------------------------------------------
  // POST /interviews/{id}/cancel — cancel the interview
  // ---------------------------------------------------------------------------

  Future<InterviewSession> cancelInterview(String id) async {
    try {
      final response = await _dio.post('/interviews/$id/cancel');
      final data = _extractData(response);
      return InterviewSession.fromJson(data);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ---------------------------------------------------------------------------
  // GET /interviews/{id}/report/status — poll report generation status
  // ---------------------------------------------------------------------------

  Future<ReportStatus> getReportStatus(String id) async {
    try {
      final response = await _dio.get('/interviews/$id/report/status');
      final data = _extractData(response);
      return ReportStatus.fromJson(data);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ---------------------------------------------------------------------------
  // GET /interviews/{id}/report — get the full report
  // ---------------------------------------------------------------------------

  Future<InterviewReport> getReport(String id) async {
    try {
      final response = await _dio.get('/interviews/$id/report');
      final data = _extractData(response);
      return InterviewReport.fromJson(data);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ---------------------------------------------------------------------------
  // POST /interviews/{id}/transcribe — upload audio and transcribe
  // ---------------------------------------------------------------------------

  Future<String> transcribeAudio(String sessionId, String filePath) async {
    try {
      final fileName = p.basename(filePath);
      final formData = FormData.fromMap({
        'audio': await MultipartFile.fromFile(filePath, filename: fileName),
      });
      final response = await _dio.post(
        '/interviews/$sessionId/transcribe',
        data: formData,
      );
      final data = _extractData(response);
      return data['text'] as String;
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ---------------------------------------------------------------------------
  // GET /interviews/{id}/messages/{messageId}/tts — download TTS audio
  // ---------------------------------------------------------------------------

  Future<String> downloadTtsAudio(
    String sessionId,
    String messageId,
    String savePath,
  ) async {
    try {
      final token = await _secureStorage.getAccessToken();
      await _dio.download(
        '/interviews/$sessionId/messages/$messageId/tts',
        savePath,
        options: Options(
          headers: {
            if (token != null) 'Authorization': 'Bearer $token',
          },
        ),
      );
      return savePath;
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}