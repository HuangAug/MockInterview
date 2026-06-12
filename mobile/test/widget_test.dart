import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/main.dart';

void main() {
  testWidgets('App renders blank MaterialApp with title', (WidgetTester tester) async {
    await tester.pumpWidget(const MockInterviewApp());

    expect(find.text('MockInterview AI'), findsOneWidget);
    expect(find.byType(MaterialApp), findsOneWidget);
    expect(find.byType(Scaffold), findsOneWidget);
  });
}
