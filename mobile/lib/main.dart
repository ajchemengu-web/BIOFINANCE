import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'features/authentication/auth_providers.dart';
import 'features/authentication/login_screen.dart';
import 'features/dashboard/home_shell.dart';

void main() {
  runApp(const ProviderScope(child: BioFinanceApp()));
}

class BioFinanceApp extends StatelessWidget {
  const BioFinanceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BioFinance',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal)),
      home: const AuthGate(),
    );
  }
}

/// Switches between the login screen and the authenticated app shell based
/// on the mock session state in features/authentication/auth_providers.dart.
class AuthGate extends ConsumerWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isAuthenticated = ref.watch(authProvider.select((state) => state.isAuthenticated));
    return isAuthenticated ? const HomeShell() : const LoginScreen();
  }
}
