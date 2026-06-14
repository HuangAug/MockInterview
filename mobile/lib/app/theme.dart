// App-wide theme constants and [ThemeData] factory.
//
// Colors follow CODING_STANDARD §3.8:
//   Primary  #2563EB | Background #F8FAFC | Error #EF4444 | Success #22C55E.
library;
import 'package:flutter/material.dart';

class AppTheme {
  AppTheme._();

  // ---------------------------------------------------------------------------
  // Brand colors
  // ---------------------------------------------------------------------------
  static const Color primary = Color(0xFF2563EB);
  static const Color background = Color(0xFFF8FAFC);
  static const Color error = Color(0xFFEF4444);
  static const Color success = Color(0xFF22C55E);
  static const Color warning = Color(0xFFF59E0B);
  static const Color info = Color(0xFF3B82F6);

  // ---------------------------------------------------------------------------
  // Spacing (multiples of 8)
  // ---------------------------------------------------------------------------
  static const double spacingXs = 4;
  static const double spacingSm = 8;
  static const double spacingMd = 16;
  static const double spacingLg = 24;
  static const double spacingXl = 32;

  // ---------------------------------------------------------------------------
  // Border radius
  // ---------------------------------------------------------------------------
  static const double cardRadius = 12;
  static const double buttonRadius = 8;

  // ---------------------------------------------------------------------------
  // ThemeData
  // ---------------------------------------------------------------------------
  static ThemeData get light => ThemeData(
    colorSchemeSeed: primary,
    useMaterial3: true,
    scaffoldBackgroundColor: background,
    cardTheme: CardThemeData(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(cardRadius),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(buttonRadius),
        ),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(buttonRadius),
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(buttonRadius),
      ),
    ),
  );
}
