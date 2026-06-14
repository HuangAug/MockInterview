// Profile states — represent the profile page lifecycle.
import 'package:mobile/features/auth/data/models/auth_user.dart';
import 'package:mobile/shared/models/job_role.dart';

sealed class ProfileState {
  const ProfileState();
}

class ProfileLoading extends ProfileState {
  const ProfileLoading();
}

class ProfileLoaded extends ProfileState {
  final AuthUser user;
  final List<JobRole> jobRoles;

  const ProfileLoaded({required this.user, required this.jobRoles});
}

class ProfileSaving extends ProfileState {
  final AuthUser user;
  final List<JobRole> jobRoles;

  const ProfileSaving({required this.user, required this.jobRoles});
}

class ProfileSaved extends ProfileState {
  final AuthUser user;
  final List<JobRole> jobRoles;

  const ProfileSaved({required this.user, required this.jobRoles});
}

class ProfileError extends ProfileState {
  final String message;
  const ProfileError(this.message);
}
