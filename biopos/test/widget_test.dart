import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:biopos/core/storage/secure_storage.dart';
import 'package:biopos/main.dart';

/// No platform channel in the widget-test harness would ever answer
/// flutter_secure_storage's real plugin — stands in for "empty local
/// storage", a real code path the app already handles (no session yet).
/// Mirrors mobile/test/widget_test.dart's override exactly.
class _InMemoryTokenStorage implements TokenStorage {
  final _store = <String, String>{};

  @override
  Future<void> write(String key, String value) async => _store[key] = value;

  @override
  Future<String?> read(String key) async => _store[key];

  @override
  Future<void> delete(String key) async => _store.remove(key);
}

void main() {
  testWidgets('Signed-out merchant sees the login screen', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [secureStorageProvider.overrideWithValue(_InMemoryTokenStorage())],
        child: const BioPosApp(),
      ),
    );

    expect(find.text('BioPOS'), findsOneWidget);
    expect(find.text('Sign in'), findsOneWidget);
  });
}
