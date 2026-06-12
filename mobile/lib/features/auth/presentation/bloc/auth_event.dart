/// Auth BLoC events.
part of 'auth_bloc.dart';

sealed class AuthEvent extends Equatable {
  const AuthEvent();

  @override
  List<Object?> get props => [];
}

/// Check if user has a valid token on app startup.
class AuthCheckRequested extends AuthEvent {}

/// User submitted the login form.
class LoginButtonPressed extends AuthEvent {
  final String email;
  final String password;

  const LoginButtonPressed({required this.email, required this.password});

  @override
  List<Object?> get props => [email, password];
}

/// User submitted the registration form.
class RegisterButtonPressed extends AuthEvent {
  final String email;
  final String password;
  final String displayName;

  const RegisterButtonPressed({
    required this.email,
    required this.password,
    required this.displayName,
  });

  @override
  List<Object?> get props => [email, password, displayName];
}

/// User tapped logout.
class LogoutButtonPressed extends AuthEvent {}
