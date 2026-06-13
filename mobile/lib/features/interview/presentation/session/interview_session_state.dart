part of 'interview_session_bloc.dart';

/// State for the interview session page.
class InterviewSessionState extends Equatable {
  final InterviewSession? session;
  final List<InterviewMessage> messages;
  final bool isLoading;
  final bool isSubmitting;
  final bool isFinished;
  final bool isCompleted;
  final bool isCancelled;
  final String? errorMessage;

  const InterviewSessionState({
    this.session,
    this.messages = const [],
    this.isLoading = true,
    this.isSubmitting = false,
    this.isFinished = false,
    this.isCompleted = false,
    this.isCancelled = false,
    this.errorMessage,
  });

  InterviewSessionState copyWith({
    InterviewSession? session,
    List<InterviewMessage>? messages,
    bool? isLoading,
    bool? isSubmitting,
    bool? isFinished,
    bool? isCompleted,
    bool? isCancelled,
    String? errorMessage,
  }) {
    return InterviewSessionState(
      session: session ?? this.session,
      messages: messages ?? this.messages,
      isLoading: isLoading ?? this.isLoading,
      isSubmitting: isSubmitting ?? this.isSubmitting,
      isFinished: isFinished ?? this.isFinished,
      isCompleted: isCompleted ?? this.isCompleted,
      isCancelled: isCancelled ?? this.isCancelled,
      errorMessage: errorMessage,
    );
  }

  @override
  List<Object?> get props => [
        session,
        messages,
        isLoading,
        isSubmitting,
        isFinished,
        isCompleted,
        isCancelled,
        errorMessage,
      ];
}
