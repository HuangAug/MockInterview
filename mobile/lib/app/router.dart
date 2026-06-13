// GoRouter configuration with auth redirect.
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile/core/storage/secure_storage.dart';
import 'package:mobile/features/auth/presentation/pages/login_page.dart';
import 'package:mobile/features/auth/presentation/pages/register_page.dart';
import 'package:mobile/features/home/presentation/pages/home_page.dart';
import 'package:mobile/features/home/presentation/pages/splash_page.dart';
import 'package:mobile/features/interview/presentation/session/interview_session_bloc.dart';
import 'package:mobile/features/interview/presentation/session/interview_session_page.dart';
import 'package:mobile/features/interview/presentation/setup/interview_setup_bloc.dart';
import 'package:mobile/features/interview/presentation/setup/interview_setup_page.dart';

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
        builder: (context, state) {
          // T033 will implement this page
          return Scaffold(
            appBar: AppBar(title: const Text('报告')),
            body: const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('报告生成中，请稍候...'),
                ],
              ),
            ),
          );
        },
      ),
      GoRoute(
        path: '/history',
        builder: (context, state) {
          // T035 will implement this page
          return Scaffold(
            appBar: AppBar(title: const Text('历史记录')),
            body: const Center(child: Text('暂无面试记录')),
            bottomNavigationBar: NavigationBar(
              selectedIndex: 1,
              onDestinationSelected: (index) {
                switch (index) {
                  case 0:
                    context.go('/home');
                  case 1:
                    break;
                  case 2:
                    context.go('/profile');
                }
              },
              destinations: const [
                NavigationDestination(
                  icon: Icon(Icons.home_outlined),
                  selectedIcon: Icon(Icons.home),
                  label: '首页',
                ),
                NavigationDestination(
                  icon: Icon(Icons.history_outlined),
                  selectedIcon: Icon(Icons.history),
                  label: '历史',
                ),
                NavigationDestination(
                  icon: Icon(Icons.person_outlined),
                  selectedIcon: Icon(Icons.person),
                  label: '我的',
                ),
              ],
            ),
          );
        },
      ),
      GoRoute(
        path: '/profile',
        builder: (context, state) {
          // T036 will implement this page
          return Scaffold(
            appBar: AppBar(title: const Text('个人资料')),
            body: const Center(child: Text('个人资料页')),
            bottomNavigationBar: NavigationBar(
              selectedIndex: 2,
              onDestinationSelected: (index) {
                switch (index) {
                  case 0:
                    context.go('/home');
                  case 1:
                    context.go('/history');
                  case 2:
                    break;
                }
              },
              destinations: const [
                NavigationDestination(
                  icon: Icon(Icons.home_outlined),
                  selectedIcon: Icon(Icons.home),
                  label: '首页',
                ),
                NavigationDestination(
                  icon: Icon(Icons.history_outlined),
                  selectedIcon: Icon(Icons.history),
                  label: '历史',
                ),
                NavigationDestination(
                  icon: Icon(Icons.person_outlined),
                  selectedIcon: Icon(Icons.person),
                  label: '我的',
                ),
              ],
            ),
          );
        },
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
