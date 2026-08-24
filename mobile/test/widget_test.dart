import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:biofinance/core/storage/secure_storage.dart';
import 'package:biofinance/main.dart';

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
  testWidgets('Unauthenticated users see the login screen', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [secureStorageProvider.overrideWithValue(_InMemoryTokenStorage())],
        child: const BioFinanceApp(),
      ),
    );

    expect(find.text('BioFinance'), findsOneWidget);
    expect(find.text('Log in'), findsOneWidget);
  });
}
