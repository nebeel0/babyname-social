import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// Test helper utilities for Flutter widget and provider testing

/// Wraps a widget in a MaterialApp for testing
Widget wrapWithMaterialApp(Widget child) {
  return MaterialApp(
    home: Scaffold(body: child),
  );
}

/// Wraps a widget in a ProviderScope with optional overrides
Widget wrapWithProviderScope(
  Widget child, {
  List<Override> overrides = const [],
}) {
  return ProviderScope(
    overrides: overrides,
    child: child,
  );
}

/// Wraps a widget in both ProviderScope and MaterialApp
Widget wrapWithApp(
  Widget child, {
  List<Override> overrides = const [],
}) {
  return ProviderScope(
    overrides: overrides,
    child: MaterialApp(
      home: Scaffold(body: child),
    ),
  );
}

/// Creates a ProviderContainer with optional overrides for testing
ProviderContainer createContainer({
  List<Override> overrides = const [],
}) {
  return ProviderContainer(
    overrides: overrides,
  );
}

/// Pumps a widget and waits for all animations to complete
Future<void> pumpWidgetAndSettle(
  WidgetTester tester,
  Widget widget, {
  Duration duration = const Duration(seconds: 5),
}) async {
  await tester.pumpWidget(widget);
  await tester.pumpAndSettle(duration);
}

/// Verifies that a widget of type T exists in the widget tree
void expectWidgetToExist<T>() {
  expect(find.byType(T), findsOneWidget);
}

/// Verifies that text exists in the widget tree
void expectTextToExist(String text) {
  expect(find.text(text), findsOneWidget);
}

/// Verifies that text does not exist in the widget tree
void expectTextNotToExist(String text) {
  expect(find.text(text), findsNothing);
}

/// Taps on a widget with the given text
Future<void> tapOnText(WidgetTester tester, String text) async {
  await tester.tap(find.text(text));
  await tester.pumpAndSettle();
}

/// Taps on a widget of the given type
Future<void> tapOnWidget<T>(WidgetTester tester) async {
  await tester.tap(find.byType(T));
  await tester.pumpAndSettle();
}

/// Enters text into a TextField
Future<void> enterText(
  WidgetTester tester,
  String text, {
  Type? widgetType,
  String? labelText,
}) async {
  if (widgetType != null) {
    await tester.enterText(find.byType(widgetType), text);
  } else if (labelText != null) {
    await tester.enterText(
      find.widgetWithText(TextField, labelText),
      text,
    );
  } else {
    await tester.enterText(find.byType(TextField), text);
  }
  await tester.pumpAndSettle();
}

/// Scrolls to find a widget
Future<void> scrollUntilVisible(
  WidgetTester tester,
  Finder finder, {
  double scrollDelta = 100.0,
  int maxScrolls = 50,
}) async {
  final scrollable = find.byType(Scrollable).first;
  int scrollCount = 0;

  while (scrollCount < maxScrolls) {
    if (tester.any(finder)) {
      break;
    }

    await tester.drag(scrollable, Offset(0, -scrollDelta));
    await tester.pumpAndSettle();
    scrollCount++;
  }

  expect(tester.any(finder), isTrue,
      reason: 'Could not find widget after $maxScrolls scrolls');
}

/// Waits for a condition to be true
Future<void> waitFor(
  WidgetTester tester,
  bool Function() condition, {
  Duration timeout = const Duration(seconds: 5),
  Duration checkInterval = const Duration(milliseconds: 100),
}) async {
  final endTime = DateTime.now().add(timeout);

  while (DateTime.now().isBefore(endTime)) {
    if (condition()) {
      return;
    }

    await tester.pump(checkInterval);
  }

  throw TimeoutException(
    'Condition was not met within $timeout',
    timeout,
  );
}

/// Exception thrown when waiting for a condition times out
class TimeoutException implements Exception {
  final String message;
  final Duration timeout;

  TimeoutException(this.message, this.timeout);

  @override
  String toString() => 'TimeoutException: $message';
}

/// Mock data builders for tests

/// Creates a mock error for testing
Exception createMockError([String message = 'Mock error']) {
  return Exception(message);
}

/// Delays execution for testing async operations
Future<void> delay([Duration duration = const Duration(milliseconds: 100)]) {
  return Future.delayed(duration);
}

/// Test data factory for creating consistent test data
class TestData {
  /// Creates a unique test ID
  static int uniqueId() {
    return DateTime.now().millisecondsSinceEpoch;
  }

  /// Creates a unique test string
  static String uniqueString([String prefix = 'test']) {
    return '${prefix}_${DateTime.now().millisecondsSinceEpoch}';
  }
}
