// GoRouter configuration with auth redirect.
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile/core/storage/secure_storage.dart';
import 'package:mobile/features/auth/presentation/pages/login_page.dart';
import 'package:mobile/features/auth/presentation/pages/register_page.dart';
import 'package:mobile/features/home/presentation/pages/home_page.dart';
import 'package:mobile/features/home/presentation/pages/splash_page.dart';
import 'package:mobile/features/history/presentation/bloc/history_bloc.dart';
import 'package:mobile/features/history/presentation/pages/history_page.dart';
import 'package:mobile/features/interview/data/job_role_repository.dart';
import 'package:mobile/features/interview/presentation/session/interview_session_bloc.dart';
import 'package:mobile/features/interview/presentation/session/interview_session_page.dart';
import 'package:mobile/features/interview/presentation/setup/interview_setup_bloc.dart';
import 'package:mobile/features/interview/presentation/setup/interview_setup_page.dart';
import 'package:mobile/features/profile/data/user_repository.dart';
import 'package:mobile/features/profile/presentation/bloc/profile_bloc.dart';
import 'package:mobile/features/profile/presentation/pages/profile_page.dart';
import 'package:mobile/features/report/presentation/bloc/report_bloc.dart';
import 'package:mobile/features/report/presentation/pages/interview_report_page.dart';

class AppRouter {
  final SecureStorage secureStorage;

  AppRouter({required this.secureStorage});

  late final GoRouter router = GoRouter(
    initialLocation: '/splash',
    redirect: _redirect,
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashPage(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginPage(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterPage(),
      ),
      GoRoute(
        path: '/home',
        builder: (context, state) => const HomePage(),
      ),
      GoRoute(
        path: '/interview/setup',
        builder: (context, state) => BlocProvider(
          create: (context) => InterviewSetupBloc(
            jobRoleRepository: context.read(),
            interviewRepository: context.read(),
          ),
          child: const InterviewSetupPage(),
        ),
      ),
      GoRoute(
        path: '/interview/session/:id',
        builder: (context, state) => BlocProvider(
          create: (context) => InterviewSessionBloc(
            interviewRepository: context.read(),
          ),
          child: InterviewSessionPage(
            sessionId: state.pathParameters['id']!,
          ),
        ),
      ),
      GoRoute(
        path: '/interview/report/:id',
        builder: (context, state) => BlocProvider(
          create: (context) => ReportBloc(
            interviewRepository: context.read(),
          ),
          child: InterviewReportPage(
            sessionId: state.pathParameters['id']!,
          ),
        ),
      ),
      GoRoute(
        path: '/history',
        builder: (context, state) => BlocProvider(
          create: (context) => HistoryBloc(
            interviewRepository: context.read(),
          ),
          child: const HistoryPage(),
        ),
      ),
      GoRoute(
        path: '/profile',
        builder: (context, state) => BlocProvider(
          create: (context) => ProfileBloc(
            userRepository: context.read<UserRepository>(),
            jobRoleRepository: context.read<JobRoleRepository>(),
          ),
          child: const ProfilePage(),
        ),
      ),
    ],
  );

  Future<String?> _redirect(
    BuildContext context,
    GoRouterState state,
  ) async {
    final isAuthRoute =
        state.matchedLocation == '/login' ||
        state.matchedLocation == '/register' ||
        state.matchedLocation == '/splash';

    final hasToken = await secureStorage.getAccessToken() != null;

    // If on splash, let it handle its own navigation
    if (state.matchedLocation == '/splash') {
      return null;
    }

    // If not authenticated and trying to access protected route
    if (!hasToken && !isAuthRoute) {
      return '/login';
    }

    // If authenticated and trying to access auth routes
    if (hasToken && isAuthRoute) {
      return '/home';
    }

    return null;
  }
}
