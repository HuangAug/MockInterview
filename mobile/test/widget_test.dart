import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/router.dart';
import 'package:mobile/core/storage/secure_storage.dart';

void main() {
  test('AppRouter can be instantiated with SecureStorage', () {
    final secureStorage = SecureStorage();
    final appRouter = AppRouter(secureStorage: secureStorage);

    expect(appRouter.router, isNotNull);
    expect(appRouter.secureStorage, same(secureStorage));
  });
}
