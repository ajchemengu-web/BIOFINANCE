import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'features/amount_entry/amount_entry_screen.dart';
import 'features/merchant_auth/merchant_auth_providers.dart';
import 'features/merchant_auth/merchant_login_screen.dart';

void main() {
  runApp(const ProviderScope(child: BioPosApp()));
}

class BioPosApp extends StatelessWidget {
  const BioPosApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BioPOS',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepOrange)),
      home: const MerchantAuthGate(),
    );
  }
}

/// Switches between merchant sign-in and the terminal based on the mock
/// session state in features/merchant_auth/merchant_auth_providers.dart.
class MerchantAuthGate extends ConsumerWidget {
  const MerchantAuthGate({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isSignedIn = ref.watch(merchantAuthProvider.select((s) => s.isSignedIn));
    return isSignedIn ? const AmountEntryScreen() : const MerchantLoginScreen();
  }
}
