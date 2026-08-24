import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:biopos/main.dart';

const _apiBase = 'http://localhost:8000/api/v1';

/// Stands in for "the customer, on their own device, running mobile/" —
/// raw HTTP against the same backend, deliberately not going through
/// BioPOS's UI, because claiming a request is mobile/'s job, not BioPOS's
/// (see backend/app/api/payments.py POST /payments/{id}/claim).
Future<String> _registerCustomerAndGetToken() async {
  final email = 'biopos-customer-${DateTime.now().millisecondsSinceEpoch}@biofinance.dev';
  final response = await http.post(
    Uri.parse('$_apiBase/auth/register'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'email': email, 'password': 'password123', 'full_name': 'Customer'}),
  );
  return (jsonDecode(response.body) as Map<String, dynamic>)['access_token'] as String;
}

Future<String> _connectMpesa(String token) async {
  final response = await http.post(
    Uri.parse('$_apiBase/providers/connect'),
    headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'},
    body: jsonEncode({
      'provider_code': 'MPESA',
      'external_account_ref': 'biopos-test-${DateTime.now().microsecondsSinceEpoch}',
    }),
  );
  return (jsonDecode(response.body) as Map<String, dynamic>)['id'] as String;
}

Future<void> _setPrimaryProvider(String token, String connectionId) async {
  await http.put(
    Uri.parse('$_apiBase/routing-policy'),
    headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'},
    body: jsonEncode({'mode': 'PRIMARY', 'primary_provider_id': connectionId}),
  );
}

Future<void> _claim(String token, String paymentId) async {
  await http.post(
    Uri.parse('$_apiBase/payments/$paymentId/claim'),
    headers: {'Authorization': 'Bearer $token'},
  );
}

void main() {
  setUpAll(() => HttpOverrides.global = null);

  testWidgets(
    'merchant opens a request, a customer claims it from their own session, '
    'BioPOS polls to a receipt',
    (tester) async {
      // Whole flow in one runAsync — real network calls (from BioPOS's own
      // taps, and WaitingScreen's Timer.periodic polling) only actually
      // progress inside a real event-loop turn; splitting this across
      // multiple runAsync calls, or letting any of it fire outside one,
      // leaves those calls/timers orphaned and nothing ever resolves.
      await tester.runAsync(() async {
        await tester.pumpWidget(const ProviderScope(child: BioPosApp()));
        await tester.pump();

        await tester.enterText(find.byType(TextFormField), 'Test Shop');
        await tester.tap(find.text('Sign in'));
        await tester.pump();
        await Future.delayed(const Duration(seconds: 2));
        await tester.pump();

        expect(find.text('Test Shop'), findsOneWidget);

        await tester.enterText(find.byType(TextFormField), '2000');
        await tester.tap(find.text('Request Payment'));
        await tester.pump();
        await Future.delayed(const Duration(seconds: 2));
        await tester.pump();
        // A plain pump() rebuilds the tree but doesn't advance the fake
        // animation clock — Navigator.push's page-route transition is
        // AnimationController-driven, so without this the new screen's
        // State is constructed (initState fires) but nothing later in the
        // test can find its widgets yet. Same requirement on the
        // WaitingScreen -> ReceiptScreen swap further down.
        await tester.pump(const Duration(milliseconds: 300));

        expect(find.text('WAITING FOR CUSTOMER'), findsOneWidget);

        final refFinder = find.textContaining('Ref: ');
        final refText = (tester.widget(refFinder) as Text).data!;
        final paymentId = refText.replaceFirst('Ref: ', '');

        // A customer, on their own device, sets up a provider and claims it.
        final customerToken = await _registerCustomerAndGetToken();
        final mpesaConnectionId = await _connectMpesa(customerToken);
        await _setPrimaryProvider(customerToken, mpesaConnectionId);
        await _claim(customerToken, paymentId);

        // BioPOS's own polling (every 2s) should pick up the change.
        await Future.delayed(const Duration(seconds: 3));
        await tester.pump();
        // Safe here (unlike WaitingScreen) — ReceiptScreen has no permanent
        // indeterminate spinner, so pumpAndSettle can actually finish once
        // the page-route transition animation completes.
        await tester.pumpAndSettle();

        expect(find.text('PAYMENT SUCCESSFUL'), findsOneWidget);
        expect(find.text('KSh 2000.00'), findsOneWidget);
        expect(find.text('via MPESA'), findsOneWidget);
      });
    },
  );
}
