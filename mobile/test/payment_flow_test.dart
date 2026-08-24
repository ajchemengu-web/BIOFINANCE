import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:biofinance/core/security/biometric_auth.dart';
import 'package:biofinance/core/storage/secure_storage.dart';
import 'package:biofinance/main.dart';

/// No platform channel in the widget-test harness would ever answer
/// local_auth's or flutter_secure_storage's real plugins — these stand in
/// for "no biometric hardware" / "empty local storage", real code paths the
/// app already handles. Everything else in this test hits the REAL backend
/// over real HTTP — run `uvicorn app.main:app` on localhost:8000 first
/// (see README).
class _FakeBiometricAuth implements BiometricAuthenticator {
  @override
  Future<bool> isAvailable() async => false;

  @override
  Future<bool> authenticate({String reason = ''}) async => true;
}

class _InMemoryTokenStorage implements TokenStorage {
  final _store = <String, String>{};

  @override
  Future<void> write(String key, String value) async => _store[key] = value;

  @override
  Future<String?> read(String key) async => _store[key];

  @override
  Future<void> delete(String key) async => _store.remove(key);
}

/// A screen can watch several FutureProviders at once (HomeShell's
/// IndexedStack keeps every tab's screen alive, so they all fire together),
/// each a real HTTP call. A single fixed real-time delay isn't reliably
/// enough turns of the real event loop for all of them to land — poll in
/// small real-time increments for the widget that proves the target state
/// was reached instead. Must run inside `tester.runAsync`.
Future<void> _pumpUntilFound(
  WidgetTester tester,
  Finder finder, {
  Duration timeout = const Duration(seconds: 15),
}) async {
  final deadline = DateTime.now().add(timeout);
  while (DateTime.now().isBefore(deadline)) {
    await tester.pump(const Duration(milliseconds: 100));
    if (finder.evaluate().isNotEmpty) return;
    await Future.delayed(const Duration(milliseconds: 200));
  }
  await tester.pump();
  if (finder.evaluate().isEmpty) {
    final allText = find.byType(Text).evaluate().map((e) => (e.widget as Text).data).toList();
    // ignore: avoid_print
    print('TIMED OUT waiting for finder. Visible Text widgets: $allText');
  }
}

void main() {
  // TestWidgetsFlutterBinding installs an HttpOverrides that makes every
  // dart:io HttpClient request return 400 without touching the network —
  // a safety net against tests accidentally hitting the real internet.
  // This test's whole point is to hit the real local backend, so opt out.
  setUpAll(() => HttpOverrides.global = null);

  testWidgets('login, connect a provider, pay, and see it in history — against the live backend',
      (tester) async {
    // The whole flow runs inside one runAsync: real network calls fire not
    // just from explicit taps (login, connect, pay) but also implicitly
    // whenever a screen rebuild causes a FutureProvider to re-fetch
    // (balances, BioID, transactions). Splitting the interaction across
    // multiple runAsync calls leaves those implicit fetches orphaned in the
    // fake-clock test zone, where they never resolve — pumpAndSettle then
    // hangs forever waiting on a Future nothing will ever complete.
    await tester.runAsync(() async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            biometricAuthProvider.overrideWithValue(_FakeBiometricAuth()),
            secureStorageProvider.overrideWithValue(_InMemoryTokenStorage()),
          ],
          child: const BioFinanceApp(),
        ),
      );
      await tester.pumpAndSettle();

      // Unique email so re-runs against the same backend don't collide.
      final email = 'flutter-test-${DateTime.now().millisecondsSinceEpoch}@biofinance.dev';
      final fields = find.byType(TextFormField);
      await tester.enterText(fields.first, email);
      await tester.enterText(fields.last, 'password123');
      await tester.tap(find.text('Log in'));
      await _pumpUntilFound(tester, find.text('BioWallet')); // login (401) -> register round trip

      expect(find.text('BioWallet'), findsOneWidget);
      await _pumpUntilFound(
        tester,
        find.text('No providers connected yet. Connect one from the Providers tab.'),
      );

      // Connect M-PESA.
      await tester.tap(find.byIcon(Icons.link));
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(OutlinedButton, 'Connect').first);
      await _pumpUntilFound(tester, find.text('Disconnect'));
      expect(find.text('Disconnect'), findsOneWidget);

      // Dashboard should now show the mock M-PESA balance.
      await tester.tap(find.byIcon(Icons.account_balance_wallet));
      await _pumpUntilFound(tester, find.textContaining('KSh 8500.00'));
      expect(find.textContaining('KSh 8500.00'), findsWidgets);

      // Set M-PESA as the preferred (primary) routing provider — BioRouter
      // has nothing to route to without this, matching PRD §22.
      await tester.tap(find.byIcon(Icons.alt_route));
      await _pumpUntilFound(tester, find.text('Preferred provider'));
      await tester.tap(find.byType(DropdownButtonFormField<String?>).first);
      await tester.pumpAndSettle();
      await tester.tap(find.text('M-PESA').last);
      await _pumpUntilFound(tester, find.text('M-PESA'));

      // Back to the dashboard to pay — biometric is faked "unavailable" so
      // it proceeds straight through.
      await tester.tap(find.byIcon(Icons.account_balance_wallet));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Pay with BioFinance'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Authenticate & Pay'));
      await _pumpUntilFound(tester, find.text('PAYMENT SUCCESSFUL'));

      expect(find.text('PAYMENT SUCCESSFUL'), findsOneWidget);
      await tester.tap(find.text('OK'));
      await tester.pumpAndSettle();

      // Transaction shows up in history, routed via MPESA.
      await tester.tap(find.byIcon(Icons.receipt_long));
      await _pumpUntilFound(tester, find.text('MPESA'));
      expect(find.text('MPESA'), findsWidgets);
      expect(find.textContaining('COMPLETED'), findsOneWidget);
    });
  });
}
