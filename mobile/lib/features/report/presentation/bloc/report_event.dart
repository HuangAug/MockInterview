/// Report events — drive report polling and display.
sealed class ReportEvent {}

/// Start polling report status for the given session.
class StartReportPolling extends ReportEvent {
  final String sessionId;
  StartReportPolling(this.sessionId);
}

/// Internal event fired by the polling timer.
class PollTick extends ReportEvent {}
