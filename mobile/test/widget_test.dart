import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:biofinance/main.dart';

void main() {
  testWidgets('Unauthenticated users see the login screen', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: BioFinanceApp()));

    expect(find.text('BioFinance'), findsOneWidget);
    expect(find.text('Log in'), findsOneWidget);
  });
}
