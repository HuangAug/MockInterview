// HistoryBloc — loads paginated interview history.
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mobile/features/history/presentation/bloc/history_event.dart';
import 'package:mobile/features/history/presentation/bloc/history_state.dart';
import 'package:mobile/features/interview/data/interview_repository.dart';
import 'package:mobile/shared/models/interview_session.dart';

const _kPageSize = 20;

class HistoryBloc extends Bloc<HistoryEvent, HistoryState> {
  final InterviewRepository interviewRepository;

  List<InterviewSessionListItem> _allItems = [];
  int _currentPage = 0;
  bool _hasMore = true;

  HistoryBloc({required this.interviewRepository})
      : super(const HistoryInitial()) {
    on<LoadHistory>(_onLoadHistory);
    on<LoadMoreHistory>(_onLoadMore);
    on<RefreshHistory>(_onRefresh);
  }

  Future<void> _onLoadHistory(
    LoadHistory event,
    Emitter<HistoryState> emit,
  ) async {
    emit(const HistoryLoading());
    _allItems = [];
    _currentPage = 0;
    _hasMore = true;

    try {
      final response = await interviewRepository.listSessions(
        page: 1,
        pageSize: _kPageSize,
      );
      _allItems = response.items;
      _currentPage = 1;
      _hasMore = response.items.length >= _kPageSize;

      emit(HistoryLoaded(
        items: _allItems,
        hasMore: _hasMore,
        currentPage: _currentPage,
      ));
    } catch (e) {
      emit(HistoryError('加载历史记录失败: $e'));
    }
  }

  Future<void> _onLoadMore(
    LoadMoreHistory event,
    Emitter<HistoryState> emit,
  ) async {
    if (!_hasMore) return;

    try {
      final nextPage = _currentPage + 1;
      final response = await interviewRepository.listSessions(
        page: nextPage,
        pageSize: _kPageSize,
      );
      _allItems = [..._allItems, ...response.items];
      _currentPage = nextPage;
      _hasMore = response.items.length >= _kPageSize;

      emit(HistoryLoaded(
        items: _allItems,
        hasMore: _hasMore,
        currentPage: _currentPage,
      ));
    } catch (e) {
      // Keep existing items, just log
      emit(HistoryLoaded(
        items: _allItems,
        hasMore: _hasMore,
        currentPage: _currentPage,
      ));
    }
  }

  Future<void> _onRefresh(
    RefreshHistory event,
    Emitter<HistoryState> emit,
  ) async {
    _allItems = [];
    _currentPage = 0;
    _hasMore = true;

    try {
      final response = await interviewRepository.listSessions(
        page: 1,
        pageSize: _kPageSize,
      );
      _allItems = response.items;
      _currentPage = 1;
      _hasMore = response.items.length >= _kPageSize;

      emit(HistoryLoaded(
        items: _allItems,
        hasMore: _hasMore,
        currentPage: _currentPage,
      ));
    } catch (e) {
      emit(HistoryError('刷新失败: $e'));
    }
  }
}
