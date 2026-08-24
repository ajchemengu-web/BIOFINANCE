import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:biopos/main.dart';

void main() {
  testWidgets('sign in, request payment, simulate customer, see receipt', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: BioPosApp()));

    await tester.tap(find.text('Sign in'));
    await tester.pumpAndSettle();

    expect(find.text('Java House'), findsOneWidget);

    await tester.enterText(find.byType(TextFormField), '2000');
    await tester.tap(find.text('Request Payment'));
    // Not pumpAndSettle — WaitingScreen shows a permanent indeterminate
    // CircularProgressIndicator (the "waiting" visual) that never settles
    // on its own. Step past the page-route transition explicitly instead.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.text('KSh 2000.00'), findsOneWidget);
    expect(find.text('WAITING FOR CUSTOMER'), findsOneWidget);

    await tester.tap(find.text('Simulate Customer Authentication'));
    await tester.pump();
    await tester.pump(const Duration(seconds: 1)); // mock authentication delay
    await tester.pump(const Duration(milliseconds: 300)); // pushReplacement transition
    await tester.pumpAndSettle();

    expect(find.text('PAYMENT SUCCESSFUL'), findsOneWidget);
    expect(find.text('KSh 2000.00'), findsOneWidget);

    await tester.tap(find.text('New Transaction'));
    await tester.pumpAndSettle();

    expect(find.text('Java House'), findsOneWidget);
  });
}
