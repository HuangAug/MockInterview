import 'package:freezed_annotation/freezed_annotation.dart';

import 'interview_message.dart';

part 'interview_session.freezed.dart';
part 'interview_session.g.dart';

/// InterviewSessionResponse — matches API §2.5.
/// Detail endpoints include `messages`; list endpoints do not.
@freezed
sealed class InterviewSession with _$InterviewSession {
  const factory InterviewSession({
    required String id,
    required String jobRoleId,
    required String jobRoleName,
    required String difficulty, // "junior" | "mid" | "senior"
    required String mode, // "text" | "voice"
    required String status, // "pending" | "in_progress" | "completed" | "cancelled" | "failed"
    required int questionCount,
    required int maxQuestions,
    required String reportStatus, // "pending" | "generating" | "ready" | "failed"
    DateTime? startedAt,
    DateTime? endedAt,
    required DateTime createdAt,
    required DateTime updatedAt,
    @Default([]) List<InterviewMessage> messages,
  }) = _InterviewSession;

  factory InterviewSession.fromJson(Map<String, dynamic> json) =>
      _$InterviewSessionFromJson(json);
}

/// InterviewSessionListItem — matches API §2.6.
/// Used in paginated list responses.
@freezed
sealed class InterviewSessionListItem with _$InterviewSessionListItem {
  const factory InterviewSessionListItem({
    required String id,
    required String jobRoleName,
    required String difficulty,
    required String mode,
    required String status,
    required int questionCount,
    required String reportStatus,
    double? overallScore,
    required DateTime createdAt,
  }) = _InterviewSessionListItem;

  factory InterviewSessionListItem.fromJson(Map<String, dynamic> json) =>
      _$InterviewSessionListItemFromJson(json);
}