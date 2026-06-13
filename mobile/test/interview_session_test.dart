// Tests for InterviewSessionBloc and InterviewSessionState.
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/interview/presentation/session/interview_session_bloc.dart';

void main() {
  group('InterviewSessionState', () {
    test('initial state has correct defaults', () {
      const state = InterviewSessionState();
      expect(state.session, isNull);
      expect(state.messages, isEmpty);
      expect(state.isLoading, isTrue);
      expect(state.isSubmitting, isFalse);
      expect(state.isFinished, isFalse);
      expect(state.isCompleted, isFalse);
      expect(state.isCancelled, isFalse);
      expect(state.errorMessage, isNull);
    });

    test('copyWith creates new state with overridden values', () {
      const state = InterviewSessionState();
      final updated = state.copyWith(
        isLoading: false,
        isFinished: true,
        errorMessage: 'test error',
      );

      expect(updated.isLoading, isFalse);
      expect(updated.isFinished, isTrue);
      expect(updated.errorMessage, 'test error');
      // Unchanged fields keep their defaults
      expect(updated.isSubmitting, isFalse);
      expect(updated.isCompleted, isFalse);
    });

    test('copyWith without errorMessage preserves null', () {
      const state = InterviewSessionState();
      final updated = state.copyWith(isLoading: false);
      expect(updated.errorMessage, isNull);
    });

    test('props includes all fields for equality comparison', () {
      const state1 = InterviewSessionState();
      const state2 = InterviewSessionState();
      expect(state1, equals(state2));
    });

    test('different states are not equal', () {
      const state1 = InterviewSessionState();
      final state2 = state1.copyWith(isLoading: false);
      expect(state1, isNot(equals(state2)));
    });
  });

  group('InterviewSessionEvent', () {
    test('InitializeSession holds sessionId', () {
      const event = InitializeSession('test-session-id');
      expect(event.sessionId, 'test-session-id');
      expect(event.props, ['test-session-id']);
    });

    test('SubmitAnswer holds content', () {
      const event = SubmitAnswer('my answer');
      expect(event.content, 'my answer');
      expect(event.props, ['my answer']);
    });

    test('CompleteInterview has empty props', () {
      const event = CompleteInterview();
      expect(event.props, isEmpty);
    });

    test('CancelInterview has empty props', () {
      const event = CancelInterview();
      expect(event.props, isEmpty);
    });
  });
}
