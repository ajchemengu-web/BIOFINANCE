import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/provider_balance.dart';
import '../bioid/bioid_providers.dart';
import '../payments/pay_screen.dart';
import 'balance_providers.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final balances = ref.watch(balanceProvider);
    final total = ref.watch(totalBalanceProvider);
    final bioId = ref.watch(bioIdProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('BioWallet')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (bioId != null)
            Text('Your BioID: $bioId', style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 12),
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
                    'KSh ${total.toStringAsFixed(2)}',
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
          if (balances.isEmpty)
            const Text('No providers connected yet. Connect one from the Providers tab.'),
          for (final balance in balances) _BalanceTile(balance: balance),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: balances.isEmpty
                ? null
                : () => Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => const PayScreen())),
            icon: const Icon(Icons.fingerprint),
            label: const Text('Pay with BioFinance'),
          ),
        ],
      ),
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
        title: Text(balance.displayName),
        trailing: Text('KSh ${balance.amount.toStringAsFixed(2)}'),
      ),
    );
  }
}
