import 'package:flutter_test/flutter_test.dart';

import 'package:biofinance/main.dart';

void main() {
  testWidgets('BioFinance app shell renders', (WidgetTester tester) async {
    await tester.pumpWidget(const BioFinanceApp());

    expect(find.text('BioFinance'), findsOneWidget);
  });
}
