// MaterialApp entry point with global providers and theme.
library;
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mobile/app/di.dart';
import 'package:mobile/app/router.dart';
import 'package:mobile/app/theme.dart';
import 'package:mobile/features/auth/data/auth_repository.dart';
import 'package:mobile/features/auth/presentation/bloc/auth_bloc.dart';
import 'package:mobile/features/interview/data/interview_repository.dart';
import 'package:mobile/features/interview/data/job_role_repository.dart';
import 'package:mobile/features/profile/data/user_repository.dart';

class MockInterviewApp extends StatelessWidget {
  const MockInterviewApp({super.key});

  @override
  Widget build(BuildContext context) {
    final appRouter = getIt<AppRouter>();
    final authRepository = getIt<AuthRepository>();

    return MultiRepositoryProvider(
      providers: [
        RepositoryProvider<AuthRepository>.value(value: authRepository),
        RepositoryProvider<InterviewRepository>.value(
          value: getIt<InterviewRepository>(),
        ),
        RepositoryProvider<JobRoleRepository>.value(
          value: getIt<JobRoleRepository>(),
        ),
        RepositoryProvider<UserRepository>.value(
          value: getIt<UserRepository>(),
        ),
      ],
      child: BlocProvider(
        create: (_) => AuthBloc(authRepository: authRepository),
        child: MaterialApp.router(
          title: 'MockInterview AI',
          theme: AppTheme.light,
          routerConfig: appRouter.router,
        ),
      ),
    );
  }
}
