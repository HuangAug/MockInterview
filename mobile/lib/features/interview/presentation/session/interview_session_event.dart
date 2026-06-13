part of 'interview_session_bloc.dart';

/// Events for the interview session page.
sealed class InterviewSessionEvent extends Equatable {
  const InterviewSessionEvent();

  @override
  List<Object?> get props => [];
}

/// Load session and auto-start if pending, or resume if in_progress.
class InitializeSession extends InterviewSessionEvent {
  final String sessionId;
  const InitializeSession(this.sessionId);

  @override
  List<Object?> get props => [sessionId];
}

/// Submit a candidate answer and receive the next question.
class SubmitAnswer extends InterviewSessionEvent {
  final String content;
  const SubmitAnswer(this.content);

  @override
  List<Object?> get props => [content];
}

/// Complete the interview (triggered when isFinished or user confirms end).
class CompleteInterview extends InterviewSessionEvent {
  const CompleteInterview();
}

/// Cancel the interview (triggered when user confirms end with 0 questions).
class CancelInterview extends InterviewSessionEvent {
  const CancelInterview();
}
