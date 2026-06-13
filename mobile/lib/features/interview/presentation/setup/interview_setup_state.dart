/// InterviewSetup BLoC state.
part of 'interview_setup_bloc.dart';

class InterviewSetupState extends Equatable {
  final bool isLoading;
  final bool isCreating;
  final List<JobRole> jobRoles;
  final JobRole? selectedJobRole;
  final String? selectedDifficulty;
  final String? selectedMode;
  final InterviewSession? createdSession;
  final String? errorMessage;

  const InterviewSetupState({
    this.isLoading = false,
    this.isCreating = false,
    this.jobRoles = const [],
    this.selectedJobRole,
    this.selectedDifficulty,
    this.selectedMode,
    this.createdSession,
    this.errorMessage,
  });

  bool get canStart =>
      selectedJobRole != null &&
      selectedDifficulty != null &&
      selectedMode != null;

  InterviewSetupState copyWith({
    bool? isLoading,
    bool? isCreating,
    List<JobRole>? jobRoles,
    JobRole? selectedJobRole,
    String? selectedDifficulty,
    String? selectedMode,
    InterviewSession? createdSession,
    String? errorMessage,
  }) {
    return InterviewSetupState(
      isLoading: isLoading ?? this.isLoading,
      isCreating: isCreating ?? this.isCreating,
      jobRoles: jobRoles ?? this.jobRoles,
      selectedJobRole: selectedJobRole ?? this.selectedJobRole,
      selectedDifficulty: selectedDifficulty ?? this.selectedDifficulty,
      selectedMode: selectedMode ?? this.selectedMode,
      createdSession: createdSession ?? this.createdSession,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }

  @override
  List<Object?> get props => [
        isLoading,
        isCreating,
        jobRoles,
        selectedJobRole,
        selectedDifficulty,
        selectedMode,
        createdSession,
        errorMessage,
      ];
}
