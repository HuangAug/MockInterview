// Interview session BLoC — manages Q&A flow for text mode.
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mobile/core/network/api_exception.dart';
import 'package:mobile/features/interview/data/interview_repository.dart';
import 'package:mobile/shared/models/interview_message.dart';
import 'package:mobile/shared/models/interview_session.dart';

part 'interview_session_event.dart';
part 'interview_session_state.dart';

class InterviewSessionBloc
    extends Bloc<InterviewSessionEvent, InterviewSessionState> {
  final InterviewRepository _interviewRepository;

  InterviewSessionBloc({required this._interviewRepository})
      : super(const InterviewSessionState()) {
    on<InitializeSession>(_onInitialize);
    on<SubmitAnswer>(_onSubmitAnswer);
    on<CompleteInterview>(_onComplete);
    on<CancelInterview>(_onCancel);
  }

  /// Load session details and auto-start if pending.
  Future<void> _onInitialize(
    InitializeSession event,
    Emitter<InterviewSessionState> emit,
  ) async {
    emit(state.copyWith(isLoading: true));
    try {
      final session = await _interviewRepository.getSession(event.sessionId);

      if (session.status == 'pending') {
        final startResult =
            await _interviewRepository.startInterview(event.sessionId);
        emit(state.copyWith(
          isLoading: false,
          session: startResult.session,
          messages: [startResult.question],
        ));
      } else if (session.status == 'in_progress') {
        emit(state.copyWith(
          isLoading: false,
          session: session,
          messages: session.messages,
        ));
      } else {
        // Session is in a terminal state (completed, cancelled, failed)
        emit(state.copyWith(
          isLoading: false,
          session: session,
          messages: session.messages,
        ));
      }
    } on ApiException catch (e) {
      emit(state.copyWith(isLoading: false, errorMessage: e.message));
    } catch (e) {
      emit(state.copyWith(isLoading: false, errorMessage: e.toString()));
    }
  }

  /// Submit a candidate answer and handle the next question or finish signal.
  Future<void> _onSubmitAnswer(
    SubmitAnswer event,
    Emitter<InterviewSessionState> emit,
  ) async {
    if (state.session == null) return;

    emit(state.copyWith(isSubmitting: true, errorMessage: null));
    try {
      final result = await _interviewRepository.submitAnswer(
        state.session!.id,
        content: event.content,
      );

      final updatedMessages = List<InterviewMessage>.from(state.messages);
      updatedMessages.add(result.answer);

      if (result.nextQuestion != null) {
        updatedMessages.add(result.nextQuestion!);
      }

      emit(state.copyWith(
        isSubmitting: false,
        messages: updatedMessages,
        isFinished: result.isFinished,
        session: state.session!.copyWith(
          questionCount: result.questionCount,
        ),
      ));

      // Auto-complete when interview is finished
      if (result.isFinished) {
        add(CompleteInterview());
      }
    } on ApiException catch (e) {
      emit(state.copyWith(isSubmitting: false, errorMessage: e.message));
    } catch (e) {
      emit(state.copyWith(isSubmitting: false, errorMessage: e.toString()));
    }
  }

  /// Complete the interview and trigger report generation.
  Future<void> _onComplete(
    CompleteInterview event,
    Emitter<InterviewSessionState> emit,
  ) async {
    if (state.session == null) return;

    emit(state.copyWith(isLoading: true));
    try {
      await _interviewRepository.completeInterview(state.session!.id);
      emit(state.copyWith(isLoading: false, isCompleted: true));
    } on ApiException catch (e) {
      emit(state.copyWith(isLoading: false, errorMessage: e.message));
    } catch (e) {
      emit(state.copyWith(isLoading: false, errorMessage: e.toString()));
    }
  }

  /// Cancel the interview (0 questions answered).
  Future<void> _onCancel(
    CancelInterview event,
    Emitter<InterviewSessionState> emit,
  ) async {
    if (state.session == null) return;

    emit(state.copyWith(isLoading: true));
    try {
      await _interviewRepository.cancelInterview(state.session!.id);
      emit(state.copyWith(isLoading: false, isCancelled: true));
    } on ApiException catch (e) {
      emit(state.copyWith(isLoading: false, errorMessage: e.message));
    } catch (e) {
      emit(state.copyWith(isLoading: false, errorMessage: e.toString()));
    }
  }
}
