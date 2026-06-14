// ProfileBloc — loads user profile, job roles, and handles save.
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mobile/features/auth/data/models/auth_user.dart';
import 'package:mobile/features/interview/data/job_role_repository.dart';
import 'package:mobile/features/profile/data/user_repository.dart';
import 'package:mobile/features/profile/presentation/bloc/profile_event.dart';
import 'package:mobile/features/profile/presentation/bloc/profile_state.dart';
import 'package:mobile/shared/models/job_role.dart';

class ProfileBloc extends Bloc<ProfileEvent, ProfileState> {
  final UserRepository userRepository;
  final JobRoleRepository jobRoleRepository;

  List<JobRole> _jobRoles = [];

  ProfileBloc({
    required this.userRepository,
    required this.jobRoleRepository,
  }) : super(const ProfileLoading()) {
    on<LoadProfile>(_onLoadProfile);
    on<SaveProfile>(_onSaveProfile);
  }

  Future<void> _onLoadProfile(
    LoadProfile event,
    Emitter<ProfileState> emit,
  ) async {
    emit(const ProfileLoading());
    try {
      final userFuture = userRepository.getUser();
      final jobRolesFuture = jobRoleRepository.getJobRoles();
      final user = await userFuture;
      _jobRoles = await jobRolesFuture;
      emit(ProfileLoaded(user: user, jobRoles: _jobRoles));
    } catch (e) {
      emit(ProfileError('加载个人资料失败: $e'));
    }
  }

  Future<void> _onSaveProfile(
    SaveProfile event,
    Emitter<ProfileState> emit,
  ) async {
    final currentState = state;
    AuthUser? currentUser;
    if (currentState is ProfileLoaded) {
      currentUser = currentState.user;
    } else if (currentState is ProfileSaved) {
      currentUser = currentState.user;
    }
    if (currentUser != null) {
      emit(ProfileSaving(user: currentUser, jobRoles: _jobRoles));
    }

    try {
      final updatedUser = await userRepository.updateUser(
        displayName: event.displayName,
        targetJobRoleId: event.targetJobRoleId,
      );
      emit(ProfileSaved(user: updatedUser, jobRoles: _jobRoles));
    } catch (e) {
      emit(ProfileError('保存失败: $e'));
    }
  }
}
