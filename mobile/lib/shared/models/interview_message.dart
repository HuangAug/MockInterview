import 'package:freezed_annotation/freezed_annotation.dart';

part 'interview_message.freezed.dart';
part 'interview_message.g.dart';

/// MessageResponse — matches API §2.4 and backend MessageResponse schema.
@freezed
sealed class InterviewMessage with _$InterviewMessage {
  const factory InterviewMessage({
    required String id,
    required String sessionId,
    required String role, // "interviewer" | "candidate"
    required String content,
    String? audioUrl,
    required int sequence,
    required DateTime createdAt,
  }) = _InterviewMessage;

  factory InterviewMessage.fromJson(Map<String, dynamic> json) =>
      _$InterviewMessageFromJson(json);
}