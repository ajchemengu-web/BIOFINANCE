import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/transaction.dart';
import 'transaction_providers.dart';

class TransactionsScreen extends ConsumerWidget {
  const TransactionsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final transactionsAsync = ref.watch(transactionProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Transactions')),
      body: transactionsAsync.when(
        data: (transactions) => transactions.isEmpty
            ? const Center(child: Text('No transactions yet'))
            : RefreshIndicator(
                onRefresh: () async {
                  ref.invalidate(transactionProvider);
                  await ref.read(transactionProvider.future).catchError((_) => <AppTransaction>[]);
                },
                child: ListView.builder(
                  itemCount: transactions.length,
                  itemBuilder: (context, index) {
                    final transaction = transactions[index];
                    final completed = transaction.status == 'COMPLETED';
                    return ListTile(
                      leading: Icon(
                        completed ? Icons.check_circle_outline : Icons.error_outline,
                        color: completed ? Colors.green : Colors.red,
                      ),
                      title: Text(transaction.selectedProvider ?? transaction.status),
                      subtitle: Text('${transaction.status} · ${transaction.id}'),
                      trailing: Text('KSh ${transaction.amount.toStringAsFixed(2)}'),
                    );
                  },
                ),
              ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text('$error')),
      ),
    );
  }
}
