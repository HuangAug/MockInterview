// History states — represent the interview list lifecycle.
import 'package:mobile/shared/models/interview_session.dart';

sealed class HistoryState {
  const HistoryState();
}

class HistoryInitial extends HistoryState {
  const HistoryInitial();
}

class HistoryLoading extends HistoryState {
  const HistoryLoading();
}

class HistoryLoaded extends HistoryState {
  final List<InterviewSessionListItem> items;
  final bool hasMore;
  final int currentPage;

  const HistoryLoaded({
    required this.items,
    required this.hasMore,
    required this.currentPage,
  });
}

class HistoryError extends HistoryState {
  final String message;
  const HistoryError(this.message);
}
