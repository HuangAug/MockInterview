import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:get_it/get_it.dart';
import 'package:mobile/app/router.dart';
import 'package:mobile/core/network/dio_client.dart';
import 'package:mobile/core/storage/secure_storage.dart';
import 'package:mobile/features/auth/data/auth_repository.dart';
import 'package:mobile/features/auth/presentation/bloc/auth_bloc.dart';
import 'package:mobile/features/interview/data/interview_repository.dart';
import 'package:mobile/features/interview/data/job_role_repository.dart';

final getIt = GetIt.instance;

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: '.env');

  // Register core services
  final secureStorage = SecureStorage();
  getIt.registerSingleton<SecureStorage>(secureStorage);

  final dio = DioClient.create(secureStorage: secureStorage);
  getIt.registerSingleton<Dio>(dio);

  // Register repositories
  getIt.registerSingleton<AuthRepository>(
    AuthRepository(dio: dio, secureStorage: secureStorage),
  );
  getIt.registerSingleton<InterviewRepository>(
    InterviewRepository(dio: dio),
  );
  getIt.registerSingleton<JobRoleRepository>(
    JobRoleRepository(dio: dio),
  );

  // Register router
  final appRouter = AppRouter(secureStorage: secureStorage);
  getIt.registerSingleton<AppRouter>(appRouter);

  runApp(const MockInterviewApp());
}

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
      ],
      child: BlocProvider(
        create: (_) => AuthBloc(authRepository: authRepository),
        child: MaterialApp.router(
          title: 'MockInterview AI',
          theme: ThemeData(
            colorSchemeSeed: const Color(0xFF2563EB),
            useMaterial3: true,
            scaffoldBackgroundColor: const Color(0xFFF8FAFC),
          ),
          routerConfig: appRouter.router,
        ),
      ),
    );
  }
}
