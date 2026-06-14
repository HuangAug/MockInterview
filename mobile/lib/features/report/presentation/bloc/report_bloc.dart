// ReportBloc — polls report status every 2 seconds, up to 60 attempts.
import 'dart:async';

import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mobile/features/interview/data/interview_repository.dart';
import 'package:mobile/features/report/presentation/bloc/report_event.dart';
import 'package:mobile/features/report/presentation/bloc/report_state.dart';

const _kPollInterval = Duration(seconds: 2);
const _kMaxPollAttempts = 60;

class ReportBloc extends Bloc<ReportEvent, ReportState> {
  final InterviewRepository interviewRepository;

  Timer? _pollTimer;
  int _attempts = 0;
  String? _sessionId;

  ReportBloc({required this.interviewRepository}) : super(const ReportLoading()) {
    on<StartReportPolling>(_onStartPolling);
    on<PollTick>(_onPollTick);
  }

  Future<void> _onStartPolling(
    StartReportPolling event,
    Emitter<ReportState> emit,
  ) async {
    _sessionId = event.sessionId;
    _attempts = 0;
    emit(const ReportPolling(0));

    // First tick immediately
    add(PollTick());
  }

  Future<void> _onPollTick(
    PollTick event,
    Emitter<ReportState> emit,
  ) async {
    if (_sessionId == null) return;

    _attempts++;
    emit(ReportPolling(_attempts));

    try {
      final status = await interviewRepository.getReportStatus(_sessionId!);

      if (status.reportStatus == 'ready') {
        final report = await interviewRepository.getReport(_sessionId!);
        emit(ReportReady(report));
        _cancelTimer();
        return;
      }

      if (status.reportStatus == 'failed') {
        emit(const ReportFailed('报告生成失败，请稍后在历史记录中查看'));
        _cancelTimer();
        return;
      }

      // Still generating — check max attempts
      if (_attempts >= _kMaxPollAttempts) {
        emit(const ReportFailed('报告生成超时，请稍后在历史记录中查看'));
        _cancelTimer();
        return;
      }

      // Schedule next poll
      _scheduleNextPoll();
    } catch (e) {
      emit(ReportFailed('获取报告状态失败: $e'));
      _cancelTimer();
    }
  }

  void _scheduleNextPoll() {
    _cancelTimer();
    _pollTimer = Timer(_kPollInterval, () => add(PollTick()));
  }

  void _cancelTimer() {
    _pollTimer?.cancel();
    _pollTimer = null;
  }

  @override
  Future<void> close() {
    _cancelTimer();
    return super.close();
  }
}
