// History events — load and paginate interview history.
sealed class HistoryEvent {}

class LoadHistory extends HistoryEvent {}

class LoadMoreHistory extends HistoryEvent {}

class RefreshHistory extends HistoryEvent {}
