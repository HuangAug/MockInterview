// InterviewSetup BLoC — manages setup page state (job role, difficulty, mode).
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mobile/core/network/api_exception.dart';
import 'package:mobile/features/interview/data/interview_repository.dart';
import 'package:mobile/features/interview/data/job_role_repository.dart';
import 'package:mobile/shared/models/interview_session.dart';
import 'package:mobile/shared/models/job_role.dart';

part 'interview_setup_event.dart';
part 'interview_setup_state.dart';

class InterviewSetupBloc extends Bloc<InterviewSetupEvent, InterviewSetupState> {
  final JobRoleRepository _jobRoleRepository;
  final InterviewRepository _interviewRepository;

  InterviewSetupBloc({
    required this._jobRoleRepository,
    required this._interviewRepository,
  }) : super(const InterviewSetupState()) {
    on<LoadJobRoles>(_onLoadJobRoles);
    on<SelectJobRole>(_onSelectJobRole);
    on<SelectDifficulty>(_onSelectDifficulty);
    on<SelectMode>(_onSelectMode);
    on<CreateInterview>(_onCreateInterview);
  }

  Future<void> _onLoadJobRoles(
    LoadJobRoles event,
    Emitter<InterviewSetupState> emit,
  ) async {
    emit(state.copyWith(isLoading: true));
    try {
      final roles = await _jobRoleRepository.getJobRoles();
      emit(state.copyWith(isLoading: false, jobRoles: roles));
    } on ApiException catch (e) {
      emit(state.copyWith(isLoading: false, errorMessage: e.message));
    } catch (e) {
      emit(state.copyWith(isLoading: false, errorMessage: e.toString()));
    }
  }

  void _onSelectJobRole(
    SelectJobRole event,
    Emitter<InterviewSetupState> emit,
  ) {
    emit(state.copyWith(selectedJobRole: event.jobRole));
  }

  void _onSelectDifficulty(
    SelectDifficulty event,
    Emitter<InterviewSetupState> emit,
  ) {
    emit(state.copyWith(selectedDifficulty: event.difficulty));
  }

  void _onSelectMode(
    SelectMode event,
    Emitter<InterviewSetupState> emit,
  ) {
    emit(state.copyWith(selectedMode: event.mode));
  }

  Future<void> _onCreateInterview(
    CreateInterview event,
    Emitter<InterviewSetupState> emit,
  ) async {
    if (state.selectedJobRole == null ||
        state.selectedDifficulty == null ||
        state.selectedMode == null) {
      return;
    }

    emit(state.copyWith(isCreating: true));
    try {
      final session = await _interviewRepository.createSession(
        jobRoleId: state.selectedJobRole!.id,
        difficulty: state.selectedDifficulty!,
        mode: state.selectedMode!,
      );
      emit(state.copyWith(isCreating: false, createdSession: session));
    } on ApiException catch (e) {
      emit(state.copyWith(isCreating: false, errorMessage: e.message));
    } catch (e) {
      emit(state.copyWith(isCreating: false, errorMessage: e.toString()));
    }
  }
}
