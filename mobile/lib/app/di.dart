// Dependency injection setup using GetIt.
//
// Call [setupDi] once in `main()` before `runApp`.
library;
import 'package:dio/dio.dart';
import 'package:get_it/get_it.dart';
import 'package:mobile/app/router.dart';
import 'package:mobile/core/audio/audio_service.dart';
import 'package:mobile/core/network/dio_client.dart';
import 'package:mobile/core/storage/secure_storage.dart';
import 'package:mobile/features/auth/data/auth_repository.dart';
import 'package:mobile/features/interview/data/interview_repository.dart';
import 'package:mobile/features/interview/data/job_role_repository.dart';
import 'package:mobile/features/profile/data/user_repository.dart';

final getIt = GetIt.instance;

/// Registers all singletons (services, repositories, router).
void setupDi() {
  // Core services
  final secureStorage = SecureStorage();
  getIt.registerSingleton<SecureStorage>(secureStorage);

  final dio = DioClient.create(secureStorage: secureStorage);
  getIt.registerSingleton<Dio>(dio);

  // Repositories
  getIt.registerSingleton<AuthRepository>(
    AuthRepository(dio: dio, secureStorage: secureStorage),
  );
  final interviewRepository = InterviewRepository(
    dio: dio,
    secureStorage: secureStorage,
  );
  getIt.registerSingleton<InterviewRepository>(interviewRepository);
  getIt.registerSingleton<JobRoleRepository>(
    JobRoleRepository(dio: dio),
  );
  getIt.registerSingleton<UserRepository>(
    UserRepository(dio: dio),
  );

  // Audio service for voice mode
  getIt.registerSingleton<AudioService>(
    AudioService(interviewRepository: interviewRepository),
  );

  // Router
  final appRouter = AppRouter(secureStorage: secureStorage);
  getIt.registerSingleton<AppRouter>(appRouter);
}
