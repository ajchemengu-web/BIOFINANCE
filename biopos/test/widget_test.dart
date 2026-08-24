import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:biopos/main.dart';

void main() {
  testWidgets('Signed-out merchant sees the login screen', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: BioPosApp()));

    expect(find.text('BioPOS'), findsOneWidget);
    expect(find.text('Sign in'), findsOneWidget);
  });
}
