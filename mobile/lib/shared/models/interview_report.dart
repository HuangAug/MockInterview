import 'package:freezed_annotation/freezed_annotation.dart';

part 'interview_report.freezed.dart';
part 'interview_report.g.dart';

/// QuestionFeedbackItem — matches API §2.7.
@freezed
sealed class QuestionFeedbackItem with _$QuestionFeedbackItem {
  const factory QuestionFeedbackItem({
    required int sequence,
    required String question,
    required String answerSummary,
    required double score,
    required String feedback,
  }) = _QuestionFeedbackItem;

  factory QuestionFeedbackItem.fromJson(Map<String, dynamic> json) =>
      _$QuestionFeedbackItemFromJson(json);
}

/// ReportResponse — matches API §2.8.
@freezed
sealed class InterviewReport with _$InterviewReport {
  const factory InterviewReport({
    required String id,
    required String sessionId,
    required double overallScore,
    required double communicationScore,
    required double technicalScore,
    required double problemSolvingScore,
    required double structureScore,
    required List<String> strengths,
    required List<String> weaknesses,
    required List<String> suggestions,
    required List<QuestionFeedbackItem> questionFeedback,
    required String summary,
    required DateTime createdAt,
  }) = _InterviewReport;

  factory InterviewReport.fromJson(Map<String, dynamic> json) =>
      _$InterviewReportFromJson(json);
}

/// ReportStatusResponse — matches API §2.9.
@freezed
sealed class ReportStatus with _$ReportStatus {
  const factory ReportStatus({
    required String sessionId,
    required String reportStatus, // "pending" | "generating" | "ready" | "failed"
  }) = _ReportStatus;

  factory ReportStatus.fromJson(Map<String, dynamic> json) =>
      _$ReportStatusFromJson(json);
}