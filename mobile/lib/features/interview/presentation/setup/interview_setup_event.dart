/// InterviewSetup BLoC events.
part of 'interview_setup_bloc.dart';

sealed class InterviewSetupEvent extends Equatable {
  const InterviewSetupEvent();

  @override
  List<Object?> get props => [];
}

class LoadJobRoles extends InterviewSetupEvent {}

class SelectJobRole extends InterviewSetupEvent {
  final JobRole jobRole;

  const SelectJobRole(this.jobRole);

  @override
  List<Object?> get props => [jobRole];
}

class SelectDifficulty extends InterviewSetupEvent {
  final String difficulty;

  const SelectDifficulty(this.difficulty);

  @override
  List<Object?> get props => [difficulty];
}

class SelectMode extends InterviewSetupEvent {
  final String mode;

  const SelectMode(this.mode);

  @override
  List<Object?> get props => [mode];
}

class CreateInterview extends InterviewSetupEvent {}
