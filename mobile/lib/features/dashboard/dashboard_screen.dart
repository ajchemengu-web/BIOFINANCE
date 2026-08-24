import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/provider_balance.dart';
import '../../models/provider_connection.dart';
import '../bioid/bioid_providers.dart';
import '../payments/pay_screen.dart';
import 'balance_providers.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final balancesAsync = ref.watch(balanceProvider);
    final bioIdAsync = ref.watch(bioIdProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('BioWallet')),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(balanceProvider);
          ref.invalidate(bioIdProvider);
          try {
            await ref.read(balanceProvider.future);
          } catch (_) {
            // Surfaced by balancesAsync.when's error branch below.
          }
        },
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            bioIdAsync.when(
              data: (bioId) => Text('Your BioID: ${bioId.code}', style: Theme.of(context).textTheme.bodySmall),
              loading: () => const SizedBox.shrink(),
              error: (_, _) => const SizedBox.shrink(),
            ),
            const SizedBox(height: 12),
            balancesAsync.when(
              data: (balances) => _BalancesSection(balances: balances),
              loading: () => const Padding(
                padding: EdgeInsets.symmetric(vertical: 32),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (error, _) => _ErrorCard(message: '$error'),
            ),
          ],
        ),
      ),
    );
  }
}

class _BalancesSection extends StatelessWidget {
  const _BalancesSection({required this.balances});

  final BalancesResult balances;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Card(
          color: Theme.of(context).colorScheme.primaryContainer,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('TOTAL AVAILABLE'),
                const SizedBox(height: 4),
                Text(
                  'KSh ${balances.total.toStringAsFixed(2)}',
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 4),
                const Text('Total across connected accounts', style: TextStyle(fontSize: 12)),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),
        Text('By provider', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        if (balances.byProvider.isEmpty)
          const Text('No providers connected yet. Connect one from the Providers tab.'),
        for (final balance in balances.byProvider) _BalanceTile(balance: balance),
        const SizedBox(height: 24),
        FilledButton.icon(
          onPressed: balances.byProvider.isEmpty
              ? null
              : () => Navigator.of(context)
                  .push(MaterialPageRoute<void>(builder: (_) => const PayScreen())),
          icon: const Icon(Icons.fingerprint),
          label: const Text('Pay with BioFinance'),
        ),
      ],
    );
  }
}

class _BalanceTile extends StatelessWidget {
  const _BalanceTile({required this.balance});

  final ProviderBalance balance;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: const Icon(Icons.account_balance_wallet_outlined),
        title: Text(providerDisplayName(balance.providerCode)),
        trailing: Text('KSh ${balance.amount.toStringAsFixed(2)}'),
      ),
    );
  }
}

class _ErrorCard extends StatelessWidget {
  const _ErrorCard({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Theme.of(context).colorScheme.errorContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Text(message, style: TextStyle(color: Theme.of(context).colorScheme.onErrorContainer)),
      ),
    );
  }
}
