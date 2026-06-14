// Profile events — load and save user profile.
sealed class ProfileEvent {}

class LoadProfile extends ProfileEvent {}

class SaveProfile extends ProfileEvent {
  final String displayName;
  final String? targetJobRoleId;
  SaveProfile({required this.displayName, this.targetJobRoleId});
}
