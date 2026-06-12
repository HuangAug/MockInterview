import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: '.env');
  runApp(const MockInterviewApp());
}

class MockInterviewApp extends StatelessWidget {
  const MockInterviewApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MockInterview AI',
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFF2563EB),
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF8FAFC),
      ),
      home: const Scaffold(
        body: Center(
          child: Text('MockInterview AI'),
        ),
      ),
    );
  }
}
