import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:biofinance/core/security/biometric_auth.dart';
import 'package:biofinance/main.dart';

/// No platform channel in the widget-test harness would ever answer
/// local_auth's real plugin — this stands in as "no biometric hardware",
/// which is a real code path the app already handles.
class _FakeBiometricAuth implements BiometricAuthenticator {
  @override
  Future<bool> isAvailable() async => false;

  @override
  Future<bool> authenticate({String reason = ''}) async => true;
}

void main() {
  testWidgets('login, pay, and see the transaction in history', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [biometricAuthProvider.overrideWithValue(_FakeBiometricAuth())],
        child: const BioFinanceApp(),
      ),
    );

    // Login (mock — see auth_providers.dart) with the pre-filled demo credentials.
    await tester.tap(find.text('Log in'));
    await tester.pumpAndSettle();

    expect(find.text('BioWallet'), findsOneWidget);
    expect(find.text('Pay with BioFinance'), findsOneWidget);

    // Open the pay flow and submit with the pre-filled merchant/amount.
    await tester.tap(find.text('Pay with BioFinance'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Authenticate & Pay'));
    // Don't pumpAndSettle here — the button shows an indeterminate
    // CircularProgressIndicator while "processing", which never settles.
    // Step past the simulated 500ms authorization latency instead.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 600));
    await tester.pumpAndSettle();

    expect(find.text('PAYMENT SUCCESSFUL'), findsOneWidget);
    await tester.tap(find.text('OK'));
    await tester.pumpAndSettle();

    // Switch to the History tab and confirm the new transaction is there.
    await tester.tap(find.byIcon(Icons.receipt_long));
    await tester.pumpAndSettle();

    expect(find.text('Java House'), findsWidgets);
  });
}
