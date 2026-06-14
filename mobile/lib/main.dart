// App entry point — loads env, registers DI, runs app.
library;
import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:mobile/app/app.dart';
import 'package:mobile/app/di.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: '.env');

  setupDi();

  runApp(const MockInterviewApp());
}
