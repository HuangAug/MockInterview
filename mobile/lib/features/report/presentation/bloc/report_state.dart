// Report states — represent the polling / display lifecycle.
import 'package:mobile/shared/models/interview_report.dart';

sealed class ReportState {
  const ReportState();
}

/// Initial state before polling begins.
class ReportLoading extends ReportState {
  const ReportLoading();
}

/// Report is being generated on the server; polling in progress.
class ReportPolling extends ReportState {
  final int attempts;
  const ReportPolling(this.attempts);
}

/// Report fetched successfully.
class ReportReady extends ReportState {
  final InterviewReport report;
  const ReportReady(this.report);
}

/// Report generation failed or polling timed out.
class ReportFailed extends ReportState {
  final String message;
  const ReportFailed(this.message);
}
