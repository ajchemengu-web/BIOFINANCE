import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/transaction.dart';
import 'transaction_providers.dart';

class TransactionsScreen extends ConsumerWidget {
  const TransactionsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final transactions = ref.watch(transactionProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Transactions')),
      body: transactions.isEmpty
          ? const Center(child: Text('No transactions yet'))
          : ListView.builder(
              itemCount: transactions.length,
              itemBuilder: (context, index) {
                final transaction = transactions[index];
                return ListTile(
                  leading: Icon(
                    transaction.status == TransactionStatus.completed
                        ? Icons.check_circle_outline
                        : Icons.error_outline,
                    color: transaction.status == TransactionStatus.completed ? Colors.green : Colors.red,
                  ),
                  title: Text(transaction.merchantName),
                  subtitle: Text('${transaction.provider} · ${transaction.id}'),
                  trailing: Text('KSh ${transaction.amount.toStringAsFixed(2)}'),
                );
              },
            ),
    );
  }
}
