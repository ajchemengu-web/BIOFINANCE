import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

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
      home: const DashboardPlaceholder(),
    );
  }
}

/// Placeholder home screen. Real BioWallet dashboard (balances by provider,
/// total across connected accounts) is built out in Phase 1 — see
/// docs/roadmap.md and PRD §20.
class DashboardPlaceholder extends StatelessWidget {
  const DashboardPlaceholder({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('BioFinance')),
      body: const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'Phase 0 scaffold.\nDashboard, BioID, and payment flows land in Phase 1.',
            textAlign: TextAlign.center,
          ),
        ),
      ),
    );
  }
}
